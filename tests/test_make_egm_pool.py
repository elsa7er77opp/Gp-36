"""tools/make_egm_pool.py: panorama drop, spacing per sequence, cap, creator split (no pixels needed)."""
import sys
import unittest

from helpers import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import make_egm_pool as eg  # noqa: E402


def r(i, seq, creator, lon, lat, t, pano=False):
    return {"image": f"{i}.jpg", "id": str(i), "sequence": seq, "creator": creator, "is_pano": pano, "lon": lon,
            "lat": lat, "captured_at": t, "width": 4000, "height": 3000, "tile": "x"}


class TestPool(unittest.TestCase):
    def test_haversine(self):
        self.assertAlmostEqual(eg.haversine_m((31.0, 30.0), (31.0, 30.001)), 111.2, delta=0.5)

    def test_thin_spacing_pano_and_cap(self):
        step = 0.00005  # ~ 5.6 m in latitude
        rows = [r(k, "s1", "c1", 31.0, 30.0 + k * step, k) for k in range(20)]
        rows.append(r(99, "s1", "c1", 31.5, 30.5, 100, pano=True))
        rows.append(r(98, "", "c1", 31.5, 30.5, 100))
        kept = eg.thin(rows, min_gap_m=15, max_per_seq=40)
        self.assertEqual([x["id"] for x in kept], ["0", "3", "6", "9", "12", "15", "18"])  # every ~16.7 m
        self.assertEqual(len(eg.thin(rows, min_gap_m=15, max_per_seq=2)), 2)

    def test_time_order_not_file_order(self):
        rows = [r(1, "s", "c", 31.0, 30.001, 5), r(2, "s", "c", 31.0, 30.0, 1)]
        self.assertEqual([x["id"] for x in eg.thin(rows, 15, 40)], ["2", "1"])

    def test_creator_split_deterministic(self):
        rows = []
        for ci, n in enumerate([5, 4, 3, 2, 1, 1]):
            rows += [r(f"{ci}_{k}", f"s{ci}", f"c{ci}", 31.0, 30.0 + k, k) for k in range(n)]
        out = eg.split_by_creator(rows, eval_every=3)
        pools = {x["creator"]: x["pool"] for x in out}
        self.assertEqual(pools, {"c0": "train", "c1": "train", "c2": "eval", "c3": "train", "c4": "train", "c5": "eval"})
        # one creator never sits in both pools
        self.assertTrue(all(len({x["pool"] for x in out if x["creator"] == c}) == 1 for c in pools))


if __name__ == "__main__":
    unittest.main()
