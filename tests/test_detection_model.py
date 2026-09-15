import unittest
from html.parser import HTMLParser
from pathlib import Path


PIXEL_DELTA = 10


def frame_metrics(current, reference):
    brightness_shift = sum(a - b for a, b in zip(current, reference)) / len(current)
    deltas = [abs((a - b) - brightness_shift) for a, b in zip(current, reference)]
    mean = sum(deltas) / len(deltas)
    changed_ratio = 100 * sum(delta >= PIXEL_DELTA for delta in deltas) / len(deltas)
    strong_ratio = 100 * sum(delta >= 24 for delta in deltas) / len(deltas)
    top_count = max(1, int(len(deltas) * 0.02))
    top_mean = sum(sorted(deltas, reverse=True)[:top_count]) / top_count
    return mean, changed_ratio, strong_ratio, top_mean, mean + changed_ratio * 1.6 + strong_ratio * 1.2 + top_mean * 0.08


def is_page_change(metrics, threshold):
    return metrics[4] >= threshold or metrics[1] >= max(0.35, threshold * 0.12)


class DetectionModelTests(unittest.TestCase):
    def test_global_brightness_shift_is_ignored(self):
        reference = [80] * 1000
        brighter = [92] * 1000
        self.assertAlmostEqual(frame_metrics(brighter, reference)[4], 0)

    def test_small_text_region_is_detected(self):
        reference = [80] * 1000
        changed = reference.copy()
        changed[:20] = [180] * 20
        self.assertTrue(is_page_change(frame_metrics(changed, reference), 5))

    def test_low_level_sensor_noise_is_ignored(self):
        reference = [80] * 1000
        noisy = [78 if i % 2 else 82 for i in range(1000)]
        self.assertFalse(is_page_change(frame_metrics(noisy, reference), 5))

    def test_html_is_parseable_and_uses_v4_cache(self):
        root = Path(__file__).parents[1]
        html = (root / "index.html").read_text(encoding="utf-8")
        HTMLParser().feed(html)
        self.assertIn("detectorSelfTest()", html)
        self.assertIn("lastPhotoFrame=referenceFrame", html)
        self.assertIn("armed=false", html)
        self.assertIn("rearmAt=performance.now()+vals().cool", html)
        self.assertIn("ppt-auto-camera-v4", (root / "sw.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
