import math
import unittest
from html.parser import HTMLParser
from pathlib import Path


WIDTH, HEIGHT, BLOCK = 192, 108, 8
C2 = (0.03 * 255) ** 2


def prepare(source):
    out = source.copy()
    for y in range(1, HEIGHT - 1):
        for x in range(1, WIDTH - 1):
            i = y * WIDTH + x
            total = (
                source[i] * 4
                + (source[i - 1] + source[i + 1] + source[i - WIDTH] + source[i + WIDTH]) * 2
                + source[i - WIDTH - 1] + source[i - WIDTH + 1]
                + source[i + WIDTH - 1] + source[i + WIDTH + 1]
            )
            out[i] = total // 16
    return out


def compare(a, b):
    cs_values, bad = [], 0
    for by in range(0, HEIGHT, BLOCK):
        for bx in range(0, WIDTH, BLOCK):
            indexes = [
                y * WIDTH + x
                for y in range(by, min(by + BLOCK, HEIGHT))
                for x in range(bx, min(bx + BLOCK, WIDTH))
            ]
            mean_a = sum(a[i] for i in indexes) / len(indexes)
            mean_b = sum(b[i] for i in indexes) / len(indexes)
            var_a = sum((a[i] - mean_a) ** 2 for i in indexes) / len(indexes)
            var_b = sum((b[i] - mean_b) ** 2 for i in indexes) / len(indexes)
            cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in indexes) / len(indexes)
            cs = max(-1, min(1, (2 * cov + C2) / (var_a + var_b + C2)))
            cs_values.append(cs)
            bad += cs < 0.92

    edge_deltas = []
    for y in range(1, HEIGHT - 1, 2):
        for x in range(1, WIDTH - 1, 2):
            i = y * WIDTH + x
            edge_a = abs(a[i + 1] - a[i - 1]) + abs(a[i + WIDTH] - a[i - WIDTH])
            edge_b = abs(b[i + 1] - b[i - 1]) + abs(b[i + WIDTH] - b[i - WIDTH])
            edge_deltas.append(abs(edge_a - edge_b))

    structure_loss = (1 - sum(cs_values) / len(cs_values)) * 100
    bad_ratio = bad * 100 / len(cs_values)
    edge_ratio = sum(delta >= 14 for delta in edge_deltas) * 100 / len(edge_deltas)
    edge_mean = sum(edge_deltas) / len(edge_deltas)
    return structure_loss * 0.55 + bad_ratio * 0.16 + edge_ratio * 0.35 + edge_mean * 0.10


def average(frames):
    return [round(sum(values) / len(frames)) for values in zip(*frames)]


def percentile(values, p):
    values = sorted(values)
    return values[min(len(values) - 1, math.ceil(len(values) * p) - 1)]


def dynamic_threshold(noise_floor, sensitivity=6):
    return max(0.7, noise_floor * 3 + 0.35) * (1.42 - sensitivity * 0.07)


class DetectionModelTests(unittest.TestCase):
    def setUp(self):
        self.base = prepare([80] * (WIDTH * HEIGHT))

    def test_global_brightness_shift_is_ignored(self):
        brighter = prepare([92] * (WIDTH * HEIGHT))
        self.assertAlmostEqual(compare(brighter, self.base), 0)

    def test_small_text_region_is_detected(self):
        changed = [80] * (WIDTH * HEIGHT)
        for y in range(30, 38):
            for x in range(40, 100):
                changed[y * WIDTH + x] = 180
        self.assertGreater(compare(prepare(changed), self.base), 0.7)

    def test_calibrated_noise_stays_below_slide_change(self):
        frames = []
        for phase in range(10):
            raw = [80 + ((i + phase) % 5 - 2) for i in range(WIDTH * HEIGHT)]
            frames.append(prepare(raw))
        reference = average(frames)
        noise_floor = percentile([compare(frame, reference) for frame in frames], 0.95)
        threshold = dynamic_threshold(noise_floor)
        self.assertTrue(all(compare(frame, reference) < threshold for frame in frames))

    def test_page_load_contract_and_v5_cache(self):
        root = Path(__file__).parents[1]
        html = (root / "index.html").read_text(encoding="utf-8")
        detector = (root / "detector.js").read_text(encoding="utf-8")
        HTMLParser().feed(html)
        self.assertIn('<script src="detector.js"></script>', html)
        self.assertIn("beginCalibration(referenceFrame)", html)
        self.assertIn("PptDetector={", detector)
        self.assertIn("ppt-auto-camera-v5", (root / "sw.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
