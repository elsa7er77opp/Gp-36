import io
import unittest
from collections import Counter

from helpers import smooth_image
from PIL import Image

from gp36data.dedup import find_links, group_samples
from gp36data.hashing import dhash, hamming, phash
from gp36data.split import group_split


def sample(im, sha, key=""):
    return {"sha256": sha, "dhash": dhash(im), "phash": phash(im), "group_key": key}


def recompress(im, q=30, scale=0.5):
    buf = io.BytesIO()
    im.resize((int(im.width * scale), int(im.height * scale))).save(buf, "JPEG", quality=q)
    return Image.open(io.BytesIO(buf.getvalue()))


class TestHashes(unittest.TestCase):
    def test_recompressed_resized_copy_is_near(self):
        im = smooth_image(7)
        r = recompress(im)
        self.assertLessEqual(hamming(dhash(im), dhash(r)), 4)
        self.assertLessEqual(hamming(phash(im), phash(r)), 10)

    def test_distinct_images_are_far(self):
        far = [hamming(phash(smooth_image(a)), phash(smooth_image(b))) for a, b in [(1, 2), (3, 4), (5, 6)]]
        self.assertTrue(all(d > 10 for d in far), far)


class TestGrouping(unittest.TestCase):
    def test_exact_near_metadata_and_transitive(self):
        a = smooth_image(1)
        s = [sample(a, "A"), sample(a, "A"),                    # 0-1 exact
             sample(recompress(a), "B"),                         # 2 near to 0
             sample(smooth_image(2), "C", "video1"),             # 3 metadata with 4
             sample(smooth_image(3), "D", "video1"),
             sample(smooth_image(4), "E")]                       # 5 alone
        links = find_links(s)
        reasons = Counter(l[2] for l in links)
        self.assertEqual(reasons["exact"], 1)
        self.assertEqual(reasons["metadata"], 1)
        self.assertGreaterEqual(reasons["near"], 1)
        g = group_samples(s, links)
        self.assertEqual(len({g[0], g[1], g[2]}), 1)
        self.assertEqual(g[3], g[4])
        self.assertEqual(len(set(g)), 3)


class TestSplit(unittest.TestCase):
    def setUp(self):
        self.groups = {f"g{i}": {"n": 1 + i % 5, "classes": {0: 1 + i % 3, 1: (i % 4 == 0) * 2}} for i in range(200)}

    def test_deterministic(self):
        self.assertEqual(group_split(self.groups, seed=3), group_split(self.groups, seed=3))

    def test_every_group_assigned_once_and_ratios_close(self):
        out = group_split(self.groups, seed=0)
        self.assertEqual(set(out), set(self.groups))
        tot = sum(g["n"] for g in self.groups.values())
        for s, r in {"train": .7, "val": .2, "test": .1}.items():
            n = sum(self.groups[g]["n"] for g, sp in out.items() if sp == s)
            self.assertAlmostEqual(n / tot, r, delta=0.03)
            for c in (0, 1):
                cs = sum(self.groups[g]["classes"][c] for g, sp in out.items() if sp == s)
                ct = sum(v["classes"][c] for v in self.groups.values())
                self.assertAlmostEqual(cs / ct, r, delta=0.05)

    def test_forced_groups_respected(self):
        out = group_split(self.groups, forced={"g0": "holdout", "g1": "test"})
        self.assertEqual((out["g0"], out["g1"]), ("holdout", "test"))

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            group_split(self.groups, ratios={"train": .5, "val": .2})
        with self.assertRaises(KeyError):
            group_split(self.groups, forced={"nope": "test"})


if __name__ == "__main__":
    unittest.main()


class TestVideoTimeblock(unittest.TestCase):
    def test_v15_frame_names_group_by_video_and_block(self):
        from gp36data.sources import group_key
        r = "video_timeblock:20"
        a = group_key("sb15", r, "frame0-00-13-83_jpg.rf.a68adef0d1e1d6ab5bdb5a38ec0b5b1f.jpg")
        b = group_key("sb15", r, "frame0-00-19-90_jpg.rf.0000000000000000000000000000000a.jpg")
        c = group_key("sb15", r, "frame0-00-20-10_jpg.rf.0000000000000000000000000000000b.jpg")
        d = group_key("sb15", r, "frame0-00-13-83-2-_jpg.rf.0000000000000000000000000000000c.jpg")
        e = group_key("sb15", r, "frame0-01-57-63-4-_jpg.rf.0000000000000000000000000000000d.jpg")
        self.assertEqual(a, b)                      # same video, same 20 s block
        self.assertNotEqual(a, c)                   # next block
        self.assertNotEqual(a, d)                   # same timestamp, different video
        self.assertEqual(e, "sb15:video4:block5")   # 117.63 s // 20
        with self.assertRaises(ValueError):
            group_key("sb15", r, "random_name.jpg")
