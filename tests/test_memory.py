import unittest

from src.memory import fifo, lru, optimal

REFS = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5, 2, 1, 5, 3, 2]


class MemoryTests(unittest.TestCase):
    def test_fifo(self):
        result = fifo(REFS, 4)
        self.assertEqual(result.hits, 5)
        self.assertEqual(result.faults, 12)

    def test_lru(self):
        result = lru(REFS, 4)
        self.assertEqual(result.hits, 7)
        self.assertEqual(result.faults, 10)

    def test_optimal(self):
        result = optimal(REFS, 4)
        self.assertEqual(result.hits, 10)
        self.assertEqual(result.faults, 7)

    def test_optimal_is_reference_best(self):
        results = [fifo(REFS, 4), lru(REFS, 4), optimal(REFS, 4)]
        self.assertEqual(min(r.faults for r in results), 7)


if __name__ == "__main__":
    unittest.main()
