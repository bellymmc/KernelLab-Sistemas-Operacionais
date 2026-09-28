import unittest
from pathlib import Path

from src.main import load_processes
from src.metrics import averages, calculate_metrics
from src.schedulers import fcfs, priority, round_robin, sjf

ROOT = Path(__file__).resolve().parents[1]
PROCESSES = load_processes(ROOT / "data" / "processes.json")


class SchedulerTests(unittest.TestCase):
    def test_fcfs_known_metrics(self):
        result = fcfs(PROCESSES)
        avg = averages(result)
        self.assertAlmostEqual(avg["waiting"], 13.6666666667)
        self.assertEqual(result.context_switches, 5)
        self.assertEqual([m.waiting for m in calculate_metrics(result) if m.pid == "P4"][0], 18)

    def test_sjf_order(self):
        result = sjf(PROCESSES)
        order = [s.pid for s in result.gantt]
        self.assertEqual(order, ["P1", "P4", "P2", "P6", "P3", "P5"])

    def test_priority_order(self):
        result = priority(PROCESSES)
        order = [s.pid for s in result.gantt]
        self.assertEqual(order, ["P1", "P4", "P2", "P6", "P3", "P5"])

    def test_round_robin_quantum_three(self):
        result = round_robin(PROCESSES, 3)
        self.assertEqual(result.completion["P4"], 11)
        self.assertEqual(result.context_switches, 13)
        self.assertAlmostEqual(averages(result)["response"], 5.3333333333)


if __name__ == "__main__":
    unittest.main()
