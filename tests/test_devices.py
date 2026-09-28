import unittest

from src.devices import EXCLUSIVE, USE, is_allowed, simulate_disk_concurrency


class DeviceTests(unittest.TestCase):
    def test_authorized_device(self):
        self.assertTrue(is_allowed("P4", "audio", USE))
        self.assertTrue(is_allowed("P5", "disco", EXCLUSIVE))

    def test_unauthorized_device(self):
        self.assertFalse(is_allowed("P1", "disco", USE))
        self.assertFalse(is_allowed("P3", "audio", USE))

    def test_mutex_serializes_disk(self):
        manager = simulate_disk_concurrency()
        self.assertEqual(manager.max_parallel_inside["disco"], 1)


if __name__ == "__main__":
    unittest.main()
