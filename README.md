# 🛰 Viral Alpha Radar Jack

**Eigenständiger Telegram-Bot für Memecoin-Storys und Handelsmomentum.** Der Programmcode ist installiert. **Er läuft erst automatisch, wenn du die Secrets ergänzt und die geplanten Scans freischaltest.**

## Was kann diese Version?

Der Bot durchsucht Google-News-RSS nach viralen Ereignissen (GTA 6/Gaming, Elon/SpaceX, Tiere/Internet-Memes und Krypto-Narrative). Er bildet daraus Suchanfragen für DEX Screener und prüft Coins auf **Solana, Ethereum, Base und BNB Chain**. Für einen Telegram-Alert müssen News-Titel den Coin-Namen oder einen ausreichend eindeutigen Ticker direkt nennen. Danach bewertet die Software Market Cap/FDV, Liquidität, Volumen, Käufe/Verkäufe und Kursdynamik. GoPlus wird für **unvollständige** Sicherheitsindikatoren abgefragt.

- **A-Radar:** 85 bis 100 Punkte; **B-Radar:** 70 bis 84 Punkte (heuristischer Score, **keine Gewinnwahrscheinlichkeit**).
- Maximal drei Alerts pro Scan und höchstens ein Alert pro Coin in 24 Stunden.
- Botbefehle: \`/start\`, \`/help\`, \`/status\`, \`/top\`. Antworten erfolgen **beim nächsten Scan**, nicht in Echtzeit.
- Keine automatischen Käufe, keine Wallet-Keys, keine ChatGPT-Work-Credits.

**Grenzen:** Keine direkten sekundenschnellen X-/Elon-Posts, kein Zugriff auf alle neuen Solana-Token, keine garantierte Erkennung jeder viralen Story, keine verlässliche Prognose von 10x-/100x-Chancen, keine Echtzeit-Honeypot-Garantie. Das Spektrum ist bewusst vorsichtig, daher können viele Coins durch die Filter fallen. Eine Erwähnung beweist keine offizielle Partnerschaft mit Rockstar, Elon Musk oder anderen Personen.

## Einrichtung auf dem iPhone — Schritt für Schritt

### 1. Zwei verschlüsselte GitHub-Secrets anlegen

Öffne **[Secrets and variables → Actions](https://github.com/albilura624/viral-alpha-radar/settings/secrets/actions)** in Safari (ggf. **Desktop-Website anfordern**).

Unter **Repository secrets** nacheinander **New repository secret** auswählen:

1. **Name:** \`TELEGRAM_BOT_TOKEN\` — **Secret:** dein *neuer* Token von @BotFather nach \`/revoke\`.
2. **Name:** \`TELEGRAM_CHAT_ID\` — **Secret:** die numerische Telegram-ID aus @userinfobot.

**Wichtig:** Weder Token noch Telegram-ID in \`bot.py\`, \`README.md\`, Issues, Kommentare oder öffentliche Dateien schreiben. Den Token niemals an ChatGPT schicken. Der alte, zuvor als Screenshot geteilte Token darf nicht verwendet werden.

### 2. Ersten Testlauf manuell starten

Sende deinem eigenen Telegram-Bot **/status**. Öffne dann **[Actions → Viral Alpha Radar](https://github.com/albilura624/viral-alpha-radar/actions/workflows/radar.yml)**, klicke **Run workflow**, wähle \`main\`, dann **Run workflow**.

Bei Erfolg erscheint ein grünes Häkchen. Dein Bot sollte beim Lauf auf \`/status\` antworten; falls keine passenden Coins gefunden wurden, ist **kein Markt-Alert** zu erwarten. Schau bei einem roten Kreuz in die Run-Logs. In Logs niemals Tokens abbilden oder öffentlich teilen.

### 3. Automatische Scans bewusst aktivieren

Öffne **[Actions-Variablen](https://github.com/albilura624/viral-alpha-radar/settings/variables/actions)** und erstelle unter **Repository variables**:

- **Name:** \`RADAR_ENABLED\`
- **Value:** \`true\`

Erst danach werden die geplanten Scans ungefähr alle 15 Minuten ausgeführt (GitHub Actions hat **keine Echtzeit- oder Zuverlässigkeitsgarantie**; Verspätungen oder Ausfälle sind möglich). Um den Bot später ohne Löschen zu pausieren, die Variable zu \`false\` ändern.

### 4. Push-Mitteilungen auf dem iPhone

In Telegram den Chat mit @ViralAlphaRadar_Bot öffnen und sicherstellen, dass er **nicht stummgeschaltet** ist. iPhone-Einstellungen → Mitteilungen → Telegram → Mitteilungen erlauben.

## Datenschutz und Sicherheit

Der Code liegt in einem **öffentlichen** Repository. Die GitHub-Secrets werden dem Workflow zur Laufzeit als Umgebungsvariablen gegeben und **nicht** mitgecommittet. Die Datei \`state.json\` enthält nur Zeitstempel, bereits gemeldete öffentliche Token-Adressen, zuletzt bewertete Coins und die Telegram-Update-Position (keine Keys).

GoPlus prüft nur einzelne öffentlich abrufbare Merkmale. Trotz fehlender Warnung sind Betrug, Washtrading, Holder-Konzentration, Dumping und Liquiditätsabzug möglich.

## Technische Hinweise

- Python 3.12, \`requests\`, Google News RSS, DEX Screener, GoPlus.
- \`bot.py\` ist nur für Alerts und Marktbeobachtung; du überträgst keine Gelder.
- GitHub Actions: \`.github/workflows/radar.yml\`, manuell oder mit \`RADAR_ENABLED=true\` ungefähr alle 15 Minuten.
- \`MIN_ALERT_SCORE\` aktuell 70. Ändere den Wert im Workflow, wenn du strengere Alerts möchtest.
- Test lokal: \`python -m unittest discover -s tests\`.
- Öffentliche GitHub-Actions-Läufe sind im üblichen GitHub-Free-Modell ohne kostenpflichtige Runner-Minuten nutzbar, können aber Limits unterliegen.

Weitere Angaben in der offiziellen GitHub- und Telegram-Dokumentation:
https://docs.github.com/en/actions
https://core.telegram.org/bots/api
