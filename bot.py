#!/usr/bin/env python3
"""Viral Alpha Radar Jack — read-only, story-led memecoin alerts."""
import datetime as dt
import html
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import quote

import requests

LOG = logging.getLogger("radar")
UTC = dt.timezone.utc
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()
MIN_SCORE = int(os.getenv("MIN_ALERT_SCORE", "70"))
STATE = Path("state.json")
SES = requests.Session()
SES.headers["User-Agent"] = "ViralAlphaRadarJack/1.1"
CHAINS = {"solana": "solana", "ethereum": "ethereum", "base": "base", "bsc": "bsc"}
CHAIN_IDS = {"ethereum": "1", "base": "8453", "bsc": "56"}
NEWS = [
    '("GTA 6" OR "GTA VI" OR "Rockstar Games") (meme OR crypto OR viral OR trailer)',
    '("Elon Musk" OR "SpaceX") (asteroid OR meme OR shiba OR viral OR crypto)',
    '("viral animal" OR "viral internet story" OR "internet sensation")',
    '("DaCity" OR "Pepe" OR "SafeMoon" OR memecoin) (viral OR gaming OR trend)',
]
SEEDS = ["dacity", "gta 6", "asteroid shiba", "elon", "pepe"]
STOP = set("""news viral meme coin crypto rockstar games internet latest launch market
    price token today first video watch after about with from this that will gtv
    grand theft auto solana ethereum youtube twitter trailer report says
    the and""".split())
STABLE = {"USDT", "USDC", "ETH", "WETH", "SOL", "WSOL", "WBTC", "DAI", "WBNB"}


def number(val):
    try:
        return float(val or 0)
    except (ValueError, TypeError):
        return 0.0


def webget(url, params=None):
    try:
        r = SES.get(url, params=params, timeout=12)
        r.raise_for_status()
        return r
    except requests.RequestException:
        LOG.warning("External source unavailable")
        return None


def tg(method, payload):
    if not TOKEN:
        return None
    try:
        r = SES.post("https://api.telegram.org/bot" + TOKEN + "/" + method,
                     json=payload, timeout=12)
        r.raise_for_status()
        data = r.json()
        if data.get("ok"):
            return data.get("result")
    except (ValueError, requests.RequestException):
        pass
    LOG.warning("Telegram operation failed: %s", method)
    return None


def send(msg):
    if not CHAT:
        return False
    return tg("sendMessage", {"chat_id": CHAT, "text": msg[:3800],
                              "disable_web_page_preview": True}) is not None


def state_load():
    try:
        result = json.loads(STATE.read_text(encoding="utf-8"))
        if isinstance(result, dict):
            return result
    except (OSError, ValueError):
        pass
    return {"offset": 0, "alerts": {}, "last_scan": "", "top": []}


def latest_news():
    stories, seen = [], set()
    for search in NEWS:
        url = "https://news.google.com/rss/search?q=" + quote(search) + "&hl=en-US&gl=US&ceid=US:en"
        r = webget(url)
        if r is None:
            continue
        try:
            items = ET.fromstring(r.content).findall("./channel/item")
        except ET.ParseError:
            continue
        for item in items[:25]:
            link = item.findtext("link") or ""
            title = html.unescape(item.findtext("title") or "").strip()
            if not link or not title or link in seen:
                continue
            seen.add(link)
            try:
                pub = parsedate_to_datetime(item.findtext("pubDate") or "")
                age = (dt.datetime.now(UTC) - pub.astimezone(UTC)).total_seconds() / 3600
            except (TypeError, ValueError, OverflowError):
                continue
            if 0 <= age <= 72:
                stories.append({"title": title, "url": link, "age": age,
                                "source": title.rsplit(" - ", 1)[-1]})
    return sorted(stories, key=lambda x: x["age"])


def search_queries(stories):
    queries = list(SEEDS)
    for story in stories[:35]:
        for name in re.findall(r"\b[A-Z][a-zA-Z0-9]{3,18}\b", story["title"]):
            term = name.lower()
            if term not in STOP and term not in queries:
                queries.append(term)
            if len(queries) == 16:
                return queries
    return queries


def market_pairs(stories):
    found = {}
    for query in search_queries(stories):
        r = webget("https://api.dexscreener.com/latest/dex/search", {"q": query})
        if r is None:
            continue
        try:
            pairs = r.json().get("pairs") or []
        except (ValueError, AttributeError):
            continue
        for pair in pairs[:25]:
            chain = str(pair.get("chainId", "")).lower()
            base = pair.get("baseToken") or {}
            address = str(base.get("address", "")).lower()
            if chain not in CHAINS or not address or str(base.get("symbol", "")).upper() in STABLE:
                continue
            key = chain + ":" + address
            liq = number((pair.get("liquidity") or {}).get("usd"))
            old = found.get(key)
            if old is None or liq > number((old.get("liquidity") or {}).get("usd")):
                found[key] = pair
    return list(found.values())


