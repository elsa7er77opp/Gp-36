import tempfile
import unittest
from pathlib import Path

from helpers import save, smooth_image, write_label

from gp36data.io_utils import PairingError, inspect_image, output_name, pair_images_labels

MULTI_DOT = [
    "plain.jpg",
    "one.dot.jpg",
    "103_jpg.rf.d14ee11bf4ea4f9a6cfa6763e973a5d8.jpg",  # Roboflow pattern (3 dots)
    "a.b.c.d.e.f.jpg",  # 6 dots
    "حفرة 1.jpg",  # unicode + space
    "my pothole (2).v1.jpg",
]


class TestPairing(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.img, self.lbl = self.tmp / "images", self.tmp / "labels"

    def test_multi_dot_and_unusual_names_pair_one_to_one(self):
        for k, name in enumerate(MULTI_DOT):
            save(smooth_image(k), self.img / name)
            write_label(self.lbl / (Path(name).stem + ".txt"), "0 0.5 0.5 0.1 0.1\n")
        pairs, no_label, orphans = pair_images_labels(self.img, self.lbl)
        self.assertEqual(len(pairs), len(MULTI_DOT))
        self.assertEqual(no_label, [])
        self.assertEqual(orphans, [])
        for img, lbl in pairs:
            self.assertEqual(img.stem, lbl.stem)  # whole stem preserved, dots included

    def test_missing_label_and_orphan_label_are_reported(self):
        save(smooth_image(1), self.img / "has.label.jpg")
        save(smooth_image(2), self.img / "no.label.jpg")
        write_label(self.lbl / "has.label.txt", "")
        write_label(self.lbl / "orphan.x.txt", "0 0.5 0.5 0.1 0.1\n")
        pairs, no_label, orphans = pair_images_labels(self.img, self.lbl)
        self.assertEqual([p[0].name for p in pairs], ["has.label.jpg"])
        self.assertEqual([p.name for p in no_label], ["no.label.jpg"])
        self.assertEqual([p.name for p in orphans], ["orphan.x.txt"])

    def test_two_images_with_same_stem_are_ambiguous(self):
        save(smooth_image(1), self.img / "dup.jpg")
        save(smooth_image(2), self.img / "dup.png", "PNG")
        with self.assertRaises(PairingError):
            pair_images_labels(self.img, self.lbl)


class TestInspect(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_valid_jpeg(self):
        info = inspect_image(save(smooth_image(0), self.tmp / "ok.jpg"))
        self.assertTrue(info["ok"])
        self.assertEqual((info["width"], info["height"]), (320, 240))
        self.assertTrue(info["ext_matches_format"])

    def test_disguised_format_detected(self):
        info = inspect_image(save(smooth_image(0), self.tmp / "really_webp.jpg", "WEBP"))
        self.assertTrue(info["ok"])
        self.assertEqual(info["format"], "WEBP")
        self.assertFalse(info["ext_matches_format"])

    def test_truncated_image_is_not_ok(self):
        p = save(smooth_image(0, (1200, 900)), self.tmp / "trunc.jpg", quality=95)
        data = p.read_bytes()
        p.write_bytes(data[: len(data) // 2])
        self.assertFalse(inspect_image(p)["ok"])

    def test_garbage_bytes_not_ok(self):
        p = self.tmp / "garbage.jpg"
        p.write_bytes(b"not an image at all" * 10)
        info = inspect_image(p)
        self.assertFalse(info["ok"])
        self.assertTrue(info["error"])

    def test_exif_orientation_read(self):
        im = smooth_image(0)
        exif = im.getexif()
        exif[0x0112] = 6
        info = inspect_image(save(im, self.tmp / "rot.jpg", exif=exif))
        self.assertEqual(info["exif_orientation"], 6)


class TestOutputNames(unittest.TestCase):
    def test_output_name_is_dot_free_and_content_addressed(self):
        a = output_name("rf8", "a" * 64)
        b = output_name("rf8", "b" * 64)
        self.assertNotEqual(a, b)
        self.assertNotIn(".", a)

    def test_long_names_sharing_a_60_char_prefix_do_not_collide(self):
        # prepare_dataset.py used f.stem[:60]; two such stems would have collided.
        prefix = "x" * 60
        stems = [prefix + "_jpg.rf.aaaa", prefix + "_jpg.rf.bbbb"]
        self.assertEqual(stems[0][:60], stems[1][:60])  # the historical collision condition
        names = {output_name("rf8", h * 64) for h in "ab"}
        self.assertEqual(len(names), 2)

    def test_invalid_source_id_rejected(self):
        with self.assertRaises(ValueError):
            output_name("rf.8", "a" * 64)

    def test_historical_with_suffix_bug_is_real(self):
        # Documents the failure mechanism: with_suffix treats '.<hash>' as the extension.
        stems = ["103_jpg.rf.d14ee11bf4ea", "103_jpg.rf.e2548d8c358"]
        old = {Path("rf_" + s).with_suffix(".jpg").name for s in stems}
        self.assertEqual(len(old), 1)  # two different images collapse onto one name


if __name__ == "__main__":
    unittest.main()
