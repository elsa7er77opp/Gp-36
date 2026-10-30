import csv
import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from helpers import save, smooth_image

from gp36data.voc import parse_voc, scan_names

NAMES = ["D00", "D10", "D20", "D40"]


def xml(objs, w=600, h=600, fname="Japan_000001.jpg"):
    o = "".join(f"<object><name>{n}</name><bndbox><xmin>{a}</xmin><ymin>{b}</ymin><xmax>{c}</xmax><ymax>{d}</ymax></bndbox></object>"
                for n, a, b, c, d in objs)
    return f"<annotation><filename>{fname}</filename><size><width>{w}</width><height>{h}</height><depth>3</depth></size>{o}</annotation>"


def codes(r):
    return [i.code for i in r.issues]


class TestParseVoc(unittest.TestCase):
    def test_pothole_box_normalised(self):
        r = parse_voc(xml([("D40", 60, 120, 180, 240)]), NAMES)
        self.assertTrue(r.ok)
        b = r.boxes[0]
        self.assertEqual(b.cls, 3)
        self.assertAlmostEqual(b.xc, 0.2); self.assertAlmostEqual(b.yc, 0.3)
        self.assertAlmostEqual(b.w, 0.2); self.assertAlmostEqual(b.h, 0.2)
        self.assertEqual(r.counts, {"D40": 1})

    def test_cracks_keep_their_own_ids_never_pothole(self):
        r = parse_voc(xml([("D00", 0, 0, 10, 10), ("D10", 0, 0, 10, 10), ("D20", 0, 0, 10, 10)]), NAMES)
        self.assertEqual(sorted(b.cls for b in r.boxes), [0, 1, 2])
        self.assertNotIn(3, [b.cls for b in r.boxes])

    def test_unknown_name_is_error_not_dropped(self):
        r = parse_voc(xml([("D43", 0, 0, 10, 10), ("D40", 0, 0, 10, 10)]), NAMES)
        self.assertFalse(r.ok)
        self.assertIn("UNKNOWN_NAME", codes(r))

    def test_float_coordinates_and_no_objects(self):
        self.assertTrue(parse_voc(xml([("D40", 10.5, 20.25, 100.0, 200.75)]), NAMES).ok)
        r = parse_voc(xml([]), NAMES)
        self.assertTrue(r.ok); self.assertEqual(r.boxes, [])

    def test_errors(self):
        self.assertIn("XML_PARSE", codes(parse_voc("<annotation><size>", NAMES)))
        self.assertIn("BAD_SIZE", codes(parse_voc(xml([], w=0), NAMES)))
        self.assertIn("NONPOSITIVE_WH", codes(parse_voc(xml([("D40", 50, 50, 50, 80)]), NAMES)))
        self.assertIn("NONPOSITIVE_WH", codes(parse_voc(xml([("D40", 90, 50, 50, 80)]), NAMES)))
        self.assertIn("EXCEEDS_IMAGE", codes(parse_voc(xml([("D40", 500, 500, 700, 590)]), NAMES)))
        self.assertIn("BAD_BNDBOX", codes(parse_voc(xml([("D40", "", 1, 2, 3)]), NAMES)))

    def test_small_overhang_clipped_with_warning(self):
        r = parse_voc(xml([("D40", 500, 500, 603, 590)]), NAMES)
        self.assertTrue(r.ok)
        self.assertIn("CLIPPED", codes(r))
        self.assertLessEqual(r.boxes[0].xc + r.boxes[0].w / 2, 1.0 + 1e-9)

    def test_real_image_size_must_match(self):
        self.assertIn("SIZE_MISMATCH", codes(parse_voc(xml([], w=600, h=600), NAMES, image_size=(720, 720))))
        self.assertTrue(parse_voc(xml([], w=600, h=600), NAMES, image_size=(600, 600)).ok)

    def test_scan_names(self):
        self.assertEqual(scan_names([xml([("D40", 0, 0, 1, 1), ("D00", 0, 0, 1, 1)]), xml([("D40", 0, 0, 1, 1)])]),
                         {"D40": 2, "D00": 1})


class TestConvertTool(unittest.TestCase):
    def test_convert_end_to_end_atomic_and_refuses_existing(self):
        import tools.convert_voc as cv
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for i, objs in enumerate([[("D40", 60, 60, 120, 120)], [("D00", 0, 0, 50, 50)], [], [("D99", 0, 0, 5, 5)]]):
                save(smooth_image(i, (600, 600)), d / "img" / f"Japan_{i:06d}.jpg")
                (d / "xml").mkdir(exist_ok=True)
                (d / "xml" / f"Japan_{i:06d}.xml").write_text(xml(objs))
            save(smooth_image(9, (600, 600)), d / "img" / "Japan_000009.jpg")  # image without xml
            out = d / "out"
            rc = cv.main(["--xml-dir", str(d / "xml"), "--img-dir", str(d / "img"), "--out", str(out), "--names", ",".join(NAMES)])
            self.assertEqual(rc, 1)  # one file had an unknown name
            s = json.loads((out / "summary.json").read_text())
            self.assertEqual((s["ok"], s["error"], s["no_objects"], s["image_without_xml"]), (3, 1, 1, 1))
            self.assertEqual((out / "labels" / "Japan_000000.txt").read_text().split()[0], "3")
            self.assertFalse((out / "labels" / "Japan_000003.txt").exists())  # no partial label on error
            with open(out / "conversion_manifest.csv", encoding="utf-8") as fh:
                st = {r["stem"]: r["status"] for r in csv.DictReader(fh)}
            self.assertEqual(st["Japan_000003"], "error")
            self.assertFalse((d / "out.partial").exists())
            self.assertEqual(cv.main(["--xml-dir", str(d / "xml"), "--img-dir", str(d / "img"), "--out", str(out), "--names", "D40"]), 2)


if __name__ == "__main__":
    unittest.main()
