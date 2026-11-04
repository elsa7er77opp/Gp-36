"""Read members of a large remote zip over HTTP range requests, without downloading the whole archive.

    python -I tools/remote_zip.py list  <url> <out.csv>
    python -I tools/remote_zip.py fetch <url> <names.txt> <new_dir> [--threads 16]

`list` reads the central directory (end of the file) and writes name, size, compressed size, method, CRC.
`fetch` downloads only the members named in names.txt (one per line), checks each CRC-32, and writes them
under <new_dir> (zip-slip safe; the directory must not exist yet, files are written to <new_dir>.partial and
the folder is renamed when every member passed). A per-file SHA-256 list goes to <new_dir>/_fetch.json.
Used because the Zenodo server gives ~10-40 KB/s per connection for the 13 GB RSID archive.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import struct
import sys
import time
import urllib.request
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath


def get_range(url, start, end, tries=6):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}", "User-Agent": "gp36-remote-zip"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if len(data) != end - start + 1:
                raise IOError(f"short read {len(data)} of {end - start + 1}")
            return data
        except Exception as e:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(2 * (k + 1))


def total_size(url):
    req = urllib.request.Request(url, headers={"Range": "bytes=0-0", "User-Agent": "gp36-remote-zip"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Range"].split("/")[1])


class RangeFile(io.RawIOBase):
    """Seekable read-only view of a remote file, enough for zipfile to parse the central directory."""

    def __init__(self, url, size, tail, threads=16, chunk=256 * 1024):
        self.url, self.size, self.pos = url, size, 0
        self.tail_start = max(0, size - tail)
        starts = range(self.tail_start, size, chunk)  # parallel chunks: the server is slow per connection
        with ThreadPoolExecutor(threads) as ex:
            parts = list(ex.map(lambda s: get_range(url, s, min(s + chunk, size) - 1), starts))
        self.tail = b"".join(parts)

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def read(self, n=-1):
        if n < 0:
            n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if n <= 0:
            return b""
        if self.pos >= self.tail_start:
            b = self.tail[self.pos - self.tail_start:self.pos - self.tail_start + n]
        else:
            b = get_range(self.url, self.pos, self.pos + n - 1)
        self.pos += len(b)
        return b

    def readinto(self, b):
        d = self.read(len(b))
        b[:len(d)] = d
        return len(d)


def infolist(url, tail=8 * 1024 * 1024):
    size = total_size(url)
    zf = zipfile.ZipFile(RangeFile(url, size, min(tail, size)))
    return zf.infolist(), size


def get_block(url, start, end, threads=16, chunk=1024 * 1024):
    """One byte range fetched as parallel chunks (the server is slow per connection and per request)."""
    starts = range(start, end + 1, chunk)
    with ThreadPoolExecutor(threads) as ex:
        return b"".join(ex.map(lambda s: get_range(url, s, min(s + chunk - 1, end)), starts))


def member_from(buf, buf_start, zi):
    o = zi.header_offset - buf_start
    sig, _, _, _, _, _, _, _, _, nlen, xlen = struct.unpack("<IHHHHHIIIHH", buf[o:o + 30])
    if sig != 0x04034B50:
        raise IOError(f"bad local header for {zi.filename}")
    s = o + 30 + nlen + xlen
    return decode(zi, buf[s:s + zi.compress_size])


def fetch_member(url, zi):
    head = get_range(url, zi.header_offset, zi.header_offset + 29)
    sig, _, _, _, _, _, _, _, _, nlen, xlen = struct.unpack("<IHHHHHIIIHH", head)
    if sig != 0x04034B50:
        raise IOError(f"bad local header for {zi.filename}")
    start = zi.header_offset + 30 + nlen + xlen
    raw = get_range(url, start, start + zi.compress_size - 1) if zi.compress_size else b""
    return decode(zi, raw)


def decode(zi, raw):
    if zi.compress_type == zipfile.ZIP_STORED:
        data = raw
    elif zi.compress_type == zipfile.ZIP_DEFLATED:
        data = zlib.decompress(raw, -15)
    else:
        raise IOError(f"unsupported compression {zi.compress_type} for {zi.filename}")
    if zlib.crc32(data) & 0xFFFFFFFF != zi.CRC:
        raise IOError(f"CRC mismatch for {zi.filename}")
    return data


def safe_target(root, name):
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or ":" in name:
        raise ValueError(f"unsafe member name {name!r}")
    return root.joinpath(*p.parts)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("list")
    a.add_argument("url")
    a.add_argument("out_csv")
    b = sub.add_parser("fetch")
    b.add_argument("url")
    b.add_argument("names")
    b.add_argument("out_dir")
    b.add_argument("--threads", type=int, default=16)
    b.add_argument("--max-gap", type=int, default=2 * 1024 * 1024)
    b.add_argument("--max-block", type=int, default=64 * 1024 * 1024)
    args = ap.parse_args()

    infos, size = infolist(args.url)
    if args.cmd == "list":
        if Path(args.out_csv).exists():
            sys.exit(f"{args.out_csv} exists")
        with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["name", "size", "compress_size", "method", "crc32", "header_offset"])
            for zi in infos:
                w.writerow([zi.filename, zi.file_size, zi.compress_size, zi.compress_type, f"{zi.CRC:08x}", zi.header_offset])
        print(f"{len(infos)} members, archive {size} bytes -> {args.out_csv}")
        return

    out = Path(args.out_dir)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    tmp = out.with_name(out.name + ".partial")
    tmp.mkdir(parents=True, exist_ok=True)  # a .partial folder is resumable: finished files are kept
    by_name = {zi.filename: zi for zi in infos}
    names = [n.strip() for n in open(args.names, encoding="utf-8") if n.strip()]
    missing = [n for n in names if n not in by_name]
    if missing:
        sys.exit(f"{len(missing)} names not in archive, e.g. {missing[:3]}")
    todo, done, log = [], 0, {}
    for n in names:
        t = safe_target(tmp, n)
        if t.exists() and t.stat().st_size == by_name[n].file_size:
            log[n] = hashlib.sha256(t.read_bytes()).hexdigest()
        else:
            todo.append(n)
    print(f"{len(names)} requested, {len(names) - len(todo)} already present, {len(todo)} to fetch", flush=True)
    t0, nbytes = time.time(), 0

    def write(n, data):
        t = safe_target(tmp, n)
        t.parent.mkdir(parents=True, exist_ok=True)
        part = t.with_name(t.name + ".tmp")
        part.write_bytes(data)
        os.replace(part, t)
        log[n] = hashlib.sha256(data).hexdigest()

    # Members close together in the archive are fetched as one block (few requests: the server limits
    # requests per minute). A gap of up to --max-gap bytes between wanted members is downloaded and discarded.
    offs = sorted(zi.header_offset for zi in infos)
    next_off = {o: offs[i + 1] if i + 1 < len(offs) else size for i, o in enumerate(offs)}
    todo.sort(key=lambda n: by_name[n].header_offset)
    blocks, cur = [], []
    for n in todo:
        s = by_name[n].header_offset
        if cur and (s - next_off[by_name[cur[-1]].header_offset] > args.max_gap
                    or next_off[s] - by_name[cur[0]].header_offset > args.max_block):
            blocks.append(cur)
            cur = []
        cur.append(n)
    if cur:
        blocks.append(cur)
    print(f"{len(blocks)} blocks", flush=True)

    def get_blk(blk):  # small blocks run side by side; a big block is itself split into parallel chunks
        s = by_name[blk[0]].header_offset
        e = next_off[by_name[blk[-1]].header_offset] - 1
        buf = get_block(args.url, s, e, threads=args.threads if len(blocks) == 1 else 1)
        return blk, s, buf

    with ThreadPoolExecutor(args.threads if len(blocks) > 1 else 1) as ex:
        for bi, fu in enumerate(as_completed([ex.submit(get_blk, b) for b in blocks])):
            blk, s, buf = fu.result()
            for n in blk:
                write(n, member_from(buf, s, by_name[n]))
            done += len(blk)
            nbytes += len(buf)
            if (bi + 1) % 50 == 0 or bi + 1 == len(blocks):
                el = time.time() - t0
                print(f"block {bi + 1}/{len(blocks)}  files {done}/{len(todo)}  {nbytes / 1e6:.0f} MB  "
                      f"{nbytes / max(el, 1e-9) / 1e3:.0f} KB/s", flush=True)
    (tmp / "_fetch.json").write_text(json.dumps({"url": args.url, "archive_size": size, "n": len(log),
                                                 "sha256": log}, indent=0), encoding="utf-8")
    os.rename(tmp, out)
    print(f"done -> {out}")


if __name__ == "__main__":
    main()
