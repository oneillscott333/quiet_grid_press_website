#!/usr/bin/env python3
"""Build the website's blog data from the blog drafts.

Run from anywhere:  python3 build_blog.py

Reads (never changes):
  06_market/00_imprint/<campaign>/blog/text_blog_*.md           the words (the one home of the text)
  06_market/00_imprint/<campaign>/assets/blog/market_<c>_blog_<nn>_hero.png   the picture
  08_promo/schedule_holiday_2026.json                           the day each post goes on the website
  06_market/register_campaign_review.json                       Scott's verdicts

Writes (generated, never edited by hand):
  src/data/blog_posts.json        APPROVED posts only (committed)
  src/data/blog_drafts.json       the other posts, for the local preview only (git-ignored)
  public/images/blog/             the pictures of APPROVED posts only

A post is "approved" only when Scott has approved its words, its picture AND its date on the
campaign site, the picture file exists, the words have not changed since he approved them, the
date is still the one he approved, and every book the schedule says the post needs is on sale
("live_books" in the schedule). Everything else is "draft": shown in the local preview,
never in the public build. An approved post is still held back until its date: the blog pages
check the date on the day the site is built, so the morning rebuild puts a post up on its day.

For a test only, QGP_BLOG_REGISTER and QGP_BLOG_SCHEDULE may name a pretend register and schedule
(files inside the work zone); the drafts and pictures are always the real ones.
"""
import datetime
import hashlib
import html
import json
import os
import re
import shutil
from pathlib import Path

WEBSITE = Path(__file__).resolve().parent
ROOT = WEBSITE.parents[1]                      # 03_qgp_books
WORKZONE = ROOT.parent                         # 01_ai_workzone
MARKET = ROOT / "06_market" / "00_imprint"
REGISTER = ROOT / "06_market" / "register_campaign_review.json"
SCHEDULE = ROOT / "08_promo" / "schedule_holiday_2026.json"
OUT_JSON = WEBSITE / "src" / "data" / "blog_posts.json"
OUT_DRAFTS = WEBSITE / "src" / "data" / "blog_drafts.json"   # git-ignored: unapproved text never enters the repository
OUT_IMAGES = WEBSITE / "public" / "images" / "blog"
TRASH = WORKZONE / "01_workspace_tools" / ".ai_trash"