def linked_news(pair, stories):
    base = pair.get("baseToken") or {}
    name = re.sub(r"[^a-z0-9]+", " ", str(base.get("name", "")).lower()).strip()
    symbol = str(base.get("symbol", "")).lower()
    if len(name) < 5 or name in STOP:
        return []
    results = []
    for story in stories:
        headline = re.sub(r"[^a-z0-9]+", " ", story["title"].lower())
        name_hit = bool(re.search(r"\b" + re.escape(name) + r"\b", headline))
        ticker_hit = (len(symbol) >= 5 and symbol not in STOP and
                      bool(re.search(r"\b" + re.escape(symbol) + r"\b", headline)))
        if name_hit or ticker_hit:
            results.append(story)
    return results[:8]


def risk_check(chain, address):
    if chain == "solana":
        url, params = "https://api.gopluslabs.io/api/v1/solana/token_security", {"contract_addresses": address}
    elif chain in CHAIN_IDS:
        url = "https://api.gopluslabs.io/api/v1/token_security/" + CHAIN_IDS[chain]
        params = {"contract_addresses": address}
    else:
        return False, []
    r = webget(url, params)
    if r is None:
        return False, []
    try:
        data = r.json().get("result") or {}
        obj = data.get(address.lower()) or data.get(address) or next(iter(data.values()))
        if not isinstance(obj, dict):
            return False, []
    except (ValueError, TypeError, AttributeError, StopIteration):
        return False, []
    if chain == "solana":
        checked = any(k in obj for k in ("mintable", "freezable"))
        flags = [key for key in ("mintable", "freezable") if
                 isinstance(obj.get(key), dict) and str(obj[key].get("status")) == "1"]
    else:
        checked = any(k in obj for k in ("is_honeypot", "is_mintable", "sell_tax"))
        fields = ("is_honeypot", "is_mintable", "cannot_sell", "cannot_sell_all",
                  "owner_change_balance", "transfer_pausable")
        flags = [key for key in fields if str(obj.get(key, "")) == "1"]
        if number(obj.get("sell_tax")) > 0.15 or number(obj.get("buy_tax")) > 0.15:
            flags.append("high tax")
    return checked, flags


def evaluate(pair, stories, checked=False):
    chain = str(pair.get("chainId", "")).lower()
    base = pair.get("baseToken") or {}
    address = str(base.get("address", ""))
    if chain not in CHAINS or not address:
        return None
    liq = number((pair.get("liquidity") or {}).get("usd"))
    mc = number(pair.get("marketCap")) or number(pair.get("fdv"))
    vol = number((pair.get("volume") or {}).get("h1"))
    tx = (pair.get("txns") or {}).get("h1") or {}
    buys, sells = int(number(tx.get("buys"))), int(number(tx.get("sells")))
    p1 = number((pair.get("priceChange") or {}).get("h1"))
    p24 = number((pair.get("priceChange") or {}).get("h24"))
    created = number(pair.get("pairCreatedAt"))
    age = (dt.datetime.now(UTC).timestamp() * 1000 - created) / 86400000 if created else 9999
    if not (liq >= 15000 and 50000 <= mc <= 30000000 and vol >= 3000
            and buys + sells >= 15 and 0 <= age <= 90):
        return None
    news = linked_news(pair, stories)
    if not news:
        return None
    score = 30 + (5 if len({a["source"] for a in news}) > 1 else 0)
    score += min(10, round(12 * buys / max(1, buys + sells)))
    score += min(8, round(vol / liq * 12))
    score += 5 if 0 < p1 <= 85 else 1 if p1 > 85 else 0
    score += 2 if 0 < p24 <= 250 else 0
    score += 15 if liq >= 250000 else 12 if liq >= 100000 else 9 if liq >= 50000 else 5
    score += 10 if mc <= 3000000 else 8 if mc <= 10000000 else 4
    score += 15 if checked else 0
    if p1 < -35:
        score -= 8
    if age < .02:
        score -= 8
    if not checked:
        score = min(score, 79)
    return {"name": base.get("name", "?"), "symbol": base.get("symbol", "?"),
            "chain": chain, "address": address, "score": max(0, min(100, int(score))),
            "url": pair.get("url") or "https://dexscreener.com",
            "news": news[0], "sources": len({a["source"] for a in news}),
            "mc": mc, "liq": liq, "vol": vol, "p1": p1, "p24": p24,
            "buys": buys, "sells": sells, "checked": checked}


