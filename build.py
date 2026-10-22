#!/usr/bin/env python3
"""Erzeugt die statischen Seiten aus src/<lang>/*.html. Aufruf: python3 build.py"""
import time
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "https://leotio.com"
VERSION = time.strftime("%Y%m%d%H%M")  # gegen Browser-Cache der CSS

# Seiten-Schlüssel -> (Pfad, Titel) je Sprache. EN liegt im Root, DE unter /de/.
PAGES = {
    "home":    {"en": ("",          "Leotio"),             "de": ("de/",              "Leotio")},
    "support": {"en": ("support/",  "Support – Leotio"),   "de": ("de/support/",      "Support – Leotio")},
    "privacy": {"en": ("privacy/",  "Privacy – Leotio"),   "de": ("de/datenschutz/",  "Datenschutz – Leotio")},
    "imprint": {"en": ("imprint/",  "Imprint – Leotio"),   "de": ("de/impressum/",    "Impressum – Leotio")},
    "dejawo-privacy": {"en": ("dejawo/privacy/",     "Déjà-where: Privacy Policy – Leotio"),
                       "de": ("de/dejawo/datenschutz/", "Déjà-wo: Datenschutzerklärung – Leotio")},
}
SRC = {"en": {"home": "home", "support": "support", "privacy": "privacy", "imprint": "imprint",
              "dejawo-privacy": "dejawo-privacy"},
       "de": {"home": "home", "support": "support", "privacy": "datenschutz", "imprint": "impressum",
              "dejawo-privacy": "dejawo-datenschutz"}}
LABELS = {"en": {"support": "Support", "privacy": "Privacy", "imprint": "Imprint"},
          "de": {"support": "Support", "privacy": "Datenschutz", "imprint": "Impressum"}}
DESC = {"en": "Leotio GmbH – from Old English lēoht: light.",
        "de": "Leotio GmbH – von altenglisch lēoht: leicht, licht."}


def rel(from_path: str, to_path: str) -> str:
    depth = from_path.count("/")
    return "../" * depth + to_path if (depth or to_path) else "./"


def render(key: str, lang: str) -> str:
    path, title = PAGES[key][lang]
    other = "de" if lang == "en" else "en"
    r = lambda p: rel(path, p)
    body = (ROOT / "src" / lang / f"{SRC[lang][key]}.html").read_text().rstrip("\n")
    header = "" if key == "home" else (
        f'  <header><div class="wrap"><a class="mark" href="{r(PAGES["home"][lang][0])}">'
        f'leotio<span class="dot">.</span></a></div></header>\n')
    nav = "".join(f'<a href="{r(PAGES[k][lang][0])}">{LABELS[lang][k]}</a>' for k in ("support", "privacy", "imprint"))
    href = {lang: r(PAGES[key][lang][0]), other: r(PAGES[key][other][0])}
    switch = '  <nav class="lang" aria-label="Language">' + "".join(
        f'<a href="{href[l]}" hreflang="{l}" lang="{l}"' + (' aria-current="true"' if l == lang else "") + f'>{l.upper()}</a>'
        for l in ("en", "de")) + "</nav>\n"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow"><!-- vor Go-live entfernen -->
  <title>{title}</title>
  <meta name="description" content="{DESC[lang]}">
  <link rel="alternate" hreflang="en" href="{SITE}/{PAGES[key]['en'][0]}">
  <link rel="alternate" hreflang="de" href="{SITE}/{PAGES[key]['de'][0]}">
  <link rel="alternate" hreflang="x-default" href="{SITE}/{PAGES[key]['en'][0]}">
  <link rel="preload" href="{r('assets/fonts/fraunces.woff2')}" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{r('assets/style.css')}?v={VERSION}">
  <link rel="icon" href="{r('assets/favicon.svg')}" type="image/svg+xml">
</head>
<body>
{switch}{header}  <main>
{body}
  </main>
  <footer>
    <div class="wrap">
      <span>© 2026 Leotio GmbH</span>
      <nav>{nav}</nav>
    </div>
  </footer>
</body>
</html>
"""


def main():
    for key in PAGES:
        for lang in ("en", "de"):
            out = ROOT / PAGES[key][lang][0] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(key, lang))
    (ROOT / "404.html").write_text(
        render("home", "en").replace(
            (ROOT / "src/en/home.html").read_text().rstrip("\n"),
            '    <div class="wrap page">\n      <h1>Page not found.</h1>\n'
            '      <p><a href="/">leotio.com</a> · <a href="/de/">Deutsch</a></p>\n    </div>')
        .replace('href="./', 'href="/').replace("<title>Leotio</title>", "<title>Not found – Leotio</title>")
        .replace('href="assets/', 'href="/assets/').replace('href="support/', 'href="/support/')
        .replace('href="privacy/', 'href="/privacy/').replace('href="imprint/', 'href="/imprint/')
        .replace('href="de/"', 'href="/de/"').replace('href="./"', 'href="/"'))


if __name__ == "__main__":
    main()
