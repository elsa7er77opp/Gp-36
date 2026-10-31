"""Tests for the live perception layer (no GPU or Ultralytics needed)."""
import unittest
from pathlib import Path

import helpers  # noqa: F401  (sets sys.path)

from perception.fsm import SAFE, STOP, WARNING, FsmConfig, PerceptionFSM, instant_state
from perception.types import Detection

W, H = 640, 480
CFG = FsmConfig()


def det(ns, cls_id, name, conf, x1, y1, x2, y2):
    """Box given in normalised coordinates."""
    return Detection(ns, cls_id, name, conf, (x1 * W, y1 * H, x2 * W, y2 * H), (W, H))


def person(bottom, x=(0.4, 0.6), conf=0.9, top=None):
    return det("coco", 0, "person", conf, x[0], top if top is not None else bottom - 0.2, x[1], bottom)


def bump(bottom, x=(0.3, 0.7), conf=0.8):
    return det("hazard", 1, "speed_bump", conf, x[0], bottom - 0.05, x[1], bottom)


class TestNamespaces(unittest.TestCase):
    def test_same_class_id_different_models_do_not_collide(self):
        a = det("hazard", 0, "pothole", 0.9, 0.4, 0.6, 0.6, 0.7)
        b = det("coco", 0, "person", 0.9, 0.4, 0.6, 0.6, 0.7)
        self.assertEqual(a.cls_id, b.cls_id)
        self.assertNotEqual(a.label, b.label)
        self.assertNotEqual(a.uid, b.uid)
        self.assertEqual(a.label, "hazard:pothole")
        self.assertEqual(b.uid, "coco:0")

    def test_unknown_namespace_rejected(self):
        with self.assertRaises(ValueError):
            Detection("yolo", 0, "x", 0.5, (0, 0, 1, 1), (W, H))

    def test_fsm_label_lists_are_namespaced(self):
        for lab in CFG.obstacle_labels + CFG.hazard_labels:
            self.assertIn(":", lab)
        self.assertTrue(set(CFG.obstacle_labels).isdisjoint(CFG.hazard_labels))


class TestInstantState(unittest.TestCase):
    def test_empty_is_safe(self):
        self.assertEqual(instant_state([], CFG)[0], SAFE)

    def test_near_person_in_corridor_is_stop(self):
        self.assertEqual(instant_state([person(0.95)], CFG)[0], STOP)

    def test_tall_person_is_stop(self):
        self.assertEqual(instant_state([person(0.8, top=0.2)], CFG)[0], STOP)

    def test_person_ahead_is_warning(self):
        self.assertEqual(instant_state([person(0.65)], CFG)[0], WARNING)

    def test_far_person_is_safe(self):
        self.assertEqual(instant_state([person(0.4)], CFG)[0], SAFE)

    def test_person_outside_corridor_is_safe(self):
        self.assertEqual(instant_state([person(0.95, x=(0.0, 0.2))], CFG)[0], SAFE)

    def test_low_confidence_person_ignored(self):
        self.assertEqual(instant_state([person(0.95, conf=0.2)], CFG)[0], SAFE)

    def test_bump_ahead_is_warning(self):
        self.assertEqual(instant_state([bump(0.7)], CFG)[0], WARNING)

    def test_far_bump_is_safe(self):
        self.assertEqual(instant_state([bump(0.3)], CFG)[0], SAFE)

    def test_hazard_never_stops_on_its_own(self):
        self.assertEqual(instant_state([bump(0.99)], CFG)[0], WARNING)

    def test_unlisted_class_ignored(self):
        chair = det("coco", 56, "chair", 0.9, 0.4, 0.5, 0.6, 0.99)
        self.assertEqual(instant_state([chair], CFG)[0], SAFE)

    def test_range_thresholds(self):
        self.assertEqual(instant_state([], CFG, range_m=0.3)[0], STOP)
        self.assertEqual(instant_state([], CFG, range_m=1.5)[0], WARNING)
        self.assertEqual(instant_state([], CFG, range_m=3.0)[0], SAFE)

    def test_worst_case_wins(self):
        self.assertEqual(instant_state([bump(0.7), person(0.95)], CFG)[0], STOP)


class TestHysteresis(unittest.TestCase):
    def test_escalation_needs_consecutive_frames(self):
        f = PerceptionFSM(CFG)
        self.assertEqual(f.update([person(0.95)], 0.0)[0], SAFE)
        self.assertEqual(f.update([person(0.95)], 0.1)[0], STOP)

    def test_single_glitch_does_not_escalate(self):
        f = PerceptionFSM(CFG)
        f.update([person(0.95)], 0.0)
        self.assertEqual(f.update([], 0.1)[0], SAFE)
        self.assertEqual(f.update([person(0.95)], 0.2)[0], SAFE)

    def test_release_is_slow(self):
        f = PerceptionFSM(CFG)
        f.update([person(0.95)], 0.0)
        f.update([person(0.95)], 0.1)
        t = 0.2
        for _ in range(CFG.release_frames - 1):
            self.assertEqual(f.update([], t)[0], STOP)
            t += 0.1
        self.assertEqual(f.update([], t)[0], SAFE)

    def test_missed_detection_keeps_stop(self):
        f = PerceptionFSM(CFG)
        f.update([person(0.95)], 0.0)
        f.update([person(0.95)], 0.1)
        f.update([], 0.2)
        self.assertEqual(f.update([person(0.95)], 0.3)[0], STOP)

    def test_range_stop_is_immediate(self):
        f = PerceptionFSM(CFG)
        self.assertEqual(f.update([], 0.0, range_m=0.3)[0], STOP)

    def test_stale_input_forces_stop(self):
        f = PerceptionFSM(CFG)
        f.update([], 0.0)
        self.assertEqual(f.tick(0.5)[0], SAFE)
        self.assertEqual(f.tick(CFG.stale_timeout_s + 0.1)[0], STOP)

    def test_no_input_at_all_is_stop(self):
        self.assertEqual(PerceptionFSM(CFG).tick(0.0)[0], STOP)


class TestConfigFile(unittest.TestCase):
    def test_config_yaml_matches_fsm_fields(self):
        import yaml
        root = Path(helpers.ROOT)
        cfg = yaml.safe_load((root / "perception" / "config.yaml").read_text(encoding="utf-8"))
        FsmConfig.from_dict(cfg["fsm"])  # raises on unknown keys
        self.assertEqual(cfg["hazard"]["expect_names"], {0: "pothole", 1: "speed_bump"})
        self.assertEqual(cfg["hazard"]["imgsz"], 960)

    def test_unknown_key_rejected(self):
        with self.assertRaises(ValueError):
            FsmConfig.from_dict({"stop_distance": 1})

    def test_detectors_module_imports_without_ultralytics(self):
        import perception.detectors  # noqa: F401  (Ultralytics is only imported inside the class)


if __name__ == "__main__":
    unittest.main()
