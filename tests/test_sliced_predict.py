"""tools/sliced_predict.py pure parts: tile grid coverage, shift + inner-edge filter, NMS / WBF merge, json format."""
import sys
import unittest

from helpers import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import sliced_predict as sp  # noqa: E402


class TestGrid(unittest.TestCase):
    def test_covers_whole_image(self):
        W, H = 1920, 1080
        g = sp.tile_grid(W, H, 640, 0.25)
        self.assertEqual(max(t[2] for t in g), W)
        self.assertEqual(max(t[3] for t in g), H)
        self.assertTrue(all(t[2] - t[0] == 640 and t[3] - t[1] == 640 for t in g))
        # every pixel column / row is covered
        for x in range(0, W, 7):
            self.assertTrue(any(t[0] <= x < t[2] for t in g))
        for y in range(0, H, 7):
            self.assertTrue(any(t[1] <= y < t[3] for t in g))

    def test_small_image_single_tile(self):
        self.assertEqual(sp.tile_grid(500, 400, 640, 0.25), [(0, 0, 500, 400)])

    def test_rows_from_skips_sky_rows(self):
        g = sp.tile_grid(1920, 1080, 640, 0.25, rows_from=0.8)
        self.assertTrue(all(t[3] >= 0.8 * 1080 for t in g))
        self.assertLess(len(g), len(sp.tile_grid(1920, 1080, 640, 0.25)))


class TestShift(unittest.TestCase):
    def test_shift_to_frame(self):
        out = sp.shift_and_filter([(0, 0.9, [10, 10, 20, 20])], (100, 200, 740, 840), 1920, 1080)
        self.assertEqual(out, [(0, 0.9, [110, 210, 20, 20])])

    def test_inner_border_box_dropped_image_border_kept(self):
        tile = (0, 440, 640, 1080)  # left and bottom = image border, top and right = inner
        dets = [(0, 0.9, [0, 600, 50, 50]),      # touches the left IMAGE border -> kept
                (0, 0.9, [600, 100, 40, 40]),    # touches the inner right border -> dropped
                (0, 0.9, [100, 0, 40, 40])]      # touches the inner top border -> dropped
        out = sp.shift_and_filter(dets, tile, 1920, 1080)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0][2][:2], [0, 1040])


class TestMerge(unittest.TestCase):
    def test_nms_classwise(self):
        d = [(0, 0.9, [0, 0, 10, 10]), (0, 0.8, [1, 0, 10, 10]), (1, 0.7, [0, 0, 10, 10])]
        out = sp.merge(d, "nms", 0.5)
        self.assertEqual(sorted((c, s) for c, s, _ in out), [(0, 0.9), (1, 0.7)])

    def test_wbf_merges_without_rescale(self):
        d = [(0, 0.8, [0, 0, 10, 10]), (0, 0.6, [1, 0, 10, 10])]
        (c, s, b), = sp.merge(d, "wbf", 0.5)
        self.assertAlmostEqual(s, 0.7)
        self.assertAlmostEqual(b[0], 0.6 / 1.4)

    def test_json_format(self):
        j = sp.to_json("img1", [(1, 0.5, [1, 2, 3, 4])])
        self.assertEqual(j, [{"image_id": "img1", "category_id": 2, "bbox": [1, 2, 3, 4], "score": 0.5}])


if __name__ == "__main__":
    unittest.main()