def money(x):
    return "USD " + (f"{x / 1e6:.2f}M" if x >= 1e6 else
                     f"{x / 1e3:.1f}K" if x >= 1e3 else f"{x:.0f}")


def alert(c):
    news = c["news"]
    tier = "🔥 A-RADAR" if c["score"] >= 85 else "⚡ B-RADAR"
    return (f"{tier}: {c['score']}/100 (heuristischer Score)\n"
            f"🪙 {c['name']} ({c['symbol']}) | {c['chain']}\n"
            f"Story: {news['title'][:160]}\n{news['url']}\n"
            f"Erwähnung in {c['sources']} Quelle(n), KEINE bestätigte Partnerschaft.\n"
            f"Cap/FDV {money(c['mc'])} | Liquidität {money(c['liq'])}\n"
            f"Vol. 1h {money(c['vol'])} | Käufe/Verkäufe 1h {c['buys']}/{c['sells']}\n"
            f"1h {c['p1']:+.1f}% | 24h {c['p24']:+.1f}%\n"
            f"Contract: {c['address']}\nChart: {c['url']}\n"
            f"Risiko-Daten: {'teilweise geprüft' if c['checked'] else 'unbekannt'}\n"
            "⚠️ Keine Sicherheitsgarantie oder Kaufempfehlung.")


def commands(state):
    events = tg("getUpdates", {"offset": int(state.get("offset", 0)) + 1,
                               "timeout": 0, "limit": 40})
    if not isinstance(events, list):
        return False
    changed = False
    for event in events:
        state["offset"] = max(int(state.get("offset", 0)), int(event.get("update_id", 0)))
        changed = True
        msg = event.get("message") or {}
        if str((msg.get("chat") or {}).get("id")) != CHAT:
            continue
        text = (msg.get("text") or "").split(" ", 1)[0].lower()
        if text in ("/start", "/help"):
            send("🛰 VIRAL ALPHA RADAR JACK\n\n"
                 "News- und Momentum-Screening. Kein Trading-Bot.\n"
                 "/status = letzter gespeicherter Scan\n/top = letzte Kandidaten\n"
                 "Antworten erscheinen erst beim nächsten automatischen Scan.")
        elif text == "/status":
            send("Letzter abgeschlossener Scan: " + str(state.get("last_scan", "unbekannt")))
        elif text == "/top":
            items = state.get("top") or []
            send("🛰 Letzte Kandidaten:\n" + (
                "\n".join(f"{x['name']} | {x['score']}/100 | {x['url']}" for x in items[:8])
                if items else "Noch keine Kandidaten"))
    return changed


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not TOKEN or not CHAT:
        raise SystemExit("Fehlende GitHub-Secrets TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID")
    state = state_load()
    stories = latest_news()
    pairs = market_pairs(stories)
    first = [(evaluate(pair, stories), pair) for pair in pairs]
    first = [(candidate, pair) for candidate, pair in first if candidate]
    first.sort(key=lambda x: x[0]["score"], reverse=True)
    evaluated = []
    for candidate, pair in first[:25]:
        checked, flags = risk_check(candidate["chain"], candidate["address"])
        if flags:
            LOG.info("Flagged risky token omitted")
            continue
        candidate = evaluate(pair, stories, checked)
        if candidate:
            evaluated.append(candidate)
    evaluated.sort(key=lambda x: x["score"], reverse=True)
    now = dt.datetime.now(UTC).timestamp()
    sent = 0
    for candidate in evaluated:
        if candidate["score"] < MIN_SCORE or sent >= 3:
            continue
        key = candidate["chain"] + ":" + candidate["address"].lower()
        prev = state.setdefault("alerts", {}).get(key) or {}
        if prev and now - number(prev.get("at")) < 86400:
            continue
        if send(alert(candidate)):
            state["alerts"][key] = {"at": now, "score": candidate["score"]}
            sent += 1
    # Save each completed scan, not just one every six hours.
    # This also means /status shows the scan that processed the command.
    finished = dt.datetime.now(UTC).astimezone(ZoneInfo("Europe/Zurich"))
    state["last_scan"] = finished.strftime("%d.%m.%Y %H:%M Uhr (Schweiz)")
    state["last_saved_at"] = now
    state["top"] = [{k: item[k] for k in ("name", "score", "url")} for item in evaluated[:10]]
    commands(state)
    state["alerts"] = dict(list(state["alerts"].items())[-500:])
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    LOG.info("Scan complete: %d matching; %d alerts", len(evaluated), sent)


if __name__ == "__main__":
    main()