def fingerprint(text):
    """The same fingerprint the campaign review site uses."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    return text


def link(m):
    label, url = m.group(1), m.group(2)
    if url.startswith("/") or "quietgridpress.com" in url:
        return '<a href="%s">%s</a>' % (url, label)
    return '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (url, label)


def to_html(body):
    """The small part of Markdown the blog drafts use: paragraphs, a bold line as a
    heading, numbered and plain lists, quotations, bold, italic and links."""
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    lines = body.split("\n")
    blocks, cur = [], []
    for line in lines:
        if re.match(r"^# ", line):             # the title; the page prints it itself
            if cur:
                blocks.append(cur)
                cur = []
            continue
        if not line.strip():
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line.rstrip())
    if cur:
        blocks.append(cur)

    out, first_para = [], ""
    for b in blocks:
        one = b[0].strip()
        if len(b) == 1 and re.match(r"^\*\*[^*]+\*\*$", one):
            out.append("<h2>%s</h2>" % inline(one[2:-2]))
        elif len(b) == 1 and re.match(r"^#{2,3} ", one):
            out.append("<h2>%s</h2>" % inline(one.lstrip("#").strip()))
        elif all(re.match(r"^\s*\d+[.)] ", x) for x in b):
            out.append("<ol>%s</ol>" % "".join(
                "<li>%s</li>" % inline(re.sub(r"^\s*\d+[.)] ", "", x)) for x in b))
        elif all(re.match(r"^\s*[-+*] ", x) for x in b):
            out.append("<ul>%s</ul>" % "".join(
                "<li>%s</li>" % inline(re.sub(r"^\s*[-+*] ", "", x)) for x in b))
        elif all(x.lstrip().startswith(">") for x in b):
            out.append("<blockquote><p>%s</p></blockquote>" % inline(
                " ".join(re.sub(r"^\s*>\s?", "", x) for x in b)))
        else:
            text = " ".join(x.strip() for x in b)
            out.append("<p>%s</p>" % inline(text))
            if not first_para:
                first_para = re.sub(r"<[^>]+>", "", inline(text))
    return "\n".join(out), html.unescape(first_para)


def slugify(title):
    s = title.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def read_draft(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    fm, body = {}, raw
    if m:
        body = m.group(2).strip()
        for line in m.group(1).split("\n"):
            k, sep, v = line.partition(":")
            if sep:
                v = v.strip()
                if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
                    v = v[1:-1]
                fm[k.strip()] = v
    return fm, body


def real_day(value):
    try:
        datetime.date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def test_file(env, default):
    """The real file, or for a test the pretend one named in the environment (inside the work zone only)."""
    value = os.environ.get(env)
    if not value:
        return default
    path = Path(value).resolve()
    if WORKZONE not in path.parents:
        raise SystemExit("%s must name a file inside %s" % (env, WORKZONE))
    print("TEST: %s is read from %s" % (env, path))
    return path


def main():
    today = datetime.date.today()
    register, schedule = test_file("QGP_BLOG_REGISTER", REGISTER), test_file("QGP_BLOG_SCHEDULE", SCHEDULE)
    reg = json.loads(register.read_text(encoding="utf-8")) if register.exists() else {}
    sched = json.loads(schedule.read_text(encoding="utf-8")) if schedule.exists() else {}
    dates = {e["key"]: e.get("date", "") for e in sched.get("entries", []) if e.get("platform") == "blog"}
    needs = {e["key"]: e.get("needs", "") for e in sched.get("entries", []) if e.get("platform") == "blog"}
    live_books = set(sched.get("meta", {}).get("live_books", []))
    posts, notes = [], []

    for path in sorted(MARKET.glob("c*/blog/text_blog_*.md")):
        if "test" in path.name:
            continue
        fm, body = read_draft(path)
        m = re.match(r"^text_blog_(c\d+)_(\d+)_", path.name)
        if not m:
            notes.append("skipped (name not understood): %s" % path.name)
            continue
        camp, num = m.group(1), m.group(2)
        title = fm.get("title") or path.stem
        post_id = fm.get("id", path.stem)
        key = "%s_%s_blog" % (camp, re.sub(r"[^A-Za-z0-9]", "", post_id))
        rec = reg.get(key, {})
        text_v, pic_v, date_v = rec.get("text", {}), rec.get("picture", {}), rec.get("date", {})
        day = dates.get(key, "")

        hero_src = path.parent.parent / "assets" / "blog" / ("market_%s_blog_%s_hero.png" % (camp, num))
        hero = hero_src.name if hero_src.exists() else None

        waiting = []
        if text_v.get("verdict") != "approved":
            waiting.append("Scott's approval of the words")
        else:
            if text_v.get("hash"):
                if text_v["hash"] != fingerprint(body):
                    waiting.append("Scott's approval of the words again (they changed after he approved them)")
            else:
                # An approval recorded without a fingerprint: fall back to the file's own date.
                try:
                    when = datetime.datetime.strptime(text_v.get("when", ""), "%Y-%m-%d %H:%M")
                    changed = datetime.datetime.fromtimestamp(path.stat().st_mtime)
                    if changed > when + datetime.timedelta(minutes=1):
                        waiting.append("Scott's approval of the words again (the file changed after he approved them)")
                except ValueError:
                    waiting.append("Scott's approval of the words (no date on record)")
        if not hero:
            waiting.append("the picture (not made yet)")
        elif pic_v.get("verdict") != "approved":
            waiting.append("Scott's approval of the picture")
        if not real_day(day):
            waiting.append("a date on the schedule")
            day = ""
        elif date_v.get("verdict") != "approved":
            waiting.append("Scott's approval of the date")
        elif date_v.get("date") != day:
            waiting.append("Scott's approval of the date again (it was moved after he approved it)")
        # a post that names a book not yet on sale waits for that book, as a social post does
        if any(code not in live_books for code in re.findall(r"\b(00\d)\b", needs.get(key, ""))):
            waiting.append("a book to be on sale (needs %s)" % needs[key].rstrip("."))
        status = "draft" if waiting else "approved"

        body_html, first_para = to_html(body)

        alt = fm.get("hero_alt", "")
        alt_file = hero_src.with_suffix(".txt")
        if not alt and alt_file.exists():
            alt = alt_file.read_text(encoding="utf-8").strip()
        if not alt:
            alt = 'Picture for the post "%s".' % title

        if fm.get("open_items", "0") not in ("0", ""):
            notes.append("%s: the draft still lists %s open item(s)" % (post_id, fm["open_items"]))
        if text_v.get("wording"):
            notes.append("%s: Scott gave his own wording on the campaign site; check it is in the draft" % post_id)

        posts.append(dict(
            id=post_id, campaign=camp, slug=slugify(title), title=title,
            date=day, status=status, waiting=waiting,
            summary=first_para, body=body_html,
            hero=hero, hero_alt=alt,
            source=str(path.relative_to(ROOT)),
        ))

    slugs = [p["slug"] for p in posts]
    dupes = sorted({s for s in slugs if slugs.count(s) > 1})
    if dupes:
        raise SystemExit("Two posts would have the same address: %s" % ", ".join(dupes))

    posts.sort(key=lambda p: (p["date"] or "0000", p["id"]), reverse=True)     # newest first; no date last

    # Pictures: only an approved post's picture goes into the public folder.
    OUT_IMAGES.mkdir(parents=True, exist_ok=True)
    wanted = {}
    for p in posts:
        if p["status"] == "approved" and p["hero"]:
            src = ROOT / Path(p["source"]).parent.parent / "assets" / "blog" / p["hero"]
            wanted[p["hero"]] = src
    for name, src in wanted.items():
        dst = OUT_IMAGES / name
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copyfile(src, dst)
    for old in sorted(OUT_IMAGES.iterdir()):
        if old.is_file() and old.name not in wanted and not old.name.startswith("."):
            # Never delete: a picture that is no longer approved is moved to the AI trash.
            folder = TRASH / ("%s_qgp_website_blog_pictures" % today.isoformat())
            folder.mkdir(parents=True, exist_ok=True)
            target, n = folder / old.name, 1
            while target.exists():
                target = folder / ("%s_%d%s" % (old.stem, n, old.suffix))
                n += 1
            shutil.move(str(old), str(target))
            notes.append("moved a picture that is no longer approved to %s" % target.relative_to(WORKZONE))

    head = dict(built=today.isoformat())
    approved_posts = [p for p in posts if p["status"] == "approved"]
    draft_posts = [p for p in posts if p["status"] != "approved"]
    OUT_JSON.write_text(json.dumps(dict(
        _about="Generated by build_blog.py from the blog drafts in 06_market. Never edit by hand. "
               "Holds APPROVED posts only, so unapproved text is not in the repository. A post is public only "
               "when its date has come. The local preview reads the other posts from blog_drafts.json.",
        **head, posts=approved_posts), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_DRAFTS.write_text(json.dumps(dict(
        _about="Generated by build_blog.py. Git-ignored. Unapproved posts, shown only in the local preview. Never commit.",
        **head, posts=draft_posts), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Blog posts: %d (%d approved, %d draft)" % (
        len(posts), sum(p["status"] == "approved" for p in posts), sum(p["status"] == "draft" for p in posts)))
    for p in posts:
        print("  %-9s %-8s %-10s picture: %-3s /blog/%s/" % (p["id"], p["status"], p["date"] or "no date",
                                                          "yes" if p["hero"] else "no", p["slug"]))
        for w in p["waiting"]:
            print("            waits for: " + w)
    for n in notes:
        print("  note: " + n)
    print("Wrote %s" % OUT_JSON.relative_to(ROOT))


if __name__ == "__main__":
    main()
