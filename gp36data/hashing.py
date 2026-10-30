"""Exact and perceptual image hashes (64-bit dHash and pHash) and Hamming distances."""
import numpy as np
from PIL import Image

from .manifest import sha256_file  # noqa: F401  (re-exported for callers)


def _bits_to_int(bits):
    return int.from_bytes(np.packbits(np.asarray(bits, dtype=bool)).tobytes(), "big")


def dhash(im):
    """Difference hash: 9x8 grayscale, compare horizontal neighbours."""
    g = np.asarray(im.convert("L").resize((9, 8), Image.BILINEAR), dtype=np.int16)
    return _bits_to_int((g[:, 1:] > g[:, :-1]).flatten())


def _dct_matrix(n):
    k = np.arange(n)[:, None]
    x = np.arange(n)[None, :]
    m = np.sqrt(2 / n) * np.cos(np.pi * (2 * x + 1) * k / (2 * n))
    m[0] /= np.sqrt(2)
    return m


_DCT32 = _dct_matrix(32)


def phash(im):
    """DCT hash: 32x32 grayscale, 8x8 lowest frequencies compared with their median (DC excluded)."""
    g = np.asarray(im.convert("L").resize((32, 32), Image.LANCZOS), dtype=np.float64)
    low = (_DCT32 @ g @ _DCT32.T)[:8, :8].flatten()
    return _bits_to_int(low > np.median(low[1:]))


def hamming(a, b):
    return (a ^ b).bit_count()


def hamming_to_all(h, arr):
    """Hamming distance from one 64-bit hash to every hash in a uint64 array."""
    return np.bitwise_count(np.bitwise_xor(arr, np.uint64(h))).astype(np.int64)
