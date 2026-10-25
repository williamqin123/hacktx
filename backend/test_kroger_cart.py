import unittest

from flask_app.kroger_cart import _build_kroger_cart_items


class BuildKrogerCartItemsTests(unittest.TestCase):
    def test_aggregates_duplicate_products_and_supports_legacy_product_urls(self):
        payload = _build_kroger_cart_items([
            {
                "retailer": "Kroger",
                "upc": "0001234567890",
                "quantity": 2,
            },
            {
                "product_page_url": (
                    "https://www.kroger.com/p/a/0001234567890?fulfillment=PICKUP"
                ),
                "quantity": 3,
            },
            {
                "retailer": "Walmart",
                "upc": "987654321098",
                "quantity": 1,
            },
        ])

        self.assertEqual(payload, [{
            "upc": "0001234567890",
            "quantity": 5,
            "modality": "PICKUP",
        }])

    def test_rejects_kroger_items_without_valid_upcs(self):
        with self.assertRaisesRegex(ValueError, "valid UPC"):
            _build_kroger_cart_items([{
                "retailer": "Kroger",
                "upc": "not-a-upc",
                "quantity": 1,
            }])

    def test_requires_at_least_one_kroger_product(self):
        with self.assertRaisesRegex(ValueError, "does not contain any Kroger"):
            _build_kroger_cart_items([{
                "retailer": "Walmart",
                "upc": "987654321098",
                "quantity": 1,
            }])


if __name__ == "__main__":
    unittest.main()
