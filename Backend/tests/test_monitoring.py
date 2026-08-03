import importlib
import unittest

from Backend.app.health_engine import calculate_health_score
from Backend.app.routes import monitoring as monitoring_routes
from Backend.app.trend_engine import evaluate_trend
from Backend.app.rul_engine import calculate_rul


class MonitoringEngineTests(unittest.TestCase):
    def test_health_score_returns_0_to_100(self):
        score = calculate_health_score(95, 0.18, 45, 8.5, 1500)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_trend_detection_flags_critical_when_metrics_rise(self):
        history = [
            {"temperature": 70 + i, "vibration": 0.01 + 0.002 * i, "electrical_current": 20 + 0.2 * i}
            for i in range(10)
        ]
        result = evaluate_trend(history)
        self.assertEqual(result["overall"], "CRITICAL")

    def test_rul_is_positive(self):
        rul = calculate_rul(35, 0.9, "CRITICAL")
        self.assertGreater(rul, 0)

    def test_monitoring_loop_starts_only_when_requested(self):
        module = importlib.reload(monitoring_routes)
        self.assertTrue(callable(getattr(module, "start_monitoring_loop", None)))
        self.assertFalse(module.is_monitoring_loop_running())


if __name__ == "__main__":
    unittest.main()
