# VIRAL ALPHA RADAR JACK 🛰️

Eigenständiger Telegram-Alert-Bot zur **Beobachtung** von Memecoins mit auffälligen viralen Geschichten, etwa Gaming-News, Elon-/Space-Themen, Internet-Memes und anderen Trends.

**Status:** Einrichtung läuft. Der Bot sendet erst dann Nachrichten, wenn der Programmcode, der GitHub-Actions-Workflow und die Repository-Secrets vollständig eingerichtet und getestet wurden.

## Prinzip
- Recherchiert Schlagzeilen über öffentliche News-RSS-Feeds.
- Vergleicht Coin-Namen mit aktuellen Nachrichten und sucht passende Tokens über DEX Screener.
- Bewertet Handelsaktivität, Liquidität, Marktkapitalisierung und verfügbare Risikoindikatoren.
- Meldet nur Coins oberhalb eines konfigurierbaren Schwellenwerts an einen **eigenen** Telegram-Chat.

⚠️ Die Nachrichten beweisen **keine** Partnerschaft mit Rockstar, Elon Musk oder anderen Personen. Scores sind **keine** Gewinnwahrscheinlichkeiten. Risikoscans sind unvollständig, insbesondere bei frisch gestarteten Token. Keine Auto-Trades, Wallets oder privaten Schlüssel.

## Telegram und GitHub
Die Zugangsdaten dürfen **niemals** in GitHub-Dateien oder in einen Chat kopiert werden. Unter `Settings → Secrets and variables → Actions` werden später zwei **Repository secrets** eingerichtet:
- `TELEGRAM_BOT_TOKEN`: der **neue** von BotFather generierte Token.
- `TELEGRAM_CHAT_ID`: die eigene numerische Chat-ID.

Das Projekt soll mit GitHub Actions automatisch laufen. GitHub Actions ist **nicht sekundengenau** und kann geplante Läufe verschieben oder aussetzen. Öffentliche News-Feeds sehen nicht jeden neuen X-Post oder On-Chain-Launch.

Weitere Hinweise folgen mit den Programmdateien.
