import unittest

from inventory import reserve


class InventoryTests(unittest.TestCase):
    def test_successful_reservation_updates_supplied_stock(self):
        stock = {"apple": 5}
        self.assertIs(reserve(stock, [("apple", 2)]), stock)
        self.assertEqual(stock, {"apple": 3})

    def test_insufficient_first_item_raises(self):
        stock = {"apple": 1}
        with self.assertRaises(ValueError):
            reserve(stock, [("apple", 2)])
        self.assertEqual(stock, {"apple": 1})


if __name__ == "__main__":
    unittest.main()
