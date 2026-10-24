import datetime as dt
import unittest

import bot


class TestViralAlphaRadar(unittest.TestCase):
    def pair(self, name="DaCityCoin", liquidity=120000):
        return {
            "chainId": "solana",
            "baseToken": {"name": name, "symbol": "DACITY", "address": "ExampleContract"},
            "liquidity": {"usd": liquidity},
            "marketCap": 1200000,
            "volume": {"h1": 60000},
            "txns": {"h1": {"buys": 150, "sells": 60}},
            "priceChange": {"h1": 12, "h24": 35},
            "pairCreatedAt": (dt.datetime.now(dt.timezone.utc).timestamp() - 3600 * 30) * 1000,
            "url": "https://dexscreener.com/solana/example",
        }

    def news(self):
        return [{"title": "GTA VI DaCityCoin gains traction - Example Source",
                 "url": "https://example.org/article", "age": 2,
                 "source": "Example Source"}]

    def test_story_matches_directly(self):
        x = bot.evaluate(self.pair(), self.news())
        self.assertIsNotNone(x)
        self.assertEqual(x["name"], "DaCityCoin")

    def test_no_story_means_no_alert_candidate(self):
        self.assertIsNone(bot.evaluate(self.pair(), []))

    def test_low_liquidity_excluded(self):
        self.assertIsNone(bot.evaluate(self.pair(liquidity=200), self.news()))

    def test_uncertain_risk_data_limits_score(self):
        x = bot.evaluate(self.pair(), self.news(), checked=False)
        self.assertLessEqual(x["score"], 79)

    def test_found_risk_data_can_raise_score(self):
        a = bot.evaluate(self.pair(), self.news(), checked=False)
        b = bot.evaluate(self.pair(), self.news(), checked=True)
        self.assertGreaterEqual(b["score"], a["score"])


if __name__ == "__main__":
    unittest.main()
