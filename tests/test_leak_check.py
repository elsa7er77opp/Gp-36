"""tools/leak_check.py: exact, re-encoded, flipped and rotated copies of protected images are hits; unrelated
images are not; known re-upload file-name families are flagged; the real protected_hashes.npz is well formed."""
import hashlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from helpers import ROOT, save, smooth_image
from PIL import Image

sys.path.insert(0, str(ROOT / "tools"))
import leak_check as lc  # noqa: E402
from gp36data.hashing import dhash, phash  # noqa: E402

TOOL = ROOT / "tools" / "leak_check.py"
REAL = ROOT / "review" / "new_data_r3" / "protected_hashes.npz"


def reencode(im, q=35, scale=0.6):
    buf = io.BytesIO()
    im.resize((int(im.width * scale), int(im.height * scale))).save(buf, "JPEG", quality=q)
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


class TestLeakCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        prot = [smooth_image(500 + k) for k in range(3)]
        paths = [save(im, self.tmp / "prot" / f"p{k}.jpg") for k, im in enumerate(prot)]
        ims = [Image.open(p).convert("RGB") for p in paths]
        self.npz = self.tmp / "prot.npz"
        np.savez(self.npz, dhash=np.array([dhash(i) for i in ims], dtype=np.uint64),
                 phash=np.array([phash(i) for i in ims], dtype=np.uint64),
                 id=np.array(["val:rf8/p0", "test:rf8/p1", "train:rf8/p2"]),
                 sha256=np.array([hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]))
        self.prot_paths = paths
        self.Z = lc.load_protected(self.npz)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def check(self, im, name="c.jpg"):
        p = save(im, self.tmp / "cand" / name)
        return lc.check_image(p, *self.Z)

    def test_exact_copy(self):
        p = self.tmp / "cand" / "x.jpg"
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.prot_paths[0], p)
        r = lc.check_image(p, *self.Z)
        self.assertTrue(r["hit"] and r["exact"])

    def test_reencoded_and_dihedral_copies(self):
        base = Image.open(self.prot_paths[1]).convert("RGB")
        for t in (None, Image.FLIP_LEFT_RIGHT, Image.ROTATE_90, Image.ROTATE_180):
            im = reencode(base if t is None else base.transpose(t))
            r = self.check(im, f"t{t}.jpg")
            self.assertTrue(r["hit"], t)
            self.assertFalse(r["exact"])
            self.assertEqual(r["closest_id"], "test:rf8/p1")

    def test_unrelated_image_is_not_a_hit(self):
        for k in range(5):
            self.assertFalse(self.check(smooth_image(9000 + k), f"u{k}.jpg")["hit"])

    def test_cli_counts_eval_and_train_hits_separately(self):
        d = self.tmp / "cli"
        save(reencode(Image.open(self.prot_paths[0]).convert("RGB")), d / "a.jpg")   # val -> eval hit
        save(reencode(Image.open(self.prot_paths[2]).convert("RGB")), d / "b.jpg")   # train -> r2_train hit
        save(smooth_image(4242), d / "c.jpg")
        r = subprocess.run([sys.executable, "-I", str(TOOL), str(d), str(self.tmp / "o.csv"), "--hashes", str(self.npz)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("(val/test/external): 1;", r.stdout)
        self.assertIn("no value): 1", r.stdout)

    def test_known_families_by_name(self):
        cases = {"Image00045.jpg": "Image000xx", "MVI_1523_frame3.jpg": "MVI_15xx", "G0012345.jpg": "G00xxxxx",
                 "VID_20190924_101.jpg": "VID_20190924", "newonetrwww (12).jpg": "newonetrwww",
                 "kg_2025-01-02.jpg": "kg_/dz_", "rdd_Japan_001.jpg": "rdd_",
                 "Image-12-_jpg.rf.0123456789abcdef0123456789abcdef.jpg": "Image000xx",
                 "SpeedBreaker-7-_jpg.rf.0123456789abcdef0123456789abcdef.jpg": "SpeedBreaker-N-"}
        for name, fam in cases.items():
            self.assertIn(fam, lc.family(name) or "", name)
        for name in ("xqq062000001.jpg", "frame_0373.png", "IMG_1234.jpg", "speedbreaker_12.jpg"):
            self.assertIsNone(lc.family(name), name)


@unittest.skipUnless(REAL.exists(), "protected_hashes.npz not in this checkout")
class TestRealProtectedHashes(unittest.TestCase):
    def test_format(self):
        z = np.load(REAL, allow_pickle=False)
        n = len(z["id"])
        self.assertGreater(n, 1000)
        self.assertEqual(len(z["dhash"]), n)
        self.assertEqual(len(z["phash"]), n)
        self.assertEqual(z["dhash"].dtype, np.uint64)
        self.assertTrue(all(len(s) == 64 for s in z["sha256"][:50]))
        prefixes = {str(i).split(":")[0] for i in z["id"]}
        self.assertTrue({"val", "test"} <= prefixes, prefixes)


if __name__ == "__main__":
    unittest.main()
