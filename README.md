# leotio-website

Statische Website der Leotio GmbH (leotio.com), gehostet über GitHub Pages.

- Bewusst minimal: nur was Apple verlangt (Support-URL, Datenschutz-URL) plus Impressum.
- Zweisprachig: Englisch im Root (`/`, `/support/`, `/privacy/`, `/imprint/`), Deutsch unter `/de/` (`/de/support/`, `/de/datenschutz/`, `/de/impressum/`). leotio.de leitet per 301 auf `https://leotio.com/de/`.
- Inhalte in `src/en/` und `src/de/`, Seiten erzeugen mit `python3 build.py` (erzeugte HTML-Dateien werden mit eingecheckt).
- Schriften: Fraunces (Wortmarke, Überschriften) und Inter (Text), selbst gehostet, SIL OFL.
- **Noch nicht live.** Vor Go-live: Platzhalter im Impressum füllen, `noindex` in `build.py` entfernen, `CNAME` mit `leotio.com` anlegen, Pages aktivieren, DNS bei Strato setzen.
