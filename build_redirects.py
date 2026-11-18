"""Builds the short links from the one list, 02_brand/qgp_short_links.json.

  python3 build_redirects.py          writes public/_redirects and src/data/forward_links.json
  python3 build_redirects.py --check  prints what would change and writes nothing

Only rows with status "active" are written. A code is never removed once printed or posted.

Two kinds of link:
- an ordinary row becomes a line of public/_redirects (read by Netlify): the visitor is passed on at once;
- a row with "amazon_book" (a post about one book; Scott, 2026-11-17) becomes a small page at /<code>/, built by
  src/pages/[code].astro from src/data/forward_links.json. The page says where it leads and forwards the reader to
  the book's Amazon page. It is a page, not a redirect, because the hosting provider counts pages it serves and
  does not count redirects. The Amazon address comes from the ASIN in src/data/bible_series.json; a book with no
  ASIN yet opens Book 1, and the page says so.
"""
import json, sys
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
LINKS = HERE.parent.parent / "02_brand" / "qgp_short_links.json"
OUT = HERE / "public" / "_redirects"
SERIES = HERE / "src" / "data" / "bible_series.json"
FORWARD = HERE / "src" / "data" / "forward_links.json"

HEAD = ("# Quiet Grid Press short links. Built from 02_brand/qgp_short_links.json (Cowork). Do not edit by hand.\n"
        "# Format: /code  destination  status. 302 so a destination can change later; a code is never removed once printed.\n\n")
TAIL = "\n# Planned, not active (needs the Amazon Attribution tags): /amazon-... \n"


def build():
    data = json.loads(LINKS.read_text(encoding="utf-8"))
    status = data.get("redirect_status", 302)
    lines = []
    for row in data["links"]:
        if row.get("status") != "active" or row.get("amazon_book"):
            continue
        dest = row["destination"]
        if row.get("utm"):
            dest += ("&" if "?" in dest else "?") + urlencode(row["utm"])
        lines.append("/%s  %s  %s" % (row["code"], dest, status))
    codes = [l.split()[0] for l in lines]
    assert len(codes) == len(set(codes)), "a short code appears twice"
    return HEAD + "\n".join(lines) + "\n" + TAIL


def forward_links():
    """The single-book links, each with the Amazon page it opens today."""
    data = json.loads(LINKS.read_text(encoding="utf-8"))
    books = {b["number"]: b for b in json.loads(SERIES.read_text(encoding="utf-8"))}
    first = books[1]
    assert first.get("asin"), "Book 1 has no ASIN in bible_series.json"
    out = []
    for row in data["links"]:
        if row.get("status") != "active" or not row.get("amazon_book"):
            continue
        book = books[row["amazon_book"]]
        opens = book if book.get("asin") else first
        out.append({
            "code": row["code"],
            "book_number": book["number"],
            "book_title": book["title"],
            "opens_number": opens["number"],
            "opens_title": opens["title"],
            "opens_cover": opens["cover"],
            "amazon_url": "https://www.amazon.com/dp/" + opens["asin"],
            "stand_in": opens is not book,
        })
    codes = [r["code"] for r in out]
    assert len(codes) == len(set(codes)), "a forwarding code appears twice"
    return out


if __name__ == "__main__":
    fwd = json.dumps(forward_links(), indent=2, ensure_ascii=False) + "\n"
    old_fwd = FORWARD.read_text(encoding="utf-8") if FORWARD.exists() else ""
    if fwd != old_fwd:
        print("forwarding pages change: %d links" % len(json.loads(fwd)))
    if "--check" not in sys.argv:
        FORWARD.write_text(fwd, encoding="utf-8")
    new = build()
    old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    a, b = set(old.splitlines()), set(new.splitlines())
    for l in sorted(a - b):
        print("- " + l)
    for l in sorted(b - a):
        print("+ " + l)
    if "--check" in sys.argv:
        print("check only: nothing written")
    else:
        OUT.write_text(new, encoding="utf-8")
        print("wrote %s (%d links)" % (OUT, sum(1 for l in new.splitlines() if l.startswith("/"))))
