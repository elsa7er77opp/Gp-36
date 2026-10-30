import unittest

import helpers  # noqa: F401  (sets sys.path)

from gp36data.labels import (Box, ClassMappingError, compare_box_sets, format_label, has_errors, map_classes,
                             parse_label_text)


def codes(text):
    return [i.code for i in parse_label_text(text)[1]]


class TestParse(unittest.TestCase):
    def test_valid_bbox(self):
        boxes, issues = parse_label_text("0 0.5 0.5 0.2 0.1\n1 0.1 0.9 0.05 0.05\n")
        self.assertEqual(issues, [])
        self.assertEqual([b.cls for b in boxes], [0, 1])

    def test_blank_lines_ignored(self):
        self.assertEqual(parse_label_text("\n  \n0 0.5 0.5 0.2 0.1\n\n")[1], [])

    def test_errors(self):
        cases = {
            "x 0.5 0.5 0.1 0.1": "NONNUMERIC",
            "0.5 0.5 0.5 0.1 0.1": "NONINT_CLASS",
            "-1 0.5 0.5 0.1 0.1": "NEGATIVE_CLASS",
            "0 0.5 0.5 0 0.1": "NONPOSITIVE_WH",
            "0 0.5 0.5 -0.1 0.1": "NONPOSITIVE_WH",
            "0 1.5 0.5 0.1 0.1": "CENTER_OUT_OF_RANGE",
            "0 0.5 0.5 1.4 0.1": "EXCEEDS_IMAGE",
            "0 0.02 0.5 0.2 0.1": "EXCEEDS_IMAGE",
            "0 nan 0.5 0.1 0.1": "NONFINITE",
            "0 0.5 0.5 0.1": "BAD_TOKEN_COUNT",
            "0 0.1 0.1 0.2 0.2 0.3": "BAD_TOKEN_COUNT",
            "0 0.1 0.1 0.5 1.4 0.9 0.1": "POLY_OUT_OF_RANGE",
            "0 0.1 0.1 0.1 0.5 0.1 0.9": "POLY_DEGENERATE",
        }
        for line, code in cases.items():
            with self.subTest(line=line):
                boxes, issues = parse_label_text(line)
                self.assertEqual(boxes, [])
                self.assertIn(code, [i.code for i in issues])
                self.assertTrue(has_errors(issues))

    def test_small_overhang_is_clipped_with_warning(self):
        boxes, issues = parse_label_text("0 0.05 0.5 0.105 0.1")  # exceeds left edge by 0.0025
        self.assertEqual([i.code for i in issues], ["CLIPPED"])
        self.assertFalse(has_errors(issues))
        x1, _, _, _ = boxes[0].xyxy()
        self.assertAlmostEqual(x1, 0.0)

    def test_duplicate_box_warning(self):
        boxes, issues = parse_label_text("0 0.5 0.5 0.2 0.1\n0 0.5 0.5 0.2 0.1\n")
        self.assertEqual(len(boxes), 1)
        self.assertEqual(codes("0 0.5 0.5 0.2 0.1\n0 0.5 0.5 0.2 0.1\n"), ["DUPLICATE_BOX"])

    def test_polygon_converted_to_bbox(self):
        boxes, issues = parse_label_text("1 0.1 0.2 0.5 0.2 0.5 0.6 0.1 0.6")
        self.assertEqual(issues, [])
        b = boxes[0]
        self.assertEqual((b.cls, b.kind), (1, "poly"))
        for got, want in zip((b.xc, b.yc, b.w, b.h), (0.3, 0.4, 0.4, 0.4)):
            self.assertAlmostEqual(got, want)

    def test_format_roundtrip(self):
        boxes, _ = parse_label_text("0 0.5 0.5 0.2 0.1\n")
        again, issues = parse_label_text(format_label(boxes))
        self.assertEqual(issues, [])
        self.assertEqual(len(again), 1)


class TestMapping(unittest.TestCase):
    def test_maps_by_name(self):
        out, ign = map_classes([Box(0, .5, .5, .1, .1)], {0: "speed_bump"})
        self.assertEqual(out[0].cls, 1)  # target id of speed_bump, not the source id
        self.assertEqual(ign, {})

    def test_unmapped_source_class_raises(self):
        with self.assertRaises(ClassMappingError):
            map_classes([Box(3, .5, .5, .1, .1)], {0: "pothole"})

    def test_ignored_classes_are_counted_not_dropped_silently(self):
        out, ign = map_classes([Box(0, .5, .5, .1, .1), Box(2, .5, .5, .1, .1)], {0: "pothole"}, ignore=[2])
        self.assertEqual(len(out), 1)
        self.assertEqual(ign, {2: 1})

    def test_unknown_target_name_raises(self):
        with self.assertRaises(ClassMappingError):
            map_classes([], {0: "crack"})


class TestCompare(unittest.TestCase):
    def test_same_minor_conflict(self):
        a = [Box(0, .5, .5, .2, .2)]
        self.assertEqual(compare_box_sets(a, [Box(0, .5, .5, .2, .2)]), "same")
        self.assertEqual(compare_box_sets(a, [Box(0, .52, .5, .2, .2)]), "minor")
        self.assertEqual(compare_box_sets(a, [Box(1, .5, .5, .2, .2)]), "conflict")
        self.assertEqual(compare_box_sets(a, a + [Box(0, .1, .1, .05, .05)]), "conflict")
        self.assertEqual(compare_box_sets(a, [Box(0, .8, .8, .2, .2)]), "conflict")
        self.assertEqual(compare_box_sets([], []), "same")


if __name__ == "__main__":
    unittest.main()
