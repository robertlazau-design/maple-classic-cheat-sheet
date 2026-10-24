#!/usr/bin/env python3
"""Builds the Maple Classic Guide into ./public as plain static HTML.
Edit the JSON in ./data, run `python3 build.py`, commit, and Vercel serves ./public.
No dependencies."""
import json, os, re, shutil, html, urllib.parse, hashlib
from datetime import date, datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "public")
SITE = "https://www.mapleclassicguide.com"
NAME = "Maple Classic Guide"
COFFEE = "https://buymeacoffee.com/goldenboypro"  # your Buy Me a Coffee link, e.g. "https://buymeacoffee.com/yourname". Empty = hidden.
CHECKED = "Oct 21, 2026"
CHECKED_ISO = "2026-10-21"
DATA_NOTE = "Grand Launch notes and Founder's Access data"
WEB3FORMS_KEY = os.environ.get("WEB3FORMS_KEY", "").strip()  # set in Vercel > Settings > Environment Variables; empty = feedback opens an email instead

def load(n):
    with open(os.path.join(ROOT, "data", n)) as f:
        return json.load(f)

JOBS = load("jobs.json"); TIERS = load("tiers.json"); EXP = load("exp.json"); UPDATES = load("updates.json"); CRAFT = load("crafting.json"); LEV = load("leveling.json"); SEC = load("secrets.json"); IMG = load("images.json"); DIR = load("directions.json"); PRICES = load("prices.json")
API = "https://maplestory.io/api/GMS/83"

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)

SHORTHAND = {"MG": "Magic Guard", "IMR": "Improved MP Recovery", "MMI": "Max MP Increase", "MA": "Magic Armor", "EB": "Energy Bolt",
             "PB": "Poison Breath", "PS": "Power Strike", "SB": "Slash Blast", "IHR": "Improved HP Recovery", "MHI": "Max HP Increase",
             "PKB": "Power Knockback", "FA": "Final Attack"}
GLOSSARY = {"STR": "Strength", "DEX": "Dexterity", "INT": "Intelligence", "LUK": "Luck", "AP": "Ability Points: 5 per level, put into stats",
            "SP": "Skill Points, put into skills", "HP": "Health", "MP": "Mana", "ACC": "Accuracy", "ATK": "Attack",
            "WDEF": "Weapon Defense", "EHP": "Effective HP (how much damage you can take)", "NX": "Nexon cash currency", "EXP": "Experience",
            "AoE": "Hits several monsters at once", "Lv": "Level", "PQ": "Party quest", "KPQ": "Kerning City Party Quest", "FM": "Free Market",
            "F/P": "Fire/Poison Wizard", "I/L": "Ice/Lightning Wizard", "NPC": "A character you talk to: shops, quests and job advancement",
            "UTC": "World time. US Pacific is 7 hours behind (8 hours from Nov 1)", "PDT": "US Pacific time", "mesos": "MapleStory's money",
            "respawn": "How long until it shows up again"}
_GLOSS_RE = re.compile(r"\b(" + "|".join(sorted(GLOSSARY, key=len, reverse=True)) + r")(?=\b|\d)")

def gloss(html_text):
    """Wrap game shorthand in <abbr> so a tap or hover explains it. Skips scripts and tag attributes."""
    parts = re.split(r"(<script.*?</script>|<[^>]+>)", html_text, flags=re.S)
    seen = set()
    for i, part in enumerate(parts):
        if part.startswith("<h2"):
            seen.clear()  # explain each term once per section, so a tap is never far away
        if not part or part.startswith("<"):
            continue
        def sub(m):
            k = m.group(1)
            if k in seen: return k
            seen.add(k)
            return f'<abbr title="{GLOSSARY[k]}">{k}</abbr>'
        parts[i] = _GLOSS_RE.sub(sub, part)
    return "".join(parts)

def tidy(s):
    """Small copy fixes on research text before it reaches readers."""
    s = str(s)
    s = s.replace(" Don't promise readers a route to 100.", "")
    s = re.sub(r"\(inference(, verify)?\)", "(our estimate)", s)
    s = s.replace("(MeowDB)", "").replace("  ", " ")
    for short, full in SHORTHAND.items():
        s = re.sub(r"\b" + short + r"\b", full, s)
    return s.strip()

def conf(c):
    c = (c or "medium").lower()
    label = {"high": "Confirmed", "medium": "Likely", "low": "Unconfirmed"}.get(c, c)
    why = {"high": "Several Classic sources agree.", "medium": "One Classic source, or partly our estimate. Could still change.",
           "low": "Not verified yet, or not in the game yet."}.get(c, "How sure we are")
    return f'<span class="chip c-{e(c)}" title="{why}">{label}</span>'

SOURCE_NAMES = {"meowdb.com": "NiaMeowDB", "metaroad.gg": "Metaroad", "mapleclassic.wiki": "Classic Wiki", "maplestorywiki.net": "MapleStory Wiki",
                "maplestory.quest": "maplestory.quest", "maplestoryguide.wiki": "maplestoryguide.wiki"}

def srcs(s):
    if not s: return ""
    items = s if isinstance(s, list) else [x.strip() for x in str(s).split(";")]
    groups = {}
    for u in items:
        u = u.strip()
        if not u.startswith("http"): continue
        host = re.sub(r"^https?://(www\.)?", "", u).split("/")[0]
        groups.setdefault(SOURCE_NAMES.get(host, host), []).append(u)
    if not groups: return ""
    out = []
    for name, urls in groups.items():
        if len(urls) == 1:
            out.append(f'<a href="{e(urls[0])}" rel="nofollow noopener" target="_blank">{e(name)}</a>')
        else:
            nums = " · ".join(f'<a href="{e(u)}" rel="nofollow noopener" target="_blank">{i + 1}</a>' for i, u in enumerate(urls))
            out.append(f"{e(name)} ({nums})")
    return f'<p class="src">Source{"s" if sum(map(len, groups.values())) > 1 else ""}: {", ".join(out)}</p>'

def _img(src, alt, cls):
    return f'<img class="{cls}" src="{src}" alt="{e(alt)}" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.remove()">'
FLYERS = {2300100, 5300100}  # Stirge, Malady: no "stand" pose, only "fly"
def mob_src(i):
    return f"{API}/mob/{i}/render/{'fly' if i in FLYERS else 'stand'}"
def mob_img(name, cls="sprite"):
    i = IMG["mobs"].get(name)
    return _img(mob_src(i), name, cls) if i else ""
def npc_img(i, name, cls="sprite"):
    return _img(f"{API}/npc/{i}/render/stand", name, cls)
def map_img(i, name):
    return f'<figure class="mini">{_img(f"{API}/map/{i}/minimap", name + " minimap", "mm")}<figcaption>{e(name)}</figcaption></figure>'
def mobs_in(text, n=3):
    found = []
    for name in sorted(IMG["mobs"], key=len, reverse=True):
        if re.search(r"(?<![A-Za-z.])" + re.escape(name) + r"(?![a-z])", text) and not any(name in f for f in found):
            found.append(name)
    order = sorted(found, key=lambda m: text.find(m))
    return order[:n]
def secret_img(name):
    for k, v in IMG["secrets"].items():
        if name.startswith(k) or k in name:
            parts = []
            if v.get("mob"): parts.append(mob_img(v["mob"]))
            if v.get("npc"): parts.append(npc_img(v["npc"][0], v["npc"][1]))
            fig = map_img(v["map"], name.split(" (")[0]) if v.get("map") else ""
            return f'<div class="pics">{fig}<div class="sprites">{"".join(parts)}</div></div>'
    return ""

LEAF = '<svg viewBox="0 0 32 32" aria-hidden="true"><path fill="var(--maple)" d="M16 2l2.6 5.4 4.2-2-1 5.6 5.2-1.6-2.6 4.6 4.6 1.6-6 3.6 1.4 3.2-6.2-1.2.4 6.8h-5.2l.4-6.8-6.2 1.2 1.4-3.2-6-3.6 4.6-1.6L5 9.4l5.2 1.6-1-5.6 4.2 2z"/><path stroke="var(--ink)" stroke-width="1.6" d="M16 12v18" fill="none"/></svg>'

LEAVES = '<div class="leaves" aria-hidden="true">' + "".join(
    f'<i style="right:{r}%;top:{t}px;--s:{sz}px;--rot:{rot}deg"></i>' for r, t, sz, rot in
    [(4, 70, 54, -20), (14, 150, 40, 25), (25, 60, 34, 10), (9, 290, 62, -35), (22, 250, 44, 40), (33, 360, 36, -10), (3, 470, 48, 15), (18, 520, 38, -25), (30, 180, 30, 55)]) + "</div>"
HOUSE = '<svg class="house" viewBox="0 0 120 110" aria-hidden="true"><path fill="currentColor" d="M60 4C28 4 6 24 6 46c0 6 4 9 10 9h88c6 0 10-3 10-9C114 24 92 4 60 4z"/><rect x="26" y="55" width="68" height="48" rx="10" fill="currentColor"/><rect x="50" y="70" width="20" height="33" rx="10" fill="#fff" opacity=".5"/></svg>'
LEAF_SM = '<svg viewBox="0 0 32 32" aria-hidden="true"><path fill="currentColor" d="M16 2l2.6 5.4 4.2-2-1 5.6 5.2-1.6-2.6 4.6 4.6 1.6-6 3.6 1.4 3.2-6.2-1.2.4 6.8h-5.2l.4-6.8-6.2 1.2 1.4-3.2-6-3.6 4.6-1.6L5 9.4l5.2 1.6-1-5.6 4.2 2z"/></svg>'

NAV = [("/", "Home"), ("/news/", "News"), ("/events/", "Events"), ("/leveling/", "Grind spots"), ("/jobs/", "Builds"), ("/tier-list/", "Tier list"), ("/bosses/", "Bosses"), ("/party-quest/", "KPQ"), ("/quests/", "Quests"), ("/citizenship/", "Citizenship"), ("/money-making/", "Mesos"), ("/prices/", "Price check"), ("/free-market/", "Market"), ("/crafting/", "Crafting"), ("/tools/", "Tools"), ("/job-advancement/", "Job up"), ("/secrets/", "Secrets"), ("/classic-rules/", "Rules")]

MORE_EMOJI = {"/news/": "📰", "/events/": "🎃", "/citizenship/": "🏠", "/free-market/": "🏪", "/leveling/": "🗺️", "/jobs/": "⚔️", "/tier-list/": "🏆", "/bosses/": "👑", "/party-quest/": "🎟️", "/quests/": "📜", "/money-making/": "💰", "/prices/": "🔎",
              "/crafting/": "⚒️", "/tools/": "🧮", "/job-advancement/": "⬆️", "/secrets/": "🤫", "/classic-rules/": "📏"}

# Top bar: five menus instead of 17 links. Every page in NAV should appear in exactly one group.
NAV_GROUPS = [
    ("News", [("/news/", "News", "Launch day, patch notes, deadlines"), ("/events/", "Events", "Mark of the Beta, Halloween, daily gifts"), ("/updates/", "What's new", "Changes to this guide")]),
    ("Leveling", [("/leveling/", "Grind spots", "Where to train at every level"), ("/quests/", "Quests", "Best quests by level"), ("/party-quest/", "KPQ", "Party quest: every answer and combo"), ("/bosses/", "Bosses", "Respawn timers and drops")]),
    ("Classes", [("/jobs/", "Builds", "AP and SP for all 10 jobs"), ("/tier-list/", "Tier list", "Best class for how you play"), ("/job-advancement/", "Job up", "1st and 2nd job tests")]),
    ("Mesos", [("/prices/", "Price check", "What it's worth + this week's farms"), ("/money-making/", "Mesos", "What sells and what to keep"), ("/free-market/", "Market", "Shops, prices and scams"), ("/crafting/", "Crafting", "What each profession needs"), ("/citizenship/", "Citizenship", "Grades, perks and housing")]),
    ("More", [("/tools/", "Tools", "EXP calculator, scroll simulator"), ("/secrets/", "Secrets", "Hidden maps and jump quests"), ("/classic-rules/", "Rules", "How Classic works")]),
]

def nav_html(cur):
    out = ""
    for label, items in NAV_GROUPS:
        here = any(h == cur for h, _, _ in items)
        links = "".join(f'<a href="{h}"{" aria-current=page" if h == cur else ""}><span class="dd-e" aria-hidden="true">{MORE_EMOJI.get(h, "✨")}</span><span><b>{e(t)}</b><small>{e(d)}</small></span></a>' for h, t, d in items)
        out += f'<details class="dd"{" data-here" if here else ""}><summary>{label}</summary><div class="dd-menu">{links}</div></details>'
    return out

LAUNCHED = "2026-10-19"  # first commit and first updates.json entry
PUBLISHER = {"@type": "Organization", "name": NAME, "url": SITE + "/"}

def page(path, title, desc, body, crumbs=None, schema=None, side_extra="", hero=""):
    canon = SITE + path
    sect = "/jobs/" if path.startswith("/jobs/") else "/quests/" if path.startswith("/quests/") else path
    nav = nav_html(sect)
    bc = ""
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "alternateName": "MapleStory Classic Guide", "url": SITE + "/", "inLanguage": "en", "publisher": PUBLISHER},
          {"@context": "https://schema.org", **PUBLISHER, "logo": f"{SITE}/icon-512.png", "description": "A free, no-ads fan guide to MapleStory Classic World."}] if path == "/" else []
    if crumbs:
        bc = '<nav class="crumbs" aria-label="Breadcrumb">' + " › ".join(f'<a href="{h}">{e(t)}</a>' if h else e(t) for h, t in crumbs) + "</nav>"
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": t, **({"item": SITE + h} if h else {})} for i, (h, t) in enumerate(crumbs)]})
    if schema and schema.get("@type") == "Article":
        schema = {**schema, "description": desc, "image": f"{SITE}/og.png", "datePublished": LAUNCHED, "dateModified": "__DATEMOD__",
                  "author": PUBLISHER, "publisher": PUBLISHER, "mainEntityOfPage": canon, "inLanguage": "en"}
    if schema: ld.append(schema)
    tabs = [("/", "M3.5 11 12 4l8.5 7v8.5a1 1 0 0 1-1 1H15v-6H9v6H4.5a1 1 0 0 1-1-1z", "Home"),
            ("/leveling/", "M9 4.5 3.5 6.5v13l5.5-2 6 2 5.5-2v-13l-5.5 2zM9 4.5v13M15 6.5v13", "Grind"),
            ("/jobs/", "M14.5 3.5h6v6L10 20l-6-6zM7 11l6 6M3.5 20.5l3-3", "Builds"),
            ("/tier-list/", "M8 3.5h8V9a4 4 0 0 1-8 0zM8 5.5H5a3 3 0 0 0 3 4.5M16 5.5h3a3 3 0 0 1-3 4.5M12 13v4M8.5 20.5h7M10 17h4", "Tiers"),
            ("/events/", "M4.5 6.5h15v13h-15zM4.5 10.5h15M8.5 4v4M15.5 4v4M8 14h2M14 14h2M8 17h2", "Events")]
    cur = sect
    tabbar = "".join(f'<a href="{h}"{" aria-current=page" if h == cur else ""}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="{d}"/></svg>{t}</a>' for h, d, t in tabs)
    in_more = cur not in [h for h, _, _ in tabs]
    tabbar += f'<button type="button" class="tb-more" data-more aria-expanded="false" aria-controls="more-sheet"{" aria-current=page" if in_more else ""}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4.5 4.5h6v6h-6zM13.5 4.5h6v6h-6zM4.5 13.5h6v6h-6zM13.5 13.5h6v6h-6z"/></svg>More</button>'
    more = "".join(f'<p class="more-sec">{label}</p><nav class="more-grid">' + "".join(f'<a href="{h}"{" aria-current=page" if h == cur else ""}><span aria-hidden="true">{MORE_EMOJI.get(h, "✨")}</span>{t}</a>' for h, t, _ in items) + "</nav>" for label, items in NAV_GROUPS)

    ldtxt = "".join(f'<script type="application/ld+json">{json.dumps(x)}</script>' for x in ld)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="max-image-preview:large">
<meta property="og:type" content="{"article" if schema and schema.get("@type") == "Article" else "website"}"><meta property="og:site_name" content="{NAME}"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE}/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Maple Classic Guide: MapleStory Classic builds, leveling and secrets">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#120a05">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" href="/favicon-48.png" sizes="48x48" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/fonts/nunito-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/style.css">
<script defer src="/_vercel/insights/script.js"></script>
{ldtxt}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="frame">{LEAVES}
<header class="site-h"><div class="wrap">
<a class="brand" href="/">{LEAF}<span>Maple Classic <span>Guide</span></span></a>
<nav class="nav" aria-label="Main">{nav}</nav>
<button class="search-btn" type="button" data-search aria-label="Search the guide"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M16.5 16.5L21 21" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg><span>Search</span><kbd>/</kbd></button>
</div></header>
{hero}
<div class="wrap">
<div class="layout{" has-side" if side_extra else ""}">
<main id="main"{"" if path in NO_INDEX else " data-pagefind-body"}>{_pf_skip(bc)}{gloss(body)}{_pf_skip(tipjar(path))}{_pf_skip(feedback(path))}</main>
<aside class="side" aria-label="Sidebar"><div class="sticky">{side_extra}</div></aside>
</div></div>
<footer class="site-f"><div class="wrap">
<a class="brand" href="/">{LEAF}<span>Maple Classic <span>Guide</span></span></a>
<nav aria-label="Footer">{"".join(f'<a href="{h}">{t}</a>' for h, t in NAV)}<a href="/updates/">What's new</a><a href="/about/">About &amp; sources</a><a href="/privacy/">Privacy</a></nav>
{coffee_btn()}<p>Unofficial fan site. Not affiliated with or endorsed by NEXON. MapleStory © NEXON. Data checked {CHECKED} ({DATA_NOTE}); we re-check after every patch. <a href="mailto:robertlazau@gmail.com?subject=Maple%20Classic%20Guide%20fix">Spotted a mistake? Tell us</a>.</p>
<p>Game sprites and minimaps © Nexon, loaded from <a href="https://maplestory.io" rel="nofollow noopener">maplestory.io</a>. Built by <a href="https://www.robertlazau.com">Golden Boy Productions</a>.</p>
</div></footer>
</div>
<nav class="tabbar" aria-label="Quick nav">{tabbar}</nav>
<div class="more-sheet" id="more-sheet" hidden><div class="more-box" tabindex="-1" role="dialog" aria-modal="true" aria-label="All guides"><p class="more-h"><b>All guides</b><button type="button" class="search-x" data-more-close aria-label="Close menu">Close</button></p>{more}</div></div>
<div class="search" id="search" hidden><div class="search-box" role="dialog" aria-modal="true" aria-label="Search">
<input id="q" type="search" placeholder="Try: assassin, mushmom, level 35, scrolls" autocomplete="off" aria-label="Search the guide"><button type="button" class="search-x" data-close aria-label="Close search">Esc</button>
<ul id="hits" role="listbox"></ul></div></div>
<script src="/site.js" defer></script>
</body>
</html>"""

def coffee_btn(big=False):
    if not COFFEE: return ""
    return f'<a class="coffee{" big" if big else ""}" href="{COFFEE}" target="_blank" rel="noopener">☕ Buy me a coffee</a>'

def _pf_skip(s):
    """Keep a block out of the full-text search index."""
    return re.sub(r"^<(\w+)", r"<\1 data-pagefind-ignore", s, count=1) if s else s

NO_INDEX = {"/404", "/privacy/"}

def stamp():
    return f'<p class="stamp" data-pagefind-ignore><b>✓ Checked {CHECKED}</b><span>{DATA_NOTE}. Tags show how sure we are: {conf("high")} {conf("medium")} {conf("low")}</span></p>'

def job_title(name):
    """People search "cleric stats" and "warrior skill guide", not "AP & SP"."""
    t = f"{name} Build Guide: MapleStory Classic Stats & Skills"
    return t if len(t) <= 60 else f"{name} Build: MapleStory Classic Stats & Skills"

LASTMOD_FILE = os.path.join(ROOT, "data", "lastmod.json")
LASTMOD = json.load(open(LASTMOD_FILE)) if os.path.exists(LASTMOD_FILE) else {}
LASTMOD_SEEN = {}
try:
    TODAY = datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
except Exception:  # no time zone data on the build machine
    TODAY = date.today().isoformat()

def page_date(path, text):
    """Date this page last changed, judged by a hash of its <main> content."""
    m = re.search(r"<main\b.*?</main>", text, re.S)
    main = re.sub(r'data-fb-key="[^"]*"', "", m.group(0) if m else text)  # the form key differs between local and Vercel builds
    h = hashlib.sha256(main.encode()).hexdigest()[:16]
    old = LASTMOD.get(path)
    d = old["d"] if old and old["h"] == h else TODAY
    LASTMOD_SEEN[path] = {"h": h, "d": d}
    return d

def write(path, text):
    text = text.replace("__DATEMOD__", page_date(path, text))
    d = os.path.join(OUT, path.strip("/"))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w") as f:
        f.write(text)

ALLJOBS = [(c, j) for c in JOBS["classes"] for j in c["jobs"]]

PATHFINDER = "https://meowdb.com/msclassic/pathfinder"

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]

def _squash(stops):
    """Ant Tunnel I, Ant Tunnel II, Ant Tunnel III -> Ant Tunnel I–III, so long walks stay readable."""
    out = []
    for x in stops:
        base, _, num = x.rpartition(" ")
        if out and num in ROMAN and out[-1][2] is not None and out[-1][0] == base and ROMAN.index(num) == out[-1][2] + 1:
            out[-1][2] = ROMAN.index(num)
        else:
            out.append([base, num, ROMAN.index(num)] if (base and num in ROMAN) else [x, None, None])
    return [b if n is None else (f"{b} {n}" if ROMAN.index(n) == hi else f"{b} {n}–{ROMAN[hi]}") for b, n, hi in out]

def go_html(name, lead="", tip=True):
    """Map-by-map walk from the nearest town (checked with NiaMeowDB's Pathfinder), plus a link to see each step on a minimap."""
    d = DIR["maps"].get(name)
    if not d: return ""
    stops = [d["from"]] + d["via"] + [name]
    hops = len(stops) - 1
    show = [stops[0]] + _squash(stops[1:-1]) + [name]
    arrow = '<span class="go-a" aria-hidden="true">›</span>'
    path = arrow.join(f'<span class="go-s{" town" if i == 0 else ""}{" dest" if i == len(show) - 1 else ""}">{e(x)}</span>' for i, x in enumerate(show))
    f, t = d["pf"].split("-")
    walk = "It's right outside town." if hops == 1 else f"{hops} maps from town."
    tip = f' <span class="go-tip">{e(d["tip"])}</span>' if tip and d.get("tip") else ""
    return f'''<div class="go"><p class="go-h">🧭 {lead}Start in <b>{e(d["from"])}</b>. {walk}{tip}</p><p class="go-path">{path}</p><a class="go-link" href="{PATHFINDER}?from={f}&amp;to={t}" target="_blank" rel="noopener">See every step on a minimap (NiaMeowDB) ↗</a></div>'''

def route_go(text, n=2):
    """Directions for the first n maps named in a route entry that we have a walk for."""
    names = {k: k for k in DIR["maps"]}; names.update(DIR["alias"])
    hits = sorted((text.find(k), -len(k), k) for k in names if k in text)
    taken, out = [], []
    for pos, neg, k in hits:
        span = (pos, pos - neg)
        if any(a <= span[0] and span[1] <= b for a, b in taken): continue  # inside a longer name we already used
        dest = names[k]
        if dest in out: continue
        taken.append(span); out.append(dest)
    seen, html = set(), []
    for i, k in enumerate(out[:n]):
        t = DIR["maps"][k].get("tip")
        html.append(go_html(k, "" if i == 0 else "Or: ", t not in seen))
        seen.add(t)
    return "".join(html)

def route_li(r):
    cls = "future" if "Nov 18" in r["map"] or "from Nov" in r["map"] else ("wall" if r["from"] >= 80 else "")
    lv = f'{r["from"]}–{r["to"]}'
    best = ", ".join(r.get("bestFor") or [])
    sprites = "".join(mob_img(m) for m in mobs_in(r.get("monsters", "")))
    mm = next((v for k, v in IMG["routeMaps"].items() if k in r["map"]), None)
    pics = f'<div class="pics">{map_img(mm, tidy(r["map"]).split(" / ")[0].split(" (")[0]) if mm else ""}<div class="sprites">{sprites}</div></div>' if (sprites or mm) else ""
    go = route_go(r["map"])
    return f'''<li class="{cls}" id="lv-{r["from"]}-{r["to"]}" data-from="{r["from"]}" data-to="{r["to"]}"{" data-all" if "all" in (r.get("bestFor") or []) else ""}><span class="lv">Lv {lv}</span>{pics}
<span class="map">{e(tidy(r["map"]))} {conf(r.get("confidence"))}</span>
<span class="sub">{e(r.get("region",""))} · {e(r.get("monsters",""))} (lv {e(r.get("monsterLevel",""))}){" · best for " + e(best) if best and best != "all" else ""}</span>
<span class="tip">{e(tidy(r.get("tip","")))}</span>{go}</li>'''

def build_home():
    route = sorted([r for r in LEV["route"]], key=lambda r: ("Nov 18" in r["map"], r["from"], r["to"]))
    fdata = {"route": [{"from": r["from"], "to": r["to"], "map": tidy(r["map"]), "monsters": r.get("monsters", ""), "monsterLevel": r.get("monsterLevel", ""), "confidence": r.get("confidence", "medium"),
                        "region": r.get("region", "").replace("Victoria Island - ", ""), "mm": next((v for k, v in IMG["routeMaps"].items() if k in r["map"]), None),
                        "opens": "2026-11-18T16:00:00Z" if "Nov 18" in r["map"] else None,
                        "sprites": [IMG["mobs"][m] for m in mobs_in(r.get("monsters", ""), 2)]} for r in route],
             "gloss": {k: GLOSSARY[k] for k in ("AP", "SP", "STR", "DEX", "INT", "LUK", "HP", "MP")},
             "classes": [{"id": c["id"], "name": c["name"], "npc": c["firstJob"]["npc"], "town": c["firstJob"]["town"], "sprite": IMG["classNpc"][c["id"]][0],
                          "jobs": [j["id"] for j in c["jobs"]], "start": JOBS["creation"]["classes"][c["id"]]["stats"]} for c in JOBS["classes"]],
             "jobs": {j["id"]: {"name": j["name"], "cls": c["id"], "weapon": j["weapon"], "play": tidy(j["playstyle"]), "adv": {"test": tidy(j["advancement"]["test"])},
                                 "apSummary": tidy(j["ap"]["summary"]), "ap": [tidy(x) for x in j["ap"]["steps"]], "sp1": [tidy(x) for x in j["sp"]["firstJob"]], "sp2": [tidy(x) for x in j["sp"]["secondJob"]]} for c, j in ALLJOBS},
             "api": API}
    cards = [("/leveling/", "🗺️ Grind spots", "Where to train at every level, 1 to 100.", "mob/1210103"),
             ("/jobs/", "⚔️ Builds", "AP + SP for all 10 jobs. Resets cost 7,000 NX, so don't wing it.", "npc/1012100"),
             ("/tier-list/", "🏆 Tier list", "Best class for grinding, bossing, parties or your first run.", "npc/1022000"),
             ("/crafting/", "⚒️ Crafting", "What to keep for each profession, and where it drops. Stop vendoring Iron Ore.", "npc/1022003"),
             ("/bosses/", "👑 Bosses", "Every boss, its respawn timer and what it drops. Mano to Jr. Balrog.", "mob/6130101"),
             ("/party-quest/", "🎟️ KPQ", "Kerning PQ answers and every combo, so your party never stalls.", "npc/9020000"),
             ("/quests/", "📜 Quests", "The quests worth doing at every level, and the ones to skip.", "npc/1012101"),
             ("/prices/", "🔎 Price check", "What's it worth? One tap to live prices, plus this week's best money farms.", "npc/9030000"),
             ("/money-making/", "💰 Mesos", "What sells, what to keep and the quests that pay the most.", "npc/1052102"),
             ("/news/", "📰 News", "Launch day, events, patch notes and deadlines, in one place.", "npc/9010000"),
             ("/events/", "🎃 Events", "Mark of the Beta walkthrough, daily gifts and the Halloween candy hunt.", "npc/9201028"),
             ("/citizenship/", "🏠 Citizenship", "Henesys or Kerning? Every grade, the donation items and how to get a house.", "npc/1012113"),
             ("/free-market/", "🏪 Market", "Sell fast, price right and dodge the classic trade scams.", "npc/9030000"),
             ("/tools/", "🧮 Tools", "EXP calculator and a scroll simulator. Gamble without losing mesos.", "npc/9000008"),
             ("/job-advancement/", "⬆️ Job up", "Who to talk to at 10 and 30, and how the marble test works.", "npc/1032001"),
             ("/secrets/", "🤫 Secrets", f'{len(SEC["secrets"])} hidden maps, jump quests and boss rooms.', "mob/1210101"),
             ("/classic-rules/", "📜 Rules", "Scroll odds, the EXP wall, crafting and making mesos.", "mob/1110100")]
    musts = ["Finish every Maple Island quest before you take the boat. It's one-way.",
             "Taxi to your job town while you're still a Beginner. It's 90% off.",
             "Plan your AP and SP. Fixing a mistake costs 7,000 NX.",
             "Carry a Return Scroll. There's no cab back out of the Ant Tunnel.",
             "Buy Orange Potions or Lemons for MP, not Blue Potions. Better value."]
    cast = [("mob", 210100, "mob", 10, 20, 2.4, .4), ("mob", 1210102, "mob", 38, 10, 2.3, .9), ("mob", 100101, "mob", 70, 24, 2.8, 1.3),
            ("npc", 1022000, "npc", 2, 58, 1.9, 0), ("npc", 1032001, "npc", 27, 50, 1.6, .6), ("npc", 1012100, "npc", 49, 58, 1.9, 1.1), ("npc", 1072003, "npc", 72, 56, 2.0, 1.6)]
    castimg = "".join(f'<img src="{API}/{kind}/{i}/render/stand" alt="" loading="eager" referrerpolicy="no-referrer" onerror="this.remove()" style="left:{left}%;top:{top}%;--k:{k};--d:{d}s">' for _, i, kind, left, top, k, d in cast)
    hero = f'''<section class="hero"><div class="wrap">
<div class="hero-copy">{HOUSE}<p class="kicker" data-launch>Classic World · launches Oct 21</p><h1>MapleStory Classic<br>Guide</h1>
<p class="sub">Pick your class. Get your build, your grind spot and the secrets. That's it.</p>
<div class="btns"><a class="btn btn-primary" href="#run">Start here {LEAF_SM}</a><button class="btn btn-ghost" type="button" data-search>Search anything</button></div>
{stamp()}</div>
<div class="cast" aria-hidden="true">{castimg}</div>
</div></section>'''
    classes = "".join(f'<button type="button" class="cls" data-cls="{e(c["id"])}" aria-pressed="false"><img src="{API}/npc/{IMG["classNpc"][c["id"]][0]}/render/stand" alt="" referrerpolicy="no-referrer" onerror="this.remove()"><b>{e(c["name"])}</b></button>' for c in JOBS["classes"])
    body = f'''<a class="newsbar" href="/news/"><span class="nb-dot" aria-hidden="true"></span><b data-launch-news>Grand Launch: Wed Oct 21, 11 AM PDT</b><span>Events, patch notes and launch-day tips →</span></a>
{deadline_bar()}
<section class="run" id="run" aria-labelledby="runh">
<h2 id="runh">Your run</h2>
<p class="step"><span>1</span>Pick your class</p><div class="classes" role="group" aria-label="Class">{classes}</div>
<p class="step"><span>2</span>Pick your job</p><div class="jobs" id="jobchips" role="group" aria-label="Job"></div>
<p class="step"><span>3</span>Your level</p>
<div class="lvl"><button type="button" class="lv-btn" data-step="-1" aria-label="Level down">−</button><output id="lvout">1</output><button type="button" class="lv-btn" data-step="1" aria-label="Level up">+</button>
<input id="lv" type="range" min="1" max="100" value="1" aria-label="Level"></div>
<div class="result" id="finder-out" aria-live="polite"></div>
<script type="application/json" id="finder-data">{json.dumps(fdata).replace("</", "<\\/")}</script></section>
<h2>Don't be that guy</h2><ol class="musts">{"".join(f"<li>{e(m)}</li>" for m in musts)}</ol>
{f'<div class="tipjar"><div><b>No ads. Powered by players.</b><span>This guide runs on donations. If it saved you a reset scroll, a coffee keeps it updated every patch.</span></div>{coffee_btn(True)}</div>' if COFFEE else ""}
<h2>Everything else</h2><div class="grid tiles">{"".join(f'<a class="card" href="{h}"><div class="icon">{_img(f"{API}/{ic}/render/stand", "", "")}</div><h3>{t}</h3><p>{d}</p></a>' for h, t, d, ic in cards)}</div>
<div class="facts" style="margin-top:28px"><div><b>Lv 100</b><span>Level cap</span></div><div><b>1st + 2nd job</b><span>3rd job planned for 2027</span></div><div><b>Victoria Island</b><span>Plus Maple Island; no Ossyria yet</span></div><div><b>7,000 NX</b><span>Per AP or SP reset</span></div></div>
<details style="margin-top:20px"><summary>What's different in Classic (60-second version)</summary><ul>{"".join(f"<li>{e(tidy(x))}</li>" for x in JOBS["classicChanges"][:8])}</ul></details>'''
    write("/", page("/", "MapleStory Classic Guide: Leveling, Builds & Secrets (2026)",
                    "MapleStory Classic World guide: pick your class and level, then get your build, where to train and the secrets you'll miss. All 10 jobs, made for phones.", body, hero=hero))

def build_leveling():
    route = sorted(LEV["route"], key=lambda r: (r["from"], r["to"]))
    regions = "".join(f'<tr><td data-th="Region"><b>{e(r["region"])}</b></td><td data-th="Status">{e(r["status"])}</td><td data-th="Notes">{e(tidy(r["notes"]))}</td></tr>' for r in LEV["regionsAvailable"])
    notes = "".join(f'<details><summary>{e(n["class"])}</summary><p>{e(tidy(n["note"]))}</p>{srcs(n.get("source"))}</details>' for n in LEV["classNotes"])
    tips = "".join(f'<li>{e(tidy(t["tip"]))}</li>' for t in LEV["tips"])
    more = [("/party-quest/", "🎟️ KPQ from level 21", "Grab 3 friends. Half a level a run in your low 20s, and every answer's on the page.", "npc/9020000"),
            ("/quests/", "📜 Quests worth doing", "Free EXP and gear by level, plus the ones to skip.", "npc/1012101"),
            ("/bosses/", "👑 Bosses and timers", "Where each boss spawns, how to walk there and when it's back.", "mob/6130101")]
    body = f'''<h1>Where to Train in MapleStory Classic, Level 1 to 100</h1>
<p class="lede">Tell us your level. We'll show you the spot, how to walk there map by map, and what to hit.</p>
{stamp()}
<div class="lvpick" id="quick"><label for="pick-lv">I'm level</label><div class="pick-row"><input id="pick-lv" type="number" inputmode="numeric" min="1" max="100" placeholder="23" aria-describedby="pick-out"><button type="button" class="btn btn-primary" id="pick-go">Show me where</button></div><p class="pick-out" id="pick-out" aria-live="polite">Or tap a level range below.</p></div>
<div class="jump" role="group" aria-label="Jump to level">{"".join(f'<a href="#lv-{r["from"]}-{r["to"]}">{r["from"]}–{r["to"]}</a>' for r in route if not (r["from"] == 39 and r["to"] == 60))}</div>
<p class="callout warn" style="margin:4px 0 16px"><b>Heads up:</b> Classic is Maple Island and Victoria Island only for now. Monsters top out around level 75, so the last stretch to 100 is a long grind.</p>
<h2 id="route">The route</h2><ol class="route">{"".join(route_li(r) for r in route)}</ol>
<p class="go-credit">Routes checked with <a href="{PATHFINDER}" target="_blank" rel="noopener">NiaMeowDB's Pathfinder</a> on {e(DIR["checked"])}. Tap "See every step" to see where each portal sits.</p>
<p class="callout" style="margin-top:12px">📈 Past 55? <a href="#endgame">Level 60 and beyond</a> has the best maps, a hit-chance checker and the EXP math.</p>
<h2 id="class">Training by class</h2>{notes}
<h2 id="more">Also worth your time</h2><div class="grid tiles">{"".join(f'<a class="card" href="{h}"><div class="icon">{_img(f"{API}/{ic}/render/stand", "", "")}</div><h3>{t}</h3><p>{d}</p></a>' for h, t, d, ic in more)}</div>
{endgame_html()}
<h2 id="tips">Tips that save you time</h2><ul>{tips}</ul>
<details id="map" style="margin-top:20px"><summary>What's in the game right now</summary><table class="tbl" style="margin-top:10px"><thead><tr><th>Region</th><th>Status</th><th>Notes</th></tr></thead><tbody>{regions}</tbody></table></details>'''
    write("/leveling/", page("/leveling/", "MapleStory Classic Training Spots: Where to Level 1–100",
                             "Type your level and get the best MapleStory Classic training spot, the monsters there and the walk from town, map by map. Levels 1 to 100, every class.", body,
                             crumbs=[("/", "Guide"), (None, "Leveling")],
                             schema={"@context": "https://schema.org", "@type": "Article", "headline": "MapleStory Classic Training Spots: Where to Level 1–100"}))

def mage_pick_html():
    MP = JOBS["magicianPick"]
    names = {j["id"]: j["name"] for c, j in ALLJOBS}
    rows = "".join(f'<tr><td data-th="Job"><a href="/jobs/{e(r["job"])}/"><b>{e(names[r["job"]])}</b></a><span class="show-sm" style="margin-top:4px">{e(r["pick"])}</span></td><td data-th="Solo"><span class="g g-{r["solo"].lower()}">{e(r["solo"])}</span></td><td data-th="Bossing"><span class="g g-{r["boss"].lower()}">{e(r["boss"])}</span></td><td data-th="Party"><span class="g g-{r["party"].lower()}">{e(r["party"])}</span></td><td data-th="1st character"><span class="g g-{r["first"].lower()}">{e(r["first"])}</span></td><td data-th="Pick it if" class="hide-sm">{e(r["pick"])}</td></tr>' for r in MP["rows"])
    return f'''<h3 id="which-magician" style="margin-top:18px">Which Magician? F/P vs I/L vs Cleric 🔮</h3><p class="muted">{e(MP["intro"])} <a href="/tier-list/">Full tier list →</a></p>
<table class="tbl compact grades"><thead><tr><th>Job</th><th>Solo</th><th>Bossing</th><th>Party</th><th>1st character</th><th class="hide-sm">Pick it if</th></tr></thead><tbody>{rows}</tbody></table>'''

def build_jobs():
    CR = JOBS["creation"]
    start = ""
    for c in JOBS["classes"]:
        st = CR["classes"][c["id"]]
        cn = IMG["classNpc"][c["id"]]
        tiles = "".join(f'<div{" class=hot" if n == st["main"] else ""}><b>{v}</b><span>{n}</span></div>' for n, v in zip(["STR", "DEX", "INT", "LUK"], st["stats"]))
        start += f'<article class="card start-card"><div class="start-top">{npc_img(cn[0], cn[1], "sprite sm")}<h3>{e(c["name"])}</h3></div><div class="facts stats" aria-label="{e(c["name"])} starting stats">{tiles}</div><p>{e(st["then"])}</p><p class="muted">Job up at level {e(c["firstJob"]["level"])} with {e(c["firstJob"]["npc"])} in {e(c["firstJob"]["town"])}.</p></article>'
    start_html = f'''<h2 id="start">New character? Your first 9 points 🎲</h2>
<p>{e(CR["intro"])}</p>
<div class="start-grid">{start}</div>
<p class="callout" style="margin-top:14px">🐌 {e(CR["beginner"])}</p>
<ul>{"".join(f"<li>{e(x)}</li>" for x in CR["tips"])}</ul>'''
    blocks = ""
    for c in JOBS["classes"]:
        fj = c["firstJob"]
        jobs = "".join(f'<a class="card" href="/jobs/{e(j["id"])}/"><h3>{e(j["name"])}</h3><p class="meta">{e(j["weapon"])}</p><p>{e(tidy(j["playstyle"]))}</p></a>' for j in c["jobs"])
        cn = IMG["classNpc"][c["id"]]
        blocks += f'''<h2 id="{e(c["id"])}">{e(c["name"])}</h2><div class="npc-row">{npc_img(cn[0], cn[1])}<span>{e(cn[1])}, {e(fj["town"])}</span></div>
<p><b>1st job:</b> level {e(fj["level"])} with {e(fj["npc"])} in {e(fj["town"])}. {e(tidy(fj["notes"]))}</p>
<div class="grid">{jobs}</div>{mage_pick_html() if c["id"] == "magician" else ""}'''
    body = f'''<h1>MapleStory Classic Job Builds</h1>
<p class="lede">Where your first 9 points go when you make a character, then AP and SP plans for every 2nd job. You place every point by hand in Classic, and a reset costs 7,000 NX, so plan before you click. Still choosing? See the <a href="/tier-list/">tier list</a>.</p>
{stamp()}<div class="toc"><a href="#start">New character</a>{"".join(f'<a href="#{e(c["id"])}">{e(c["name"])}</a>' for c in JOBS["classes"])}</div>{start_html}{blocks}
<h2>What changed for jobs in Classic</h2><ul>{"".join(f"<li>{e(tidy(x))}</li>" for x in JOBS["classicChanges"])}</ul>'''
    write("/jobs/", page("/jobs/", "MapleStory Classic Builds: Stats & Skills for All 10 Jobs",
                         "MapleStory Classic builds for all 10 jobs: starting stats, then where to put your stats (AP) and skills (SP) for every Warrior, Magician, Bowman and Thief.", body,
                         crumbs=[("/", "Guide"), (None, "Job builds")]))
    for c, j in ALLJOBS:
        def steps(lst):
            out = ""
            for s in lst:
                s = tidy(s)
                note = not re.match(r"^(lv|beginner)", s, re.I)
                out += f'<li class="{"note" if note else ""}">{e(s)}</li>'
            return out
        others = "".join(f'<a href="/jobs/{e(x["id"])}/">{e(x["name"])}</a>' for x in c["jobs"] if x["id"] != j["id"])
        side = f'<div class="card"><h3>Other {e(c["name"])} jobs</h3>{"".join(f"<p><a href=/jobs/{e(x["id"])}/>{e(x["name"])}</a></p>" for x in c["jobs"] if x["id"] != j["id"])}</div>'
        adv = j["advancement"]
        body = f'''<h1>{e(j["name"])} Build: MapleStory Classic</h1>
<p class="lede">{e(tidy(j["playstyle"]))}</p>
<p class="stamp"><span class="tag">{e(c["name"])}</span><span class="tag">{e(j["weapon"])}</span>{conf(j.get("confidence"))}<span>Checked {CHECKED}</span></p>
<section class="tldr" aria-label="TL;DR"><h2>TL;DR</h2><dl>
<div><dt>Stats</dt><dd>{e(tidy(j["ap"]["summary"]))}</dd></div>
<div><dt>Skills first</dt><dd>{e(" · ".join([tidy(x) for x in j["sp"]["secondJob"] if re.match(r"^lv", x, re.I) and not re.match(r"^lv\s?7[01]", x, re.I)][:2] or ["; ".join(tidy(j["sp"]["secondJob"][0]).split("; ")[:3])]))}</dd></div>
<div><dt>Job up</dt><dd>Level {e(adv["level"])}, {e(adv["npc"])} in {e(adv["town"])}</dd></div>
<div><dt>Good at</dt><dd>{e(tidy(j["pros"][0]))}</dd></div>
<div><dt>Watch out</dt><dd>{e(tidy(j["cons"][0]))}</dd></div></dl></section>
<div class="toc">{'<a href="#how-to-level">How to level</a>' if j.get("leveling") else ""}<a href="#ap">AP build</a><a href="#sp">SP build</a><a href="#adv">Job advancement</a><a href="#pros">Pros &amp; cons</a>{'<a href="#which-magician">Which Magician?</a>' if c["id"] == "magician" else ""}</div>
{f'<h2 id="how-to-level">How to level a {e(j["name"])} 📈</h2><ol class="musts">{"".join(f"<li>{e(x)}</li>" for x in j["leveling"])}</ol>' if j.get("leveling") else ""}
<h2 id="ap">AP build</h2><p class="callout">{e(tidy(j["ap"]["summary"]))}</p>
<ol class="steps" style="margin-top:12px">{steps(j["ap"]["steps"])}</ol>
<h2 id="sp">SP build</h2><h3>1st job (levels 10–29)</h3><ol class="steps" style="margin-top:8px">{steps(j["sp"]["firstJob"])}</ol>
<h3 style="margin-top:20px">2nd job (level 30+)</h3><ol class="steps" style="margin-top:8px">{steps(j["sp"]["secondJob"])}</ol>
<h2 id="adv">Job advancement</h2><div class="pics">{map_img(IMG["testMap"][c["id"]], "2nd job test map")}<div class="sprites">{npc_img(IMG["classNpc"][c["id"]][0], IMG["classNpc"][c["id"]][1])}</div></div><p><b>1st job:</b> level {e(c["firstJob"]["level"])}, {e(c["firstJob"]["npc"])} in {e(c["firstJob"]["town"])}.</p>
<p><b>2nd job:</b> level {e(adv["level"])}, {e(adv["npc"])} in {e(adv["town"])}. {e(tidy(adv["test"]))}</p>
{mage_pick_html() if c["id"] == "magician" else ""}
<h2 id="pros">Pros &amp; cons</h2><div class="pc"><div class="card"><h3>Pros</h3><ul>{"".join(f"<li>{e(tidy(x))}</li>" for x in j["pros"])}</ul></div><div class="card"><h3>Cons</h3><ul>{"".join(f"<li>{e(tidy(x))}</li>" for x in j["cons"])}</ul></div></div>
<p style="margin-top:20px">How does {e(j["name"])} rank? See the <a href="/tier-list/">MapleStory Classic tier list</a>.</p>
<p>Other {e(c["name"])} jobs: {" · ".join(f'<a href="/jobs/{e(x["id"])}/">{e(x["name"])}</a>' for x in c["jobs"] if x["id"] != j["id"])}</p>
{srcs(j.get("sources"))}'''
        write(f"/jobs/{j['id']}/", page(f"/jobs/{j['id']}/", job_title(j["name"]),
                                        f"MapleStory Classic {j['name']} build: where to put your stats (AP) each level, skill order (SP) for 1st and 2nd job, job advancement, pros and cons.", body,
                                        crumbs=[("/", "Guide"), ("/jobs/", "Job builds"), (None, j["name"])], side_extra=side,
                                        schema={"@context": "https://schema.org", "@type": "Article", "headline": f"{j['name']} Build Guide: MapleStory Classic"}))

def build_adv():
    first = "".join(f'<tr><td data-th="Class">{npc_img(IMG["classNpc"][c["id"]][0], IMG["classNpc"][c["id"]][1], "sprite sm")}<b>{e(c["name"])}</b></td><td data-th="Level">{e(c["firstJob"]["level"])}</td><td data-th="NPC">{e(c["firstJob"]["npc"])}</td><td data-th="Where">{e(c["firstJob"]["town"])}</td><td data-th="Stat req">{e(c["firstJob"]["statReq"])}</td></tr>' for c in JOBS["classes"])
    second = "".join(f'<tr><td data-th="Job"><a href="/jobs/{e(j["id"])}/"><b>{e(j["name"])}</b></a></td><td data-th="NPC">{e(j["advancement"]["npc"])}, {e(j["advancement"]["town"])}</td><td data-th="Test">{e(tidy(j["advancement"]["test"]))}</td></tr>' for c, j in ALLJOBS)
    body = f'''<h1>MapleStory Classic Job Advancement</h1>
<p class="lede">1st job at level 10 with no stat requirement, 2nd job at level 30 after a short Dark Marble test. Here's who to see and where.</p>
{stamp()}
<h2 id="quick">The 30-second version</h2><ol class="musts">{"".join(f'<li><b>{e(c["name"])}:</b> level {e(c["firstJob"]["level"])}, talk to {e(c["firstJob"]["npc"])} in {e(c["firstJob"]["town"])}. Come back to them at 30 for 2nd job.</li>' for c in JOBS["classes"])}<li><b>2nd job test:</b> collect 30 Dark Marbles in the test map, trade them for The Proof of a Hero, then pick your path. <a href="#second">Details</a></li></ol>
<p class="callout" style="margin-top:12px">💡 Still a Beginner? Taxis are 90% off until you job up, so ride to your job town. New character? See <a href="/jobs/#start">where your first 9 points go</a>.</p>
<h2>1st job (level 10)</h2><table class="tbl"><thead><tr><th>Class</th><th>Level</th><th>NPC</th><th>Where</th><th>Stat req</th></tr></thead><tbody>{first}</tbody></table>
<p style="margin-top:12px">Tip: ride the taxi to your job town while you're still a Beginner. Beginners get 90% off taxis.</p>
<h2 id="second">2nd job (level 30)</h2><p>Every class works the same way: your job NPC gives you a letter, the Job Instructor sends you into a test map, you collect 30 Dark Marbles, trade them for The Proof of a Hero and bring it back to choose your path.</p>
<table class="tbl"><thead><tr><th>Job</th><th>Who</th><th>The test</th></tr></thead><tbody>{second}</tbody></table>
<h2>3rd job</h2><p>Not in Classic at launch. Nexon has said a 3rd job test server is planned for early 2027, alongside the Ossyria rework.</p>'''
    write("/job-advancement/", page("/job-advancement/", "MapleStory Classic Job Advancement: 1st & 2nd Job Guide",
                                    "How to job advance in MapleStory Classic: level 10 1st job NPCs, the level 30 2nd job Dark Marble test for all 10 jobs, and when 3rd job arrives.", body,
                                    crumbs=[("/", "Guide"), (None, "Job advancement")]))

def spoil(inner, s):
    if "Forgotten Hollow" in (s.get("name", "") + s.get("region", "") + s.get("howToGet", "")):
        return f'<details class="spoiler"><summary>Spoiler: new content (opens Nov 18). Tap to show</summary>{inner}</details>'
    return inner

def build_secrets():
    types = []
    for s in SEC["secrets"]:
        if s["type"] not in types: types.append(s["type"])
    slug = lambda t: re.sub(r"[^a-z]+", "-", t.lower()).strip("-")
    btns = '<button type="button" data-f="all" aria-pressed="true">All</button>' + "".join(f'<button type="button" data-f="{slug(t)}" aria-pressed="false">{e(t.capitalize())}</button>' for t in types)
    cards = ""
    for s in SEC["secrets"]:
        future = "" if s.get("classicConfirmed", True) else ' <span class="tag">Not confirmed in Classic</span>'
        cards += f'''<article class="card" id="{slug(s["name"].split(" (")[0])}" data-type="{slug(s["type"])}">{secret_img(s["name"])}<h3>{e(s["name"])}</h3>
<p class="meta">{e(s["type"].capitalize())} · {e(s["region"])} · Level {e(s["level"])} {conf(s.get("confidence"))}{future}</p>
{spoil(f'<p><b>How to get there:</b> {e(tidy(s["howToGet"]))}</p>{route_go(s["name"], 1) or route_go(s["howToGet"], 1)}<p><b>Why go:</b> {e(tidy(s["reward"]))}</p>', s)}</article>'''
    body = f'''<h1>MapleStory Classic Hidden Maps &amp; Secrets</h1>
<p class="lede">Hidden streets, jump quests, boss rooms and one-time rewards on Maple Island and Victoria Island, with directions.</p>
{stamp()}
<p class="callout warn" style="margin-top:12px"><b>Don't miss:</b> Maple Island is one-way. Finish its quests (including Pio's boxes for the Green Relaxer chair) before you take the boat.</p>
<h2 id="all">All {len(SEC["secrets"])} secrets</h2>
<div class="filters" data-filters role="group" aria-label="Filter by type">{btns}</div>
<div class="grid">{cards}</div>
'''
    write("/secrets/", page("/secrets/", "MapleStory Classic Hidden Maps, Jump Quests & Secrets",
                            f"{len(SEC['secrets'])} MapleStory Classic secrets: hidden streets, Forest of Patience and Shumi jump quests, Mushmom and Jr. Balrog rooms, and missable Maple Island rewards.", body,
                            crumbs=[("/", "Guide"), (None, "Secrets")]))

def build_rules():
    mech = "".join(f'<h2 id="m{i}">{e(m["topic"])}</h2><p>{conf(m.get("confidence"))}</p><ul>{"".join(f"<li>{e(tidy(x))}</li>" for x in m["facts"])}</ul>{srcs(m.get("source"))}' + ('<p class="callout">⚒️ Full breakdown, with what to keep for each profession: <a href="/crafting/">Crafting guide</a>.</p>' if "raft" in m["topic"] else "") for i, m in enumerate(SEC["mechanics"]))
    money = "".join(f'<div class="card"><h3>{e(m["method"])} {conf(m.get("confidence"))}</h3><p>{e(tidy(m["details"]))}</p></div>' for m in SEC["moneyMaking"])
    toc = "".join(f'<a href="#m{i}">{e(m["topic"])}</a>' for i, m in enumerate(SEC["mechanics"])) + '<a href="#money">Making mesos</a>'
    body = f'''<h1>MapleStory Classic Rules &amp; Mechanics</h1>
<p class="lede">What's different in Classic: scroll odds, resets, death penalty, the EXP curve, crafting, bosses, the Cash Shop and the economy.</p>
{stamp()}<div class="toc">{toc}</div>{mech}
<h2 id="money">Making mesos</h2><p class="callout">💰 Prices, meso quests and boss drops in one place: <a href="/money-making/">Money making guide</a>.</p><div class="grid" style="margin-top:12px">{money}</div>'''
    write("/classic-rules/", page("/classic-rules/", "MapleStory Classic Mechanics: Scrolls, EXP, Crafting & Mesos",
                                  "MapleStory Classic rules explained: scroll success rates, AP/SP reset cost, EXP table and the 90+ wall, crafting professions, boss timers and money making.", body,
                                  crumbs=[("/", "Guide"), (None, "Classic rules")]))

def build_tiers():
    jobs = {j["id"]: (c, j) for c, j in ALLJOBS}
    def jname(jid): return jobs[jid][1]["name"]
    def face(jid):
        c = jobs[jid][0]; n = IMG["classNpc"][c["id"]]
        return npc_img(n[0], c["name"], "sprite sm")
    picks = "".join(f'<a class="pick" href="/jobs/{e(p["job"])}/"><span class="pl">{e(p["label"])}</span><b>{e(jname(p["job"]))}</b><span>{e(p["why"])}</span></a>' for p in TIERS["picks"])
    toc = "".join(f'<a href="#{e(l["id"])}">{l["emoji"]} {e(l["title"])}</a>' for l in TIERS["lists"]) + '<a href="#grades">All grades</a><a href="#faq">FAQ</a>'
    lists = ""
    for l in TIERS["lists"]:
        rows = ""
        for t in ["S", "A", "B"]:
            items = "".join(f'<li><a href="/jobs/{e(jid)}/">{face(jid)}<b>{e(jname(jid))}</b></a><span>{e(why)}</span></li>' for jid, why in l["tiers"][t])
            rows += f'<div class="tier t-{t.lower()}"><div class="tl" aria-label="{t} tier">{t}</div><ul>{items}</ul></div>'
        lists += f'<h2 id="{e(l["id"])}">{l["emoji"]} {e(l["title"])}</h2><p>{e(l["intro"])}</p><div class="tiers">{rows}</div>'
    cols = TIERS["grades"]["cols"]
    grows = "".join(f'<tr><td data-th="Job"><a href="/jobs/{e(jid)}/"><b>{e(jname(jid))}</b></a> <span class="muted">{e(jobs[jid][0]["name"])}</span></td>' +
                    "".join(f'<td data-th="{e(cols[i])}"><span class="g g-{g.lower()}">{g}</span></td>' for i, g in enumerate(gs)) + "</tr>"
                    for jid, gs in TIERS["grades"]["rows"].items())
    faq = "".join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in TIERS["faq"])
    body = f"""<h1>MapleStory Classic Tier List: Best Class for How You Play</h1>
<p class="lede">There's no single best class in Classic. So we ranked all 10 jobs four ways: solo grinding, bossing, party play and how forgiving they are for new players.</p>
<p class="stamp"><b>✓ Checked {CHECKED}</b><span>Level 70, 1st + 2nd job, launch build. {conf(TIERS["meta"]["confidence"])} We re-rank after launch.</span></p>
<h2 id="picks">Quick picks</h2><div class="picks">{picks}</div>
<div class="toc">{toc}</div>
{lists}
<h2 id="grades">All grades at a glance</h2>
<table class="tbl grades"><thead><tr><th>Job</th>{"".join(f"<th>{e(c)}</th>" for c in cols)}</tr></thead><tbody>{grows}</tbody></table>
<p class="muted" style="margin-top:8px">S = top third, A = middle, B = bottom third of the 10 jobs for that column. Mobility counts Teleport and Haste.</p>
<h2>How we ranked them</h2><p>{e(TIERS["meta"]["basis"])} Gear, scrolls, party makeup and the maps you pick change real results, and 3rd job (planned for 2027) will shake this up. Picked a job? Grab its <a href="/jobs/">AP and SP build</a> next.</p>
{srcs(TIERS["meta"]["sources"])}
<h2 id="faq">FAQ</h2>{faq}"""
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in TIERS["faq"]]}
    side = '<div class="card"><h3>Job builds</h3>' + "".join(f'<p><a href="/jobs/{e(j["id"])}/">{e(j["name"])}</a></p>' for _, j in ALLJOBS) + "</div>"
    write("/tier-list/", page("/tier-list/", "MapleStory Classic Tier List (2026): Best Class to Pick",
                              "MapleStory Classic tier list for all 10 jobs: best class for solo grinding, bossing, party play and beginners, with quick picks and FAQ.", body,
                              crumbs=[("/", "Guide"), (None, "Tier list")], schema=schema, side_extra=side))

def tipjar(path):
    if not COFFEE or path in ("/", "/404", "/privacy/", "/about/"): return ""
    return f'<div class="tipjar slim"><div><b>No ads, ever. Powered by players.</b><span>If this page helped, a coffee keeps the guide free and updated.</span></div>{coffee_btn()}</div>'

def feedback(path):
    if path in ("/404", "/privacy/"): return ""
    return f"""<section class="fb" data-fb-key="{e(WEB3FORMS_KEY)}" aria-labelledby="fbh">
<p id="fbh" class="fb-q">Was this page right?</p>
<div class="fb-btns"><button type="button" class="fb-b" data-fb="up">👍 Yep</button><button type="button" class="fb-b" data-fb="down">👎 Something's off</button></div>
<form class="fb-form" hidden><label for="fbm">What did you see in game?</label>
<textarea id="fbm" name="message" rows="3" maxlength="1500" required placeholder="e.g. Ant Tunnel I beats Ant Tunnel II at level 25, I get about 40k EXP an hour there"></textarea>
<input type="checkbox" name="botcheck" class="fb-hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<div class="fb-row"><button type="submit" class="btn btn-primary">Send fix</button><span class="fb-note">Goes straight to us. No account needed.</span></div></form>
</section>"""

def build_tools():
    expdata = json.dumps({"toNext": EXP["toNext"]})
    body = f"""<h1>MapleStory Classic Tools: EXP Calculator &amp; Scroll Simulator</h1>
<p class="lede">How long until your next level, and what happens if you slap a Chaos scroll on your weapon. Saved on your device, nothing to sign up for.</p>
<div class="toc"><a href="#exp">⏱ EXP calculator</a><a href="#scrolls">✨ Scroll simulator</a></div>
<h2 id="exp">⏱ EXP calculator</h2>
<p>Classic uses the old-school EXP curve up to level 89, then every level from 90 costs 2.1× the last. Level 99 to 100 alone is about 9.5 billion EXP.</p>
<div class="tool" id="expcalc">
<div class="tool-grid">
<label>Your level<input type="number" id="xc-lv" min="1" max="99" value="1" inputmode="numeric"></label>
<label>EXP bar %<input type="number" id="xc-pct" min="0" max="99.99" step="0.01" value="0" inputmode="decimal"></label>
<label>Goal level<input type="number" id="xc-goal" min="2" max="100" value="10" inputmode="numeric"></label>
<label>EXP per hour<input type="number" id="xc-rate" min="0" step="1000" placeholder="e.g. 40000" inputmode="numeric"></label>
</div>
<div class="tool-row"><button type="button" class="btn btn-ghost" id="xc-start">⏱ Measure my EXP/hour</button><span class="muted" id="xc-timer" aria-live="polite"></span></div>
<div class="tool-out" id="xc-out" aria-live="polite"></div>
<script type="application/json" id="exp-data">{expdata}</script>
</div>
<p class="muted" style="margin-top:8px">How to measure: tap the button, grind for 10 minutes or more, update your level and EXP %, then tap it again.</p>
<h2 id="scrolls">✨ Scroll simulator</h2>
<p>Classic's scrolls come in four grades, and how much each one adds depends on the scroll type. Every attempt uses a slot, pass or fail, and only Chaos scrolls can destroy the item (half of failed Chaos attempts). Try your luck here before you spend real mesos.</p>
<div class="tool" id="scrollsim">
<div class="tool-grid">
<label>Scroll type<select id="ss-type">
<option value="watk" selected>Weapon attack</option>
<option value="matk">Magic attack (staff, wand)</option>
<option value="stat">Stat or accuracy</option></select></label>
<label>Scroll<select id="ss-grade">
<option value="lesser">Lesser: 100%</option>
<option value="inter" selected>Intermediate: 60%</option>
<option value="greater">Greater: 10%</option>
<option value="chaos">Chaos: 10%, can boom</option></select></label>
<label>Upgrade slots<input type="number" id="ss-slots" min="1" max="10" value="7" inputmode="numeric"></label>
</div>
<div class="item" id="ss-item" aria-live="polite"></div>
<div class="tool-row"><button type="button" class="btn btn-primary" id="ss-one">Use 1 scroll</button><button type="button" class="btn btn-ghost" id="ss-all">Use all slots</button><button type="button" class="btn btn-ghost" id="ss-reset">New item</button></div>
<ol class="ss-log" id="ss-log"></ol>
</div>
<p class="muted" style="margin-top:8px">Weapon attack scrolls add +1 / +2 / +4 / +5 (Lesser / Intermediate / Greater / Chaos), so the average gain per slot is 1.0, 1.2, 0.4 and 0.5. Magic attack scrolls add +2 / +4 / +8 / +10, and stat scrolls +1 / +2 / +3 / +4. Intermediate is the best value every time, and each Chaos attempt has a 45% chance to boom.</p>
<h2>More on scrolls and EXP</h2><p>The full rules (scroll families, resets, death penalty) are on <a href="/classic-rules/">Classic rules</a>.</p>{srcs(EXP["source"])}"""
    write("/tools/", page("/tools/", "MapleStory Classic EXP Calculator & Scroll Simulator",
                          "Free MapleStory Classic tools: an EXP calculator with an EXP-per-hour stopwatch, and a scroll simulator for Lesser, Intermediate, Greater and Chaos.", body,
                          crumbs=[("/", "Guide"), (None, "Tools")]))

def build_crafting():
    C = CRAFT
    def icon(name, cls="ic"):
        it = C["items"].get(name, {})
        if it.get("icon"):
            return f'<img class="{cls}" src="{API}/item/{it["icon"]}/icon" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.replaceWith(Object.assign(document.createElement(\'span\'),{{className:\'{cls} emo\',textContent:\'📦\'}}))">'
        return f'<span class="{cls} emo" aria-hidden="true">{it.get("emoji", "📦")}</span>'
    def mob(name):
        i = C["mobs"].get(name)
        return _img(mob_src(i), name, "mobxs") if i else ""
    def source(name):
        it = C["items"].get(name, {})
        if it.get("made"): return f'<span class="src-line">Made: {e(it["made"])}</span>'
        if it.get("from"): return f'<span class="src-line"><span class="mobs">{"".join(mob(m) for m in it["from"])}</span>From {e(", ".join(it["from"]))}</span>'
        return ""
    def keep_card(name, why):
        return f'<li class="kp">{icon(name)}<div><b>{e(name)}</b><span>{e(why)}</span>{source(name)}</div></li>'
    chips = "".join(f'<a href="#{p["id"]}">{p["emoji"]} {e(p["name"])}</a>' for p in C["professions"])
    every = "".join(f'<li class="kp sm">{icon(n)}<div><b>{e(n)}</b>{source(n)}</div></li>' for n in C["everyone"])
    lv = "".join(f'<tr><td data-th="Crafting level"><b>{l}</b></td><td data-th="EXP to next">{(f"{x:,}" if x else "max at launch")}</td><td data-th="Character level needed">{c}</td></tr>' for l, x, c in C["levels"])
    profs = ""
    for p in C["professions"]:
        keep = "".join(keep_card(n, w) for n, w in p["keep"])
        extra = (f'<p class="callout">{e(p["tip"])}</p>' if p.get("tip") else "") + \
                (f'<p class="callout warn"><b>Don\'t sell your bases.</b> {e(p["bases"])}</p>' if p.get("bases") else "") + \
                (f'<p class="muted">💰 {e(p["money"])}</p>' if p.get("money") else "")
        profs += f'''<section class="prof" id="{p["id"]}" aria-labelledby="h-{p["id"]}">
<h2 id="h-{p["id"]}">{p["emoji"]} {e(p["name"])}</h2>
<p class="prof-meta"><span class="tag">Mentor: {e(p["mentor"])}, {e(p["town"])}</span></p>
<p>{e(p["makes"])} <b>Best for:</b> {e(p["goodFor"])}.</p>
<h3>Leveling {e(p["name"])}? Keep these</h3>
<ul class="keep">{keep}</ul>{extra}</section>'''
    faq = "".join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in C["faq"])
    body = f"""<h1>MapleStory Classic Crafting Guide: What to Keep for Every Profession</h1>
<p class="lede">Six professions, 290 launch recipes, and one rule: stop vendoring the wrong drops. Pick your profession and see exactly which items to hold on to, and which monsters drop them.</p>
<p class="stamp"><b>✓ Checked {CHECKED}</b><span>Launch recipes, crafting levels 1 to 8. {conf(C["meta"]["confidence"])}</span></p>
<div class="toc">{chips}<a href="#basics">How it works</a><a href="#faq">FAQ</a></div>
<h2 id="never">🎒 Never sell these (every crafter needs them)</h2>
<p>These show up across the most recipes and sell fast on the Free Market, so they're never wasted bag space.</p>
<ul class="keep cols">{every}</ul>
<h2 id="basics">📜 How crafting works in Classic</h2>
<ul>{"".join(f"<li>{e(b)}</li>" for b in C["basics"])}</ul>
<table class="tbl grades"><thead><tr><th>Crafting level</th><th>EXP to next</th><th>Character level needed</th></tr></thead><tbody>{lv}</tbody></table>
{profs}
<h2 id="faq">FAQ</h2>{faq}
<p class="muted" style="margin-top:16px">{e(C["meta"]["note"])} Item and monster art from maplestory.io (classic sprites; a few Classic-only items use a stand-in icon).</p>
{srcs(C["meta"]["sources"])}"""
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in C["faq"]]}
    side = '<div class="card"><h3>Professions</h3>' + "".join(f'<p><a href="#{p["id"]}">{p["emoji"]} {e(p["name"])}</a></p>' for p in C["professions"]) + "</div>"
    write("/crafting/", page("/crafting/", "MapleStory Classic Crafting Guide: What to Keep and Sell",
                             "MapleStory Classic crafting: what to keep for Smithing, Weaponcrafting, Tailoring, Woodcrafting, Leatherworking and Arcforge, and where it drops.", body,
                             crumbs=[("/", "Guide"), (None, "Crafting")], schema=schema, side_extra=side))

G = load("guides.json")
QG = load("questguides.json")  # step-by-step data for each quest page (/quests/<slug>/)
QGB = {q["name"]: q for q in QG["quests"]}

def icon_id(name):
    """maplestory.io (GMS v83) item ID for an item name, or None. Classic's scroll names get a stand-in scroll icon."""
    if name in G["icons"]: return G["icons"][name]
    if name in QG["icons"]: return QG["icons"][name]
    if "Scroll:" in name or name.startswith("Greater weapon"):
        kind = "attack" if "Attack" in name or "weapon" in name else "shoes" if name.startswith("Shoes") else "armor"
        return QG["icons"]["_scroll_" + kind]
    return None

def gicon(spec, cls="ic"):
    name = spec.split("|")[0]
    iid = icon_id(name)
    if iid:
        return f'<img class="{cls}" src="{API}/item/{iid}/icon" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.replaceWith(Object.assign(document.createElement(\'span\'),{{className:\'{cls} emo\',textContent:\'📦\'}}))">'
    em = next((v for k, v in {**G["emoji"], **QG["emoji"]}.items() if k in name), "📦")
    return f'<span class="{cls} emo" aria-hidden="true">{em}</span>'

def rw(spec):
    name, _, label = spec.partition("|")
    text = name if not label else (f"{name} {label}" if label.startswith("x") else label)
    return f'<span class="rw">{gicon(spec, "ic")}<span>{e(text)}</span></span>'

def who(npc_id, name, cls="sprite"):
    if isinstance(npc_id, int): return npc_img(npc_id, name, cls)
    return f'<span class="npc-emo" aria-hidden="true">{npc_id}</span>'

def boss_sprite(b, cls="sprite"):
    s = _img(mob_src(b["mob"]), b["name"] + (" (stand-in art)" if b.get("rotten") else ""), cls + (" rotten" if b.get("rotten") else ""))
    return s

def faq_html(rows):
    return "".join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in rows)

def faq_schema(rows):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in rows]}

def guide_stamp(extra=""):
    return f'<p class="stamp" data-pagefind-ignore><b>✓ Checked {G["checked"]}</b><span>{extra}Tags show how sure we are: {conf("high")} {conf("medium")} {conf("low")}</span></p>'

def build_bosses():
    B = G["bosses"]
    ladder = "".join(f'<a href="#{b["id"]}" class="rung">{boss_sprite(b, "bs")}<b>{e(b["name"])}</b><span>Lv {b["lv"]}</span></a>' for b in B)
    rows = "".join(f'<tr><td data-th="Boss"><a href="#{b["id"]}"><b>{e(b["name"])}</b></a></td><td data-th="Level">{b["lv"]}</td><td data-th="HP">{b["hp"]:,}</td><td data-th="EXP">{b["exp"]:,}</td><td data-th="Respawn">{e(b.get("short", b["respawn"]))}</td></tr>' for b in B)
    cards = ""
    for b in B:
        el = "".join(f'<span class="el good">Weak: {e(x)}</span>' for x in b["weak"]) + "".join(f'<span class="el bad">Resists: {e(x)}</span>' for x in b["strong"])
        traits = "".join(f'<span class="tag">{e(t)}</span>' for t in b["traits"])
        drops = "".join(rw(d) for d in b["drops"])
        timer = f'<div class="timer" data-boss="{b["id"]}" data-min="{60 if b["timer"] == 75 else b["timer"]}" data-max="{90 if b["timer"] == 75 else b["timer"]}"><button type="button" class="btn btn-ghost sm" data-kill>⏱ I just killed it</button><span class="timer-out" aria-live="polite"></span></div>' if b["timer"] else (f'<p><a class="btn btn-ghost sm" href="{b["link"]}">Read the KPQ guide →</a></p>' if b.get("link") else "")
        stats = f'<div class="bstats"><div><b>{b["hp"]:,}</b><span>HP</span></div><div><b>{b["exp"]:,}</b><span>EXP</span></div><div><b>{e(b["mesos"] or "–")}</b><span>Mesos/kill</span></div></div>'
        maybe = f'<p class="muted" style="margin-top:6px">{e(b["maybe"])}</p>' if b.get("maybe") else ""
        cards += f'''<article class="boss{" future" if b.get("future") else ""}" id="{b["id"]}">
<div class="boss-art"><span class="lvb">Lv {b["lv"]}</span>{boss_sprite(b, "big")}</div>
<div class="boss-body"><h2>{e(b["name"])} {conf(b["conf"])}{' <span class="chip c-medium">Nov 18</span>' if b.get("future") else ""}</h2>
<p class="meta">📍 {e(b["where"])} · 🔁 {e(b["respawn"])}</p>
{go_html(DIR["bosses"].get(b["id"], ""), "How to get there: ")}
{stats}<div class="els">{el}{traits}</div>
<p><b>Try it at:</b> {e(b["tryAt"])}</p>
<h3>Drops players have seen</h3><div class="rws">{drops}</div>{maybe}
<p class="callout">{e(b["tip"])}</p>{timer}{srcs(b["src"])}</div></article>'''
    body = f"""<h1>MapleStory Classic Bosses: Where to Find Every Boss and What It Drops</h1>
<p class="lede">Every boss on Maple Island and Victoria Island, from Mano to Jr. Balrog: where it spawns, how long the respawn takes, what it drops and when you're ready to fight it.</p>
{guide_stamp("Launch data, Founder's Access drops. ")}
<div class="ladder" role="list" aria-label="Bosses by level">{ladder}</div>
<p class="callout" style="margin-top:14px">⏱ <b>Respawn timers:</b> tap "I just killed it" on any boss and we'll count down to its next spawn window. It's saved on this device only.</p>
<h2 id="glance">At a glance</h2><table class="tbl compact"><thead><tr><th>Boss</th><th>Level</th><th>HP</th><th>EXP</th><th>Respawn</th></tr></thead><tbody>{rows}</tbody></table>
<div class="bosses">{cards}</div>
<h2 id="faq">FAQ</h2>{faq_html(G["bossFaq"])}"""
    side = '<div class="card"><h3>Bosses</h3>' + "".join(f'<p><a href="#{b["id"]}">{e(b["name"])}</a> <span class="muted">Lv {b["lv"]}</span></p>' for b in B) + '<p><a href="/party-quest/">KPQ guide →</a></p></div>'
    write("/bosses/", page("/bosses/", "MapleStory Classic Bosses: Locations, Respawn Timers & Drops",
                           "Every MapleStory Classic boss from Mano to Jr. Balrog: where it spawns, how long it takes to respawn, what it drops and the level to fight it.", body,
                           crumbs=[("/", "Guide"), (None, "Bosses")], schema=faq_schema(G["bossFaq"]), side_extra=side))

def build_kpq():
    K = G["kpq"]
    facts = "".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in K["facts"])
    stages = ""
    for s in K["stages"]:
        sprites = "".join(_img(mob_src(m), "", "sprite") for m in s["mobs"])
        combo = ""
        if s.get("combo"):
            btns = "".join(f'<button type="button" aria-pressed="false">{e(c)}</button>' for c in s["combo"])
            combo = f'<div class="combo" data-combo="s{s["n"]}"><p class="combo-h"><b>Tap each combo as you try it, double-tap the winner</b><span>{len(s["combo"])} combos</span><button type="button" class="combo-reset">Reset</button></p><div class="combo-g">{btns}</div></div>'
        tip = f'<p class="callout">💡 {e(s["tip"])}</p>' if s.get("tip") else ""
        stages += f'<li class="stage" id="stage-{s["n"]}"><span class="sn">{s["n"]}</span><div><h3>{e(s["title"])}</h3>{f"<div class=sprites>{sprites}</div>" if sprites else ""}<p>{e(s["text"])}</p>{combo}{tip}</div></li>'
    cloto = "".join(f'<tr><td data-th="Cloto asks">{e(q)}</td><td data-th="Coupons"><span class="rw">{gicon("Coupon")}<b>{n}</b></span></td></tr>' for q, n in K["cloto"])
    mobs = "".join(f'<tr><td data-th="Monster">{_img(mob_src(i), n, "sprite sm")}<b>{e(n)}</b></td><td data-th="Level">{lv}</td><td class="hide-sm" data-th="HP">{hp:,}</td><td data-th="EXP">{x:,}</td><td data-th="Where">{e(w)}</td></tr>' for n, i, lv, hp, x, w in K["mobs"])
    box = "".join(rw(x) for x in K["box"])
    other = "".join(f'<div class="card"><h3>{e(n)} {conf(c)}</h3><p class="meta">{e(lv)}</p><p>{e(t)}</p></div>' for n, lv, t, c, _ in K["other"])
    npcs = "".join(f'<figure class="npcfig">{npc_img(i, n)}<figcaption>{e(n)}</figcaption></figure>' for i, n in [(9020000, "Lakelis"), (9020001, "Cloto"), (9020002, "Nella")])
    body = f"""<h1>Kerning City Party Quest (KPQ) Guide for MapleStory Classic</h1>
<p class="lede">Four players, five stages and King Slime at the end. Every answer, every combination and what's in the box, so your party never stalls on the barrels again.</p>
{guide_stamp("Launch version of KPQ. ")}
<div class="facts" style="margin-top:18px">{facts}</div>
<div class="toc"><a href="#start">Start</a><a href="#stages">Stages</a><a href="#cloto">Coupon answers</a><a href="#rewards">Rewards</a><a href="#etiquette">Party tips</a><a href="#other">Other PQs</a><a href="#faq">FAQ</a></div>
<h2 id="start">How to start</h2><div class="npcs">{npcs}</div><p>{e(K["start"])}</p>
<h2 id="stages">Stage by stage</h2><ol class="stages">{stages}</ol>
<h2 id="cloto">Cloto's coupon answers</h2><table class="tbl compact"><thead><tr><th>Cloto asks</th><th>Coupons</th></tr></thead><tbody>{cloto}</tbody></table><p class="muted" style="margin-top:8px">{e(K["clotoNote"])}</p>
<h2 id="monsters">Monsters inside KPQ</h2><p>KPQ uses its own weaker copies: stage 1's Ligators are level 21, not the level 31 ones in the swamp.</p><table class="tbl compact"><thead><tr><th>Monster</th><th>Lv</th><th class="hide-sm">HP</th><th>EXP</th><th>Where</th></tr></thead><tbody>{mobs}</tbody></table>
<h2 id="rewards">Rewards</h2><p>EXP as you clear each stage, a shot at Squishy Shoes from King Slime, and a Companion's Magic Box for every member at the end. {e(K.get("expNote", ""))}</p>
<div class="kp shoes">{gicon("Squishy Shoes")}<div><b>Squishy Shoes</b><span>{e(K["shoes"])}</span></div></div>
<h3>What players pull from the Companion's Magic Box</h3><div class="rws">{box}</div>
<h2 id="etiquette">Party tips</h2><ul>{"".join(f"<li>{e(r)}</li>" for r in K["rules"])}</ul>
<p class="callout"><b>If someone dies or disconnects:</b> {e(K["death"])}</p>
<h2 id="other">Other party quests</h2><div class="grid">{other}</div>
{srcs(K["src"])}
<h2 id="faq">FAQ</h2>{faq_html(K["faq"])}"""
    side = '<div class="card"><h3>KPQ stages</h3>' + "".join(f'<p><a href="#stage-{s["n"]}">{s["n"]}. {e(s["title"])}</a></p>' for s in K["stages"]) + '<p><a href="/bosses/#king-slime">King Slime →</a></p></div>'
    write("/party-quest/", page("/party-quest/", "KPQ Guide: Kerning City Party Quest in MapleStory Classic",
                                "MapleStory Classic KPQ guide: level 21+, Cloto's coupon answers, every rope, kitten and barrel combo, King Slime and the rewards worth farming.", body,
                                crumbs=[("/", "Guide"), (None, "Party quest")], schema=faq_schema(K["faq"]), side_extra=side))

VERDICT = {"must": ("Must do", "v-must"), "good": ("Worth it", "v-good"), "fun": ("For fun", "v-fun"), "skip": ("Skip it", "v-skip"), "future": ("From Nov 18", "v-future")}
def qslug(n): return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")
def qhref(q):
    """The quest's own step-by-step page when it has one, else its card on /quests/."""
    gq = QGB.get(q["name"] if isinstance(q, dict) else q)
    return f'/quests/{gq["slug"]}/' if gq else f'/quests/#q-{qslug(q["name"] if isinstance(q, dict) else q)}'
def first_sentence(t):
    """First sentence of t, without splitting on Mr. / Dr. / Lv. and friends."""
    m = re.search(r"(?<!\bMr)(?<!\bMrs)(?<!\bDr)(?<!\bJr)(?<!\bLv)(?<!\bSt)\.(\s|$)", t or "")
    return (t[:m.start() + 1] if m else t or "").strip()

def build_quests():
    toNext = EXP["toNext"]
    bands = G["questBands"] + [[51, 99, None]]
    sections = ""
    chips = ""
    for lo, hi, total in bands:
        qs = [q for q in G["quests"] if lo <= q["lv"] <= hi]
        if not qs: continue
        bid = f"lv{lo}-{hi}"
        label = f"Level {lo} to {hi}" if hi < 99 else f"Level {lo}+"
        chips += f'<a href="#{bid}">{lo}–{hi if hi < 99 else "+"}</a>'
        cards = ""
        for q in qs:
            gq = QGB.get(q["name"])
            if gq:  # the walkthrough data is newer and checked step by step, so it wins on the card too
                r = gq["rewards"]
                q = {**q, "task": gq["card"], "rewards": gq["cardRewards"], "exp": r["exp"] or q["exp"], "mesos": r["mesos"] or q["mesos"],
                     "verdict": "future" if gq["status"] == "future" else q["verdict"], "steps": len(gq["chain"]) or q["steps"],
                     "note": first_sentence(gq["missable"]), "link": f'/quests/{gq["slug"]}/'}
            need = toNext[min(q["lv"], len(toNext)) - 1]
            ratio = q["exp"] / need
            gauge = f"{ratio:.1f} levels at Lv {q['lv']}" if ratio >= 1 else f"{round(ratio * 100)}% of a level at Lv {q['lv']}"
            if q["lv"] < 8: gauge = "gets you to about Lv 8"
            vl, vc = VERDICT[q["verdict"]]
            rws = "".join(rw(r) for r in q["rewards"])
            note = f'<p class="qnote">{e(q["note"])}</p>' if q["note"] else ""
            step = f'<a class="q-steps" href="{q["link"]}">Step-by-step guide →</a>' if q.get("link") else ""
            cards += f'''<article class="quest {vc}" id="q-{qslug(q["name"])}" data-q="{qslug(q["name"])}">
<div class="q-top">{who(q["npcId"], q["npc"], "sprite")}<span class="verdict">{vl}</span></div>
<h3>{e(q["name"])}</h3><p class="meta">Lv {q["lv"]} · {e(q["npc"])}, {e(q["town"])}{f" · {q['steps']} quests" if q["steps"] > 1 else ""}</p>
<div class="gauge" title="EXP compared with what level {q["lv"]} needs"><i style="width:{min(100, round(ratio * 100))}%"></i></div>
<p class="q-nums"><b>{q["exp"]:,} EXP</b> <span>≈ {gauge}</span>{f" · <b>{q['mesos']:,}</b> mesos" if q["mesos"] else ""}</p>
<p>{e(q["task"])}</p>{f'<div class="rws">{rws}</div>' if rws else ""}{note}
<div class="q-acts"><button type="button" class="q-done" aria-pressed="false">Mark done</button>{step}</div></article>'''
        tot = f'<span class="muted">{total:,} EXP of shared quests in this band</span>' if total else ""
        sections += f'<h2 id="{bid}">{label} <span class="band-prog" data-band="{bid}"></span></h2>{tot}<div class="qgrid" data-bandgrid="{bid}">{cards}</div>'
    C = G["citizen"]
    crow = "".join(f'<tr><td data-th="Quest"><b>{e(n)}</b></td><td data-th="Level">{lv}</td><td data-th="Reward">{e(r)}</td><td data-th="Notes">{e(nt)}</td></tr>' for n, lv, r, nt in C["rows"])
    legend = "".join(f'<span class="verdict {c}">{l}</span>' for l, c in VERDICT.values())
    body = f"""<h1>MapleStory Classic Quest Guide: Best Quests by Level</h1>
<p class="lede">The quests worth your time from level 1 to 65, with the EXP each one is worth at the level you can start it, the rewards, and the ones to skip.</p>
{guide_stamp("Quest tracker data, launch week. ")}
<div class="toc">{chips}<a href="#citizenship">Citizenship</a><a href="#faq">FAQ</a></div>
<p class="legend">{legend}</p>
<p class="callout" style="margin-top:12px">✅ Tap <b>Step-by-step guide</b> on any quest for every NPC, item, monster and reward, in order. Tap <b>Mark done</b> as you finish quests; your progress stays on this device. The bar under each quest shows its EXP as a share of the level you'd be doing it at.</p>
{sections}
<h2 id="citizenship">Citizenship quests</h2><p>{e(C["intro"])}</p>
<p class="callout" style="margin:10px 0 12px">🏠 Grades, donation items, every story arc and housing: <a href="/citizenship/">Citizenship guide</a>.</p>
<table class="tbl"><thead><tr><th>Quest</th><th>Level</th><th>Reward</th><th>Notes</th></tr></thead><tbody>{crow}</tbody></table>
<p class="callout" style="margin-top:12px">Your 2nd job advancement quests at level 30 pay 9,560 EXP too. See <a href="/job-advancement/">Job up</a>.</p>
{srcs(G["questSrc"])}
<h2 id="faq">FAQ</h2>{faq_html(G["questFaq"])}"""
    side = '<div class="card"><h3>Must-do quests</h3>' + "".join(f'<p><a href="{qhref(q)}">{e(q["name"])}</a> <span class="muted">Lv {q["lv"]}</span></p>' for q in G["quests"] if q["verdict"] == "must" and not (QGB.get(q["name"]) or {}).get("status") == "future") + "</div>"
    write("/quests/", page("/quests/", "MapleStory Classic Quest Guide: Best Quests by Level (1–65)",
                           "The best MapleStory Classic quests by level, from Maple Island to level 65: EXP, mesos and rewards, citizenship quests and which ones to skip.", body,
                           crumbs=[("/", "Guide"), (None, "Quests")], schema=faq_schema(G["questFaq"]), side_extra=side))

def quest_title(name):
    for t in (f"{name} Quest Guide: MapleStory Classic Walkthrough", f"{name}: MapleStory Classic Quest Guide", f"{name} Quest Guide (MapleStory Classic)"):
        if len(t) <= 62: return t
    return f"{name} | MapleStory Classic"

def build_quest_pages():
    """One step-by-step page per quest: where to start, what to bring, every step, rewards and tips."""
    toNext = EXP["toNext"]
    order = [q for q in G["quests"] if q["name"] in QGB]
    for i, card in enumerate(order):
        g = QGB[card["name"]]
        key, path = qslug(card["name"]), f'/quests/{g["slug"]}/'
        lv, r, st = g["level"] or card["lv"], g["rewards"], g["start"]
        future = g["status"] == "future"
        vl, vc = VERDICT["future" if future else card["verdict"]]
        need = toNext[min(lv, len(toNext)) - 1]
        ratio = (r["exp"] or 0) / need
        share = ((f"{ratio:.1f} levels" if ratio >= 1 else f"{round(ratio * 100)}% of a level") + f" at Lv {lv}") if r["exp"] else ""
        if lv < 8 and r["exp"]: share = "enough to reach about Lv 8"
        where = st["map"] + (f", {st['town']}" if st["town"] and st["town"] not in st["map"] else "")

        # The 30-second version
        need_bits = [f'{c["count"]:,} {c["name"]}' if c["count"] else c["name"] for c in g["collect"] if c["from"]][:4]
        kill_bits = [f'{k["count"]:,} {k["monster"]}' if k["count"] else k["monster"] for k in g["kills"]][:3]
        got = []
        for x in g["cardRewards"]:
            n, _, lab = x.partition("|")
            got.append(f"{n} {lab}" if lab.startswith("x") else (lab or n))
        money = ", ".join(b for b in [f'{r["exp"]:,} EXP' if r["exp"] else "", f'{r["mesos"]:,} mesos' if r["mesos"] else ""] if b)
        musts = [f"<b>Start:</b> talk to {e(st['npc'])} in {e(where)}{f' at Lv {lv}' if lv > 1 else ''}."]
        if need_bits: musts.append("<b>Collect:</b> " + e(", ".join(need_bits)) + ".")
        if kill_bits: musts.append("<b>Defeat:</b> " + e(", ".join(kill_bits)) + ".")
        musts.append("<b>You get:</b> " + e(", ".join(([money] if money else []) + got)) + ".")

        fame = f' · +{r["fame"]} fame' if r.get("fame") else ""
        exp_b = f'{r["exp"]:,}' if r["exp"] else "–"
        mes_b = f'{r["mesos"]:,}' if r["mesos"] else "–"
        facts = (f'<div class="facts qfacts"><div><b>Lv {lv}+</b><span>{e(g["jobs"] or "All jobs")}</span></div>'
                 f'<div><b>{e(st["npc"])}</b><span>{e(st["town"] or st["map"])}</span></div>'
                 f'<div><b>{exp_b}</b><span>EXP{(" · " + e(share)) if share else ""}</span></div>'
                 f'<div><b>{mes_b}</b><span>mesos{fame}</span></div></div>')

        sid = st.get("npcId") or (card["npcId"] if st["npc"] == card["npc"] else None)
        sprite = who(sid, st["npc"]) if sid else ""
        dirs = f'<p>{e(st["directions"])}</p>' if st["directions"] else ""
        start = (f'<h2 id="start">Where to start</h2><div class="qstart">{sprite}<div><p><b>{e(st["npc"])}</b> · {e(where)}</p>{dirs}</div></div>'
                 + go_html(st["map"], tip=False))
        pre = ('<h2 id="before">Before you start</h2><ul class="qtips">' + "".join(f"<li>{e(x)}</li>" for x in g["prereqs"]) + "</ul>") if g["prereqs"] else ""
        chain = ""
        if len(g["chain"]) > 1:
            chain = (f'<p class="qchain"><b>This guide covers {len(g["chain"])} quests:</b> '
                     + " › ".join(e(c["name"]) + (f' <span class="muted">(Lv {c["level"]})</span>' if c.get("level") and len({x.get("level") for x in g["chain"]}) > 1 else "") for c in g["chain"]) + "</p>")

        def src_cell(froms, note):
            out = ""
            for f in froms:
                maps = (": " + e(", ".join(f["maps"]))) if f["maps"] else ""
                out += f'<span class="qsrc">{mob_img(f["monster"], "msm")}<span><b>{e(f["monster"])}</b>{maps}</span></span>'
            return out + (f'<span class="qnote2">{e(note)}</span>' if note else "") or "–"
        rows = "".join(
            f'<tr><td data-th="Item"><span class="rw">{gicon(c["name"])}<span><b>{e(c["name"])}</b></span></span></td>'
            f'<td data-th="How many" class="{"qn" if c["count"] else "qn0"}"><b>{format(c["count"], ",") if c["count"] else "–"}</b></td><td data-th="Where to get it">{src_cell(c["from"], c["note"])}</td></tr>'
            for c in g["collect"])
        krows = "".join(
            f'<tr><td data-th="Monster"><span class="rw">{mob_img(k["monster"], "msm")}<span><b>{e(k["monster"])}</b></span></span></td>'
            f'<td data-th="How many" class="{"qn" if k["count"] else "qn0"}"><b>{format(k["count"], ",") if k["count"] else "–"}</b></td><td data-th="Where">{e(", ".join(k["maps"])) or "–"}</td></tr>'
            for k in g["kills"])
        hunt = []
        for nm in [m for c in g["collect"] for f in c["from"] for m in f["maps"]] + [m for k in g["kills"] for m in k["maps"]]:
            if nm in DIR["maps"] and nm not in hunt and nm != st["map"]: hunt.append(nm)
        gos = "".join(go_html(nm, lead=f"<b>{e(nm)}:</b> ", tip=False) for nm in hunt[:3])
        needs = ""
        if rows or krows:
            needs = '<h2 id="need">What you need</h2>'
            if rows: needs += f'<table class="tbl qneed"><thead><tr><th>Item</th><th>How many</th><th>Where to get it</th></tr></thead><tbody>{rows}</tbody></table>'
            if krows: needs += f'<h3 class="qh3">Monsters to defeat</h3><table class="tbl qneed"><thead><tr><th>Monster</th><th>How many</th><th>Where</th></tr></thead><tbody>{krows}</tbody></table>'
            if gos: needs += f'<h3 class="qh3">Getting to the hunting spots</h3>{gos}'

        steps = ""
        for n, x in enumerate(g["steps"]):
            meta = " · ".join(e(v) for v in (x["npc"], x["map"]) if v)
            meta = f'<span class="qs-m">{meta}</span>' if meta else ""
            steps += f'<li class="qstep"><label><span><span class="qs-t">{e(x["text"])}</span>{meta}</span><input type="checkbox" aria-label="Step {n + 1} done"></label></li>'
        stepsec = (f'<section data-qpage="{key}"><h2 id="steps">Step by step <span class="qp-prog" aria-live="polite"></span></h2>'
                   '<p class="muted qhint">Tick each step as you finish it. Your ticks stay on this device.</p>'
                   f'<ol class="steps qsteps">{steps}</ol>'
                   '<p class="qp-act"><button type="button" class="q-done qp-done" aria-pressed="false">Mark quest done</button></p></section>')

        def rline(it):
            tags = " ".join(t for t, on in (("choose one", it.get("choice")), ("random", it.get("random"))) if on)
            cnt = f' x{it["count"]:,}' if (it.get("count") or 0) > 1 else ""
            tag = f' <span class="chip c-tag">{e(tags)}</span>' if tags else ""
            note = f'<small>{e(it["note"])}</small>' if it.get("note") else ""
            return f'<li><span class="rw">{gicon(it["name"])}<span><b>{e(it["name"])}{cnt}</b>{tag}{note}</span></span></li>'
        nq = len(g["chain"]) or 1
        each = " each" if r["other"].startswith("Numbers are per") else ""
        rew = (f'<h2 id="rewards">Rewards</h2><div class="facts stats qrw"><div class="hot"><b>{exp_b}</b><span>EXP{each}</span></div>'
               f'<div><b>{mes_b}</b><span>Mesos{each}</span></div><div><b>{("+" + str(r["fame"])) if r.get("fame") else "–"}</b><span>Fame</span></div>'
               f'<div><b>{nq}</b><span>Quest{"s" if nq > 1 else ""}</span></div></div>'
               + (f'<p class="muted">That EXP is {e(share)}.</p>' if share else "")
               + (f'<ul class="qrlist">{"".join(rline(it) for it in r["items"])}</ul>' if r["items"] else "")
               + (f'<p>{e(r["other"])}</p>' if r["other"] else ""))

        miss = f'<p class="callout warn" style="margin-top:14px"><b>Don&#39;t miss:</b> {e(g["missable"])}</p>' if g["missable"] else ""
        fut = (f'<p class="callout warn" style="margin-top:14px"><b>Not out yet.</b> This quest opens {e(g["opens"] or "with the Forgotten Hollow update")}. '
               'The steps come from the quest data already in the game, so details may change when it goes live.</p>') if future else ""
        tips = ('<h2 id="tips">Tips</h2><ul class="qtips">' + "".join(f"<li>{e(t)}</li>" for t in g["tips"]) + "</ul>") if g["tips"] else ""
        unk = ('<h2 id="unconfirmed">Still being confirmed</h2><ul class="qtips">' + "".join(f"<li>{e(t)}</li>" for t in g["unknowns"])
               + '</ul><p class="muted">We update this page as players confirm these. Know the answer? Use the feedback box below.</p>') if g["unknowns"] else ""
        prev, nxt = (order[i - 1] if i else None), (order[i + 1] if i + 1 < len(order) else None)
        qnav = ('<nav class="qnav" aria-label="More quests">'
                + (f'<a href="{qhref(prev)}"><span>← Lv {prev["lv"]}</span>{e(prev["name"])}</a>' if prev else "<span></span>")
                + '<a class="all" href="/quests/">All quests</a>'
                + (f'<a class="nx" href="{qhref(nxt)}"><span>Lv {nxt["lv"]} →</span>{e(nxt["name"])}</a>' if nxt else "<span></span>")
                + "</nav>")

        title = quest_title(card["name"])
        desc = f"How to do {card['name']} in MapleStory Classic, step by step: start at {st['npc']} in {st['town'] or st['map']} (Lv {lv}), what to bring, where it drops and every reward."
        if len(desc) > 160: desc = f"{card['name']} in MapleStory Classic, step by step: where to start, what to bring, every step and every reward."
        ingame = f'{e(g["inGame"]).rstrip(".")}. ' if g["inGame"] else ""
        body = (f'<h1>{e(card["name"])}: step-by-step guide</h1><p class="lede">{e(g["summary"])}</p>'
                f'<p class="stamp" data-pagefind-ignore><b>✓ Checked {QG["checked"]}</b><span>{ingame}How sure we are: {conf(g["conf"])}</span></p>'
                f'<p class="qverdict"><span class="verdict {vc}">{vl}</span></p>{fut}{facts}'
                f'<h2 id="quick">The 30-second version</h2><ol class="musts">{"".join(f"<li>{m}</li>" for m in musts)}</ol>'
                f'{miss}{start}{pre}{chain}{needs}{stepsec}{rew}{tips}{unk}{qnav}{srcs(g["sources"])}')
        side = (f'<div class="card qside"><h3>At a glance</h3><p><span class="verdict {vc}">{vl}</span> {conf(g["conf"])}</p>'
                f'<p><b>Level:</b> {lv}+</p><p><b>Start:</b> {e(st["npc"])}, {e(st["town"] or st["map"])}</p><p><b>Steps:</b> {len(g["steps"])}</p>'
                '<p class="toc-s"><a href="#quick">30-second version</a><a href="#start">Where to start</a>'
                + ('<a href="#need">What you need</a>' if needs else "") + '<a href="#steps">Step by step</a><a href="#rewards">Rewards</a>'
                + ('<a href="#tips">Tips</a>' if tips else "") + '</p><p><a href="/quests/">← All quests</a></p></div>')
        write(path, page(path, title, desc, body, crumbs=[("/", "Guide"), ("/quests/", "Quests"), (None, card["name"])],
                         schema={"@context": "https://schema.org", "@type": "Article", "headline": title}, side_extra=side))

def build_money():
    Mo = G["money"]
    bid = {b["id"]: b for b in G["bosses"]}
    stages = "".join(f'<div class="card mstage"><span class="lvpill">{e(s["lv"])}</span><h3>{e(s["title"])}</h3><ul>{"".join(f"<li>{e(x)}</li>" for x in s["items"])}</ul></div>' for s in Mo["stages"])
    market = "".join(f'<tr><td data-th="Item"><span class="rw">{gicon(n)}<span><b>{e(n)}</b>{("<small class=show-sm>" + e(note) + "</small>") if note else ""}</span></span></td><td data-th="Sold for"><b>{p:,}</b></td><td class="hide-sm" data-th="Note">{e(note)}</td></tr>' for n, p, note in Mo["market"])
    trends = "".join(f'<div class="trend {d}"><b>{e(v)}</b><span>{e(n)}</span></div>' for n, v, d in Mo["trends"])
    snap = "".join(f'<tr><td data-th="Item"><span class="rw">{gicon(n)}<span><b>{e(n.split("|")[-1])}</b>{("<small class=show-sm>" + e(note) + "</small>") if note else ""}</span></span></td><td data-th="Mesos"><b>{p:,}</b></td><td class="hide-sm" data-th="Note">{e(note)}</td></tr>' for n, p, note in Mo.get("snapshot", []))
    mobid = {"Orange Mushroom": 1210102, "Stump": 130100, "Red Snail": 130101, "Slime": 210100}
    vendor = "".join(f'<tr><td data-th="Drop"><span class="rw">{gicon(n)}<b>{e(n)}</b></span></td><td data-th="Dropped by">{_img(mob_src(mobid[m]), m, "sprite sm")}{e(m)}</td><td data-th="NPC pays"><b>{p:,}</b></td></tr>' for n, m, p in Mo["vendor"])
    have = {qslug(q["name"]) for q in G["quests"]}
    qa = lambda n: f'<a href="{qhref(n.split(" (")[0])}"><b>{e(n)}</b></a>' if qslug(n.split(" (")[0]) in have else f'<a href="/quests/#citizenship"><b>{e(n)}</b></a>'
    quests = "".join(f'<tr><td data-th="Quest">{qa(n)}</td><td data-th="Level">{lv}</td><td data-th="Mesos"><b>{m:,}</b></td></tr>' for n, lv, m in Mo["quests"])
    bosses = "".join(f'<a class="card bosscard" href="/bosses/#{i}">{boss_sprite(bid[i], "sprite")}<h3>{e(n)}</h3><p><b>{e(v)}</b> mesos per kill</p></a>' for n, i, v in Mo["bosses"])
    crafts = "".join(f'<tr><td data-th="Craft"><span class="rw">{gicon(n.split(" /")[0].replace(" x500", ""))}<b>{e(n)}</b></span></td><td data-th="Profession">{e(p)}</td><td data-th="Profit per craft"><b>{e(v)}</b></td></tr>' for n, p, v in Mo["crafts"])
    body = f"""<h1>MapleStory Classic Money Making Guide: How to Make Mesos</h1>
<p class="lede">How to make mesos at every stage of your run: what to sell, what to keep, which quests pay best, and which bosses are worth farming.</p>
{guide_stamp("Free Market data from launch week. ")}
<p class="callout" style="margin-top:12px">🔎 <b>Selling something right now?</b> The <a href="/prices/">price check</a> takes you straight to its live price, and <a href="/prices/#farms">this week's money farms</a> tell you which mobs to hunt.</p>
<div class="toc"><a href="#stages">By level</a><a href="#market">Prices</a><a href="#trends">Trends</a><a href="#vendor">Vendor list</a><a href="#quests">Meso quests</a><a href="#bosses">Bosses</a><a href="#crafting">Crafting</a><a href="#merch">Merching</a><a href="#faq">FAQ</a></div>
<h2 id="stages">Making mesos by level</h2><div class="grid">{stages}</div>
<h2 id="market">What sells on the Free Market</h2><table class="tbl compact"><thead><tr><th>Item</th><th>Mesos</th><th class="hide-sm">Note</th></tr></thead><tbody>{market}</tbody></table>
<p class="muted" style="margin-top:8px">{e(Mo["marketNote"])}</p>
<h3 style="margin-top:18px">Latest snapshot</h3><table class="tbl compact"><thead><tr><th>Item</th><th>Mesos</th><th class="hide-sm">Note</th></tr></thead><tbody>{snap}</tbody></table><p class="muted" style="margin-top:8px">{e(Mo.get("snapshotNote", ""))}</p>
<h2 id="trends">Where prices are heading</h2><p class="muted" style="margin-bottom:10px">{e(Mo.get("trendsNote", ""))}</p><div class="trends">{trends}</div><p class="callout" style="margin-top:12px">{e(Mo["trendTip"])}</p>
<h2 id="vendor">Early drops worth vendoring</h2><p>Many drops sell back to NPCs for very little in Classic, but these early weapons pay well. Keep one you can use, then sell the duplicates.</p>
<table class="tbl compact"><thead><tr><th>Drop</th><th>Dropped by</th><th>NPC pays</th></tr></thead><tbody>{vendor}</tbody></table>
<h2 id="quests">Quests that pay the most mesos</h2><table class="tbl compact"><thead><tr><th>Quest</th><th>Level</th><th>Mesos</th></tr></thead><tbody>{quests}</tbody></table>
<h2 id="bosses">Bosses worth farming</h2><div class="grid">{bosses}</div>
<h2 id="crafting">Crafting for profit</h2><table class="tbl compact"><thead><tr><th>Craft</th><th>Profession</th><th>Profit per craft</th></tr></thead><tbody>{crafts}</tbody></table>
<p class="muted" style="margin-top:8px">Based on NPC sell-back and closed-test numbers. Check Free Market prices before you craft in bulk. See the <a href="/crafting/">crafting guide</a> for what to keep.</p>
<h2 id="merch">Merching basics</h2><p class="callout">🏪 Store permits, pricing, scams and bots: <a href="/free-market/">Free Market guide</a>.</p><ul>{"".join(f"<li>{e(x)}</li>" for x in Mo["merch"])}</ul>
<div class="callout warn"><b>Don't:</b><ul style="margin:6px 0 0">{"".join(f"<li>{e(x)}</li>" for x in Mo["dont"])}</ul></div>
{srcs(Mo["src"])}
<h2 id="faq">FAQ</h2>{faq_html(Mo["faq"])}"""
    side = '<div class="card"><h3>Quick money</h3><p><a href="/prices/">Price check (this week)</a></p><p><a href="/prices/#farms">Money farms this week</a></p><p><a href="#market">Launch-week prices</a></p><p><a href="#quests">Meso quests</a></p><p><a href="/bosses/">Boss timers</a></p><p><a href="/crafting/">What to keep</a></p></div>'
    write("/money-making/", page("/money-making/", "MapleStory Classic Money Making Guide: Best Ways to Make Mesos",
                                 "How to make mesos in MapleStory Classic: Free Market prices, what to sell and keep, the best meso quests, boss meso drops, crafting profit and merching tips.", body,
                                 crumbs=[("/", "Guide"), (None, "Money making")], schema=faq_schema(Mo["faq"]), side_extra=side))

PC_ITEMS = []  # filled by build_prices, read by the search index

def short(s, n=110):
    """Trim a context line for search results at a word boundary."""
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0].rstrip(",;:·(") + "…"

def build_prices():
    P = PRICES
    for k, v in CRAFT["items"].items():
        if v.get("icon"): G["icons"].setdefault(k, v["icon"])
    icons = dict(G["icons"])
    uses = {}
    for pr in CRAFT["professions"]:
        for k in pr.get("keep", []):
            uses.setdefault(k[0], []).append(pr["name"])
    quoted = {n: v for n, v in P["prices"].items()}
    names = sorted(set(icons) | set(CRAFT["items"]) | set(quoted), key=str.lower)
    items = [{"n": n, "ic": icons.get(n), "from": CRAFT["items"].get(n, {}).get("from", []), "use": uses.get(n, []), "p": quoted.get(n)} for n in names]
    PC_ITEMS[:] = items
    pdata = {"items": items, "sites": P["sites"], "week": P["week"], "api": API}
    chips = "".join(f'<button type="button" class="pc-chip" data-item="{e(n)}">{gicon(n)}{e(n)}</button>' for n in P["popular"])
    mobs = CRAFT["mobs"]
    farms = ""
    for i, f in enumerate(P["picks"], 1):
        drops = "".join(f'<span class="rw">{gicon(d)}<span><b>{e(d)}</b><small>{"~" + format(quoted[d][0], ",") + " mesos" if d in quoted else "price: check"}</small></span></span>' for d in f["drops"])
        spr = _img(mob_src(mobs[f["mob"]]), f["mob"], "sprite") if f["mob"] in mobs else ""
        farms += f'''<li class="farm"><span class="farm-n">{i}</span><div class="farm-art">{spr}</div><div class="farm-body">
<h3>{e(f["title"])}</h3><p class="meta">{e(f["mob"])}, lv {f["lv"]} · {e(f["map"])} · good from lv {f["from"]}</p>
<div class="rws">{drops}</div><p>{e(f["why"])}</p>{go_html(f["map"])}</div></li>'''
    sites = "".join(f'<li><a href="{u}" target="_blank" rel="noopener"><b>{e(n)}</b></a> <span class="muted">{e(d)}</span></li>' for n, u, d in P["sites"])
    tips = "".join(f"<li>{e(t)}</li>" for t in P["tips"])
    plist = "".join(f'<tr><td data-th="Item"><span class="rw">{gicon(n)}<b>{e(n)}</b></span></td><td data-th="Usual price"><b>{v[0]:,}</b>{" <small class=muted>few sales</small>" if "few sales" in v[1] else ""}</td></tr>' for n, v in sorted(quoted.items(), key=lambda kv: -kv[1][0]))
    body = f'''<h1>MapleStory Classic Price Check: What's It Worth?</h1>
<p class="lede">Type any item and jump straight to its live price. Then see which mobs are worth farming for mesos this week.</p>
<div class="pcbox" id="pc">
<label for="pc-q" class="pc-l">🔎 What are you selling?</label>
<input id="pc-q" type="search" placeholder="Try Iron Ore or Squishy Shoes" autocomplete="off" spellcheck="false">
<div class="pc-out" id="pc-out" aria-live="polite"></div>
<p class="pc-pop">Popular this week</p>
<div class="pc-chips" role="group" aria-label="Popular items">{chips}</div>
<script type="application/json" id="pc-data">{json.dumps(pdata).replace("</", "<\\/")}</script>
</div>
<p class="muted" style="margin-top:10px">Tapping a price button opens that site and copies the item name, so you can paste it straight into their search.</p>
<h2 id="farms">This week's money farms 💰</h2>
<p class="lede" style="margin-top:0">Week of {e(P["week"])}. These mobs drop the items selling for the most right now, and you can reach them early.</p>
<ol class="farms">{farms}</ol>
<p class="go-credit">{e(P["note"])} Prices: <a href="{P["sourceUrl"]}" target="_blank" rel="noopener">{e(P["source"])}</a>, usual sold price over the last 24 hours on {e(P["week"])}.</p>
<h2 id="list">This week's prices, most valuable first</h2>
<p>Every price we quote, so you can scan your inventory in one go. These are the usual sold prices on NiaMeowDB on {e(P["week"])}. For anything not listed, use the search box up top.</p>
<details class="pc-list"><summary>Show all {len(quoted)} prices</summary><table class="tbl compact"><thead><tr><th>Item</th><th>Mesos</th></tr></thead><tbody>{plist}</tbody></table></details>
<h2 id="tips">Price check like a pro</h2><ol class="musts">{tips}</ol>
<h2 id="sites">Where the live prices come from</h2><ul class="pc-sites">{sites}</ul>
<p class="muted">We don't copy their data. The buttons send you to them, and the few prices quoted on this page link back to the source.</p>
<p class="callout" style="margin-top:16px">💰 Want the bigger picture? <a href="/money-making/">How to make mesos</a> and <a href="/free-market/">selling on the Free Market</a>.</p>'''
    write("/prices/", page("/prices/", "MapleStory Classic Price Check: Item Prices & Money Farms",
                           "Check what any MapleStory Classic item is worth in one tap, plus this week's best mobs to farm for mesos, with directions from town.", body,
                           crumbs=[("/", "Guide"), (None, "Price check")]))

EVENT_AT = {"The Journey Begins": "2026-10-21T18:00:00Z", "Housing": "2026-10-21T18:00:00Z", "Mark of the Beta": "2026-10-21T18:00:00Z",
            "Halloween": "2026-10-28T00:00:00Z", "GM events": "2026-10-22T00:00:00Z", "Excavation Site and Stumpy": "2026-10-21T18:00:00Z", "Forgotten Hollow": "2026-11-18T16:00:00Z", "Moon Bunny's Rice Cake": "2026-11-18T16:00:00Z",
            "Guilds, Hollow PQ and Happyville": "2026-12-09T16:00:00Z"}

def build_news():
    N = G["news"]
    facts = "".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in N["launch"])
    tips = "".join(f"<li>{e(t)}</li>" for t in N["tips"])
    evts = ""
    for ev in N["events"]:
        at = EVENT_AT.get(ev["name"])
        when = f'<span class="tag when"{f" data-at={chr(34)}{at}{chr(34)}" if at else ""}>{e(ev["when"])}</span>'
        lv = f'<span class="tag">{e(ev["lv"])}</span>' if ev["lv"] else ""
        evts += f'<article class="card evt" id="e-{qslug(ev["name"])}"><div class="evt-top"><span class="evt-emo" aria-hidden="true">{ev["emoji"]}</span><span class="evt-live" aria-live="polite"></span></div><h3>{e(ev["name"])} {conf(ev["conf"])}</h3><p class="evt-meta">{when}{lv}</p><p>{e(ev["text"])}</p>{f'<a class="evt-go" href="{EVENT_LINK[ev["name"]]}">Full guide →</a>' if ev["name"] in EVENT_LINK else ""}</article>'
    dl = "".join(f'<tr><td data-th="When"><b>{e(d)}</b></td><td data-th="What">{e(t)}</td></tr>' for d, t in N["deadlines"])
    rules = "".join(f"<li>{e(r)}</li>" for r in N["rules"])
    patches = "".join(f'<article class="upd" id="p{e(pn["date"])}"><p class="upd-d"><time datetime="{e(pn["date"])}">{date.fromisoformat(pn["date"]).strftime("%b %-d, %Y")}</time></p><h3>{e(pn["title"])}</h3><ul>' + "".join(f"<li>{e(x)}</li>" for x in pn["items"]) + "</ul></article>" for pn in reversed(N["patches"]))
    body = f"""<h1>MapleStory Classic News: Launch Day, Events &amp; Patch Notes</h1>
<p class="lede">Everything that's changed since Founder's Access opened on Oct 6, what's coming next, and what to know before you log in on launch day.</p>
{guide_stamp("Official notes and Nexon Discord posts, via community recaps. ")}
<div class="toc"><a href="#launch">Launch day</a><a href="#events">Events</a><a href="#deadlines">Deadlines</a><a href="#rules">Rule changes</a><a href="#patches">Patch notes</a><a href="#faq">FAQ</a></div>
<h2 id="launch">Grand Launch: what to know</h2><div class="facts">{facts}</div>
<ol class="musts" style="margin-top:16px">{tips}</ol>
<h2 id="events">Events and what's coming</h2><p class="muted" style="margin-bottom:12px">Dates are from Nexon's MapleStory Fest roadmap (Oct 17) and can move. Event details marked "Likely" come from the test client.</p><div class="grid">{evts}</div>
<h2 id="deadlines">Deadlines</h2><table class="tbl compact"><thead><tr><th>When</th><th>What</th></tr></thead><tbody>{dl}</tbody></table>
<h2 id="rules">Rule changes worth knowing</h2><ul>{rules}</ul>
<h2 id="patches">Patch notes since Founder's Access</h2><p class="muted" style="margin-bottom:6px">Newest first. Nexon's Grand Launch notes (client v1.0.0) come out Oct 21; we'll add them here.</p>{patches}
{srcs(N["src"])}
<h2 id="faq">FAQ</h2>{faq_html(N["faq"])}"""
    side = '<div class="card"><h3>Coming up</h3>' + "".join(f'<p><a href="#e-{qslug(ev["name"])}">{ev["emoji"]} {e(ev["name"])}</a> <span class="muted">{e(ev["when"])}</span></p>' for ev in N["events"]) + "</div>"
    write("/news/", page("/news/", "MapleStory Classic News: Patch Notes, Events & Key Dates",
                         "MapleStory Classic World news: every patch since Founder's Access, live events, Cash Shop deadlines, Forgotten Hollow on Nov 18 and guilds on Dec 9.", body,
                         crumbs=[("/", "Guide"), (None, "News")], schema=faq_schema(N["faq"]), side_extra=side))

L = load("launch.json")
G["icons"].update(L["icons"])
EVENT_LINK = {"The Journey Begins": "/events/#journey", "Housing": "/citizenship/#housing", "Mark of the Beta": "/events/#mark", "Halloween": "/events/#halloween"}

def deadline_bar():
    items = sorted(L["deadlines"], key=lambda d: d["end"])
    main = next(d for d in items if d.get("main"))
    rest = "".join(f'<li data-dl><b>{e(d["when"])}</b><span class="dl-left" data-left="{d["end"]}"></span><span class="dl-what">{e(d["what"])}</span></li>' for d in items if not d.get("main"))
    return f'''<div class="dlbar" aria-label="Deadlines"><div class="dl-main" data-dl><span class="dl-emo" aria-hidden="true">🎁</span><div><b>{e(main["what"])} by {e(main["when"].split(",")[0])}</b><span>{e(main["tip"])}</span></div><span class="dl-left" data-left="{main["end"]}"></span></div>
<ul class="dl-list">{rest}</ul></div>'''

def build_citizenship():
    C = L["citizenship"]
    H = C["housing"]
    quick = "".join(f"<li>{e(x)}</li>" for x in C["quick"])
    towns = ""
    for t in C["towns"]:
        perks = "".join(f'<div class="kp sm">{gicon(p)}<div><b>{e(p.split("|")[-1])}</b><span>{e(d)}</span></div></div>' for p, d in t["perks"])
        faces = "".join(f'<figure class="npcfig">{npc_img(i, n, "")}<figcaption>{e(n)}</figcaption></figure>' for i, n in t["neighbors"])
        towns += f'''<article class="card town" id="{t["id"]}"><p class="town-h"><span aria-hidden="true">{t["emoji"]}</span><b>{e(t["name"])}</b><span class="tag">{e(t["best"])}</span></p>
<p class="meta">Sign up: {e(t["clerk"])} · House: {e(t["home"])}</p><div class="perks">{perks}</div>
<p class="faces-h">Neighbors you'll greet</p><div class="faces">{faces}</div><p class="muted" style="margin:0">VIP neighbors from grade 5: {e(t["vip"])}.</p></article>'''
    grows = "".join(f'<tr data-g="{g}"><td data-th="Grade"><b>{g}</b><span class="gname">{e(n)}</span></td><td data-th="Level">{lv}</td><td data-th="Points">{pts:,}</td><td class="hide-sm" data-th="Discount">{d}</td><td class="hide-sm" data-th="Storage fee">{fee}</td><td data-th="Unlocks">{e(u)}</td></tr>' for g, n, lv, pts, d, fee, u, _ in C["grades"])
    opts = "".join(f'<option value="{g}">Grade {g}: {e(n)}</option>' for g, n, *_ in C["grades"])
    don = lambda lst: "".join(f'<span class="rw">{gicon(n)}<span>{e(n)}<small>Grade {g} · +{p:,}</small></span></span>' for n, g, p in lst)
    arcs = "".join(f'<tr><td data-th="Level"><b>Lv {lv}</b><span class="gname">Grade {g}</span></td><td data-th="Henesys"><b>{e(ha)}</b><span class="gname">{e(hr)}</span></td><td data-th="Kerning"><b>{e(ka)}</b><span class="gname">{e(kr)}</span></td></tr>' for lv, g, ha, hr, ka, kr in C["arcs"])
    hfacts = "".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in H["facts"])
    homes = "".join(f'<div class="card"><h3>{e(n)}</h3><p>{e(t)}</p></div>' for _, n, t in H["homes"])
    place = "".join(f'<div class="card"><span class="evt-emo" aria-hidden="true">{em}</span><h3>{e(n)}</h3><p>{e(t)}</p></div>' for em, n, t in H["place"])
    hnpc = "".join(f'<tr><td data-th="Who"><b>{e(r)}</b></td><td data-th="Henesys">{e(a)}</td><td data-th="Kerning">{e(b)}</td></tr>' for r, a, b in H["npcs"])
    body = f"""<h1>MapleStory Classic Citizenship &amp; Housing Guide</h1>
<p class="lede">Pick a town, say hi to the neighbors every day, and work your way up to a house of your own. Here's every grade, what it unlocks and the fastest way up.</p>
{guide_stamp("Launch client data via NiaMeowDB and maplestory.quest. ")}
<div class="toc"><a href="#start">Start</a><a href="#town">Which town?</a><a href="#grades">Grades</a><a href="#points">Earning points</a><a href="#stories">Story quests</a><a href="#housing">Housing</a><a href="#gotchas">Gotchas</a><a href="#faq">FAQ</a></div>
<h2 id="start">The 30-second version</h2><ol class="musts">{quick}</ol>
<h2 id="town">Henesys or Kerning?</h2><div class="grid two">{towns}</div>
<p class="callout" style="margin-top:14px">{e(C["both"])}</p>
<h2 id="grades">The 10 grades</h2>
<div class="gpick"><label for="gsel">I'm at</label><select id="gsel"><option value="0">Not a citizen yet</option>{opts}</select><p id="gout" aria-live="polite"></p></div>
<table class="tbl compact grades"><thead><tr><th>Grade</th><th>Lv</th><th>Points</th><th class="hide-sm">Discount</th><th class="hide-sm">Storage fee</th><th>Unlocks</th></tr></thead><tbody>{grows}</tbody></table>
<p class="muted" style="margin-top:8px">{e(C["gradeNote"])} Discounts cover cabs and some store items in your town. Storage fee is mesos per item (100 without citizenship).</p>
<script type="application/json" id="gdata">{json.dumps(C["grades"])}</script>
<h2 id="points">How to earn points</h2>
<h3>Every day: greet a neighbor</h3><p>{e(C["daily"])}</p>
<h3 style="margin-top:18px">Every week: donate 30 of one item</h3><p>{e(C["donateNote"])}</p>
<div class="grid two" style="margin-top:10px"><div class="card"><h3>🍄 Henesys donation pool</h3><div class="rws">{don(C["donations"]["henesys"])}</div></div><div class="card"><h3>🌃 Kerning donation pool</h3><div class="rws">{don(C["donations"]["kerning"])}</div></div></div>
<p class="callout" style="margin-top:14px">💡 Stash snail shells, mushroom caps and tails while you level. When the board asks for them, you're done in one click.</p>
<h2 id="stories">Story quests</h2><p>{e(C["arcNote"])}</p>
<table class="tbl compact"><thead><tr><th>Level</th><th>Henesys</th><th>Kerning</th></tr></thead><tbody>{arcs}</tbody></table>
<h2 id="housing">Housing 🏠</h2><p>Housing opens with Grand Launch on Oct 21. Get to grade 2 in Henesys or Kerning and you can buy a place in that town.</p>
<div class="facts">{hfacts}</div>
<div class="grid two" style="margin-top:14px">{homes}</div>
<h3 style="margin-top:20px">What you can put in it</h3><div class="grid">{place}</div>
<h3 style="margin-top:20px">Who to talk to</h3><table class="tbl compact"><thead><tr><th>Who</th><th>Henesys</th><th>Kerning</th></tr></thead><tbody>{hnpc}</tbody></table>
<ul style="margin-top:12px">{"".join(f"<li>{e(x)}</li>" for x in H["extra"])}</ul>
<div class="kp shoes">{gicon("Resident's Chair")}<div><b>Resident's Chair</b><span>{e(C["chair"].split(": ", 1)[1])}</span></div></div>
<p class="callout warn"><b>Still unknown:</b> {e(H["unknown"].replace("Not known yet: ", ""))}</p>
<h2 id="gotchas">Gotchas</h2><ul>{"".join(f"<li>{e(x)}</li>" for x in C["gotchas"])}</ul>
<p class="callout">📜 Want the rest of the best quests by level? See the <a href="/quests/">quest guide</a>.</p>
{srcs(C["src"])}
<h2 id="faq">FAQ</h2>{faq_html(C["faq"])}"""
    side = '<div class="card"><h3>Citizenship</h3><p><a href="#town">Henesys or Kerning?</a></p><p><a href="#grades">Grade planner</a></p><p><a href="#points">Donation items</a></p><p><a href="#housing">Housing</a></p></div>'
    write("/citizenship/", page("/citizenship/", "MapleStory Classic Citizenship & Housing: Grades and Houses",
                                "MapleStory Classic citizenship: Henesys or Kerning, all 10 grades and what they unlock, donation items, the Resident's Chair and buying a house.", body,
                                crumbs=[("/", "Guide"), (None, "Citizenship")], schema=faq_schema(C["faq"]), side_extra=side))

def build_events():
    V = L["events"]
    now = ""
    for ev in V["now"]:
        end = f' data-end="{ev["end"]}"' if ev["end"] else ""
        now += f'''<article class="card evt"><div class="evt-top"><span class="evt-emo" aria-hidden="true">{ev["emoji"]}</span><span class="evt-live" aria-live="polite"></span></div>
<h3>{e(ev["name"])} {conf(ev["conf"])}</h3><p class="evt-meta"><span class="tag when" data-at="{ev["at"]}"{end}>{e(ev["when"])}</span><span class="tag">{e(ev["lv"])}</span></p><p>{e(ev["blurb"])}</p><a class="evt-go" href="#{ev["id"]}">How to do it ↓</a></article>'''
    M = V["mark"]
    msteps = ""
    for i, s in enumerate(M["steps"], 1):
        art = npc_img(s["npc"], "", "sprite") if s["npc"] else (_img(mob_src(s["mob"]), "", "sprite") if s["mob"] else "")
        clue = f'<p class="clue">🔎 The clue: “…{e(s["clue"])}…”</p>' if s["clue"] else ""
        msteps += f'<li class="stage"><span class="sn">{i}</span><div><h3>{e(s["title"])}</h3>{f"<div class=sprites>{art}</div>" if art else ""}{clue}<p>{e(s["do"])}</p></div></li>'
    J = V["journey"]
    jfacts = "".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in J["facts"])
    jb = "".join(f'<button type="button" aria-pressed="false" aria-label="Gift {i}">{i}</button>' for i in range(1, 15))
    Hw = V["halloween"]
    hfacts = "".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in Hw["facts"])
    hsteps = ""
    for i, s in enumerate(Hw["steps"], 1):
        art = npc_img(s["npc"], "Malady", "sprite") if s.get("npc") else "".join(_img(mob_src(m), "", "sprite sm") for m in s.get("mobs", []))
        hsteps += f'<li class="stage"><span class="sn">{i}</span><div><h3>{e(s["title"])}</h3>{f"<div class=sprites>{art}</div>" if art else ""}<p>{e(s["do"])}</p></div></li>'
    maybe = "".join(rw(x) for x in Hw["maybe"])
    body = f"""<h1>MapleStory Classic Events: Mark of the Beta, Halloween &amp; Daily Gifts</h1>
<p class="lede">What's on in Classic World, how to finish each event fast, and what you get for it.</p>
{guide_stamp("Nexon's Grand Launch notes, plus quest steps from the game files. ")}
<div class="toc"><a href="#now">On now</a><a href="#mark">Mark of the Beta</a><a href="#journey">The Journey Begins</a><a href="#halloween">Halloween</a><a href="#faq">FAQ</a></div>
<h2 id="now">What's on</h2><div class="grid">{now}</div>
<p class="muted" style="margin-top:10px">Forgotten Hollow, Moon Bunny, guilds and the rest of the roadmap are on the <a href="/news/#events">News page</a>.</p>
<h2 id="mark">Mark of the Beta walkthrough 🗺️</h2><p>{e(M["intro"])}</p>
<ol class="stages">{msteps}</ol>
<div class="kp shoes">{gicon("Mark of the Beta")}<div><b>Your reward</b><span>{e(M["reward"])}</span></div></div>
<p class="muted">{e(M["note"])}</p><p class="callout">{e(M["rings"])}</p>
<h2 id="journey">The Journey Begins 🎁</h2><div class="npcs">{npc_img(9010000, "Maple Administrator")}</div>
<ol class="musts">{"".join(f"<li>{e(x)}</li>" for x in J["how"])}</ol>
<div class="facts" style="margin-top:14px">{jfacts}</div>
<p style="margin-top:14px">{e(J["gifts"])}</p>
<div class="jb" data-jb><p class="combo-h"><b>Tap a box each time you claim a gift</b><span id="jb-out" aria-live="polite"></span></p><div class="jb-g">{jb}</div></div>
<p class="muted" style="margin-top:8px">{e(J["note"])} Your boxes are saved on this device only.</p>
<h2 id="halloween">Malady's Halloween 🎃</h2><div class="facts">{hfacts}</div>
<ol class="stages" style="margin-top:16px">{hsteps}</ol>
<h3 style="margin-top:20px">Rewards and goodies</h3><div class="rws">{maybe}</div><p class="muted">{e(Hw["maybeNote"])}</p>
<h3 style="margin-top:18px">Tips</h3><ul>{"".join(f"<li>{e(x)}</li>" for x in Hw["tips"])}</ul>
<p class="callout warn">{e(Hw["note"])}</p>
{srcs(V["src"])}
<h2 id="faq">FAQ</h2>{faq_html(V["faq"])}"""
    side = '<div class="card"><h3>Events</h3>' + "".join(f'<p><a href="#{ev["id"]}">{ev["emoji"]} {e(ev["name"])}</a> <span class="muted">{e(ev["when"])}</span></p>' for ev in V["now"]) + '<p><a href="/news/">All news →</a></p></div>'
    write("/events/", page("/events/", "MapleStory Classic Events: Halloween, Mark of the Beta & Gifts",
                           "MapleStory Classic events: Malady's Halloween candy hunt (Oct 27 to Nov 18), a Mark of the Beta walkthrough and The Journey Begins daily gifts.", body,
                           crumbs=[("/", "Guide"), (None, "Events")], schema=faq_schema(V["faq"]), side_extra=side))

def build_market():
    Mk = L["market"]
    facts = "".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in Mk["facts"])
    permits = "".join(f'<tr><td data-th="Permit"><span class="rw">{gicon(n)}<span><b>{e(n)}</b><small class="show-sm">{e(note)}</small></span></span></td><td data-th="Cost"><b>{e(c)}</b></td><td data-th="Items">{i}</td><td class="hide-sm" data-th="Note">{e(d)} · {e(note)}</td></tr>' for n, c, d, i, note in Mk["permits"])
    li = lambda rows: "".join(f"<li><b>{e(a)}</b> <span class='muted'>{e(b)}</span></li>" for a, b in rows)
    scams = "".join(f'<div class="card"><span class="evt-emo" aria-hidden="true">{em}</span><h3>{e(n)}</h3><p>{e(t)}</p></div>' for em, n, t in Mk["scams"])
    B = Mk["bots"]
    body = f"""<h1>MapleStory Classic Free Market Guide: Selling, Prices &amp; Scams</h1>
<p class="lede">How to sell fast, price right, and keep your mesos (and your account) safe.</p>
{guide_stamp("Player-reported prices via NiaMeowDB, shop rules from item text. ")}
<div class="toc"><a href="#quick">Quick tips</a><a href="#how">How it works</a><a href="#shop">Your shop</a><a href="#sells">What sells</a><a href="#scams">Scams</a><a href="#bots">Bots &amp; bans</a><a href="#cash">NX to mesos</a><a href="#faq">FAQ</a></div>
<h2 id="quick">Sell like a pro</h2><ol class="musts">{"".join(f"<li>{e(x)}</li>" for x in Mk["quick"])}</ol>
<p class="callout" style="margin-top:12px">🔎 Price check: <a href="https://meowdb.com/msclassic/free-market" rel="nofollow noopener" target="_blank">NiaMeowDB's Free Market tracker</a> shows what items really sold for. Our own snapshot is on the <a href="/money-making/#market">mesos page</a>.</p>
<h2 id="how">How the Free Market works</h2><div class="facts">{facts}</div><ul style="margin-top:14px">{"".join(f"<li>{e(x)}</li>" for x in Mk["how"])}</ul>
<h2 id="shop">Opening your own shop</h2><table class="tbl compact"><thead><tr><th>Permit</th><th>Cost</th><th>Items</th><th class="hide-sm">Details</th></tr></thead><tbody>{permits}</tbody></table>
<p class="muted" style="margin-top:8px">A Regular permit costs about 22,000 mesos worth of NX at ~15 mesos per NX.</p>
<ul>{"".join(f"<li>{e(x)}</li>" for x in Mk["shopRules"])}</ul>
<h2 id="sells">Hot or not</h2><div class="grid two hotnot"><div class="card hot"><h3>🔥 Sells fast</h3><ul>{li(Mk["hot"])}</ul></div><div class="card not"><h3>🧊 Sits forever</h3><ul>{li(Mk["not"])}</ul></div></div>
<p class="muted" style="margin-top:8px">{e(Mk["hotNote"])} <a href="/money-making/#market">See the prices →</a></p>
<h2 id="scams">Scams to dodge</h2><div class="grid">{scams}</div>
<h2 id="bots">Bots, reports and bans</h2>
<p><b>Where they hang out:</b> {e(B["spots"])}</p>
<p><b>How to spot one:</b></p><ul>{"".join(f"<li>{e(x)}</li>" for x in B["signs"])}</ul>
<p><b>Report it:</b> {e(B["report"])}</p>
<p class="callout warn"><b>Don't buy mesos.</b> {e(B["bans"])}</p>
<h2 id="cash">Turning NX into mesos</h2><ul>{"".join(f"<li>{e(x)}</li>" for x in Mk["cash"])}</ul>
<div class="rws">{rw("Regular Store Permit")}{rw("Megaphone|Megaphone · 350 NX")}{rw("Super Megaphone|Super Megaphone · 1,500 NX")}</div>
{srcs(Mk["src"])}
<h2 id="faq">FAQ</h2>{faq_html(Mk["faq"])}"""
    side = '<div class="card"><h3>Free Market</h3><p><a href="#quick">Quick tips</a></p><p><a href="#shop">Store permits</a></p><p><a href="#scams">Scams</a></p><p><a href="/money-making/">Mesos guide →</a></p></div>'
    write("/free-market/", page("/free-market/", "MapleStory Classic Free Market: How to Sell & Avoid Scams",
                                "MapleStory Classic Free Market guide: how shops and store permits work, how to price at the sold price, what sells, trade scams, bots and bans.", body,
                                crumbs=[("/", "Guide"), (None, "Free Market")], schema=faq_schema(Mk["faq"]), side_extra=side))

def endgame_html():
    Eg = L["endgame"]
    facts = "".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in Eg["facts"])
    maps = "".join(f'<tr><td data-th="Map">{"".join(_img(mob_src(m), "", "sprite sm") for m in ids[:1])}<b>{e(n)}</b><small class="show-sm">{e(mons)}</small></td><td class="hide-sm" data-th="Monsters">{e(mons)}</td><td data-th="EXP/hr">{e(xh)}</td><td class="hide-sm" data-th="Per level at 60">{e(hrs)}</td><td data-th="Best for">{e(best)}<small class="show-sm">{e(note)}</small></td><td class="hide-sm" data-th="Note">{e(note)}</td></tr>' for n, ids, mons, xh, hrs, best, note in Eg["maps"])
    hit = "".join(f'<tr data-lv="{lv}" data-av="{av}"><td data-th="Monster">{_img(mob_src(i), "", "sprite sm")}<b>{e(n)}</b><small class="show-sm">{e(w)}</small></td><td data-th="Lv">{lv}</td><td class="hide-sm" data-th="Where">{e(w)}</td><td class="hc-out" data-th="Hit chance">–</td></tr>' for n, i, lv, av, w in Eg["hit"])
    quests = "".join(f'<tr><td data-th="Quest"><b>{e(n)}</b></td><td data-th="Level">{e(lv)}</td><td data-th="Why">{e(w)}</td></tr>' for n, lv, w in Eg["quests"])
    return f"""<h2 id="endgame">Level 60 and beyond</h2><p>{e(Eg["intro"])}</p><div class="facts">{facts}</div>
<h3 style="margin-top:20px">Where to train past 55</h3><table class="tbl compact"><thead><tr><th>Map</th><th class="hide-sm">Monsters</th><th>EXP/hr</th><th class="hide-sm">Per level at 60</th><th>Best for</th><th class="hide-sm">Note</th></tr></thead><tbody>{maps}</tbody></table>
<p class="muted" style="margin-top:8px">{e(Eg["mapsNote"])} <a href="/tools/#exp">EXP calculator →</a></p>
<h3 style="margin-top:20px" id="hit">Can you hit it?</h3><p>Enter your level and accuracy (ACC) to see your chance to hit each high-level monster.</p>
<div id="hitchk"><div class="hc-in"><label>Your level<input id="hc-lv" type="number" min="1" max="100" value="60" inputmode="numeric"></label><label>Your ACC<input id="hc-acc" type="number" min="0" max="999" value="130" inputmode="numeric"></label></div>
<table class="tbl compact"><thead><tr><th>Monster</th><th>Lv</th><th class="hide-sm">Where</th><th>Hit chance</th></tr></thead><tbody>{hit}</tbody></table></div>
<p class="muted" style="margin-top:8px">{e(Eg["hitNote"])}</p>
<h3 style="margin-top:20px">Quests worth it past 55</h3><table class="tbl compact"><thead><tr><th>Quest</th><th>Level</th><th>Why</th></tr></thead><tbody>{quests}</tbody></table>
<p class="callout warn" style="margin-top:12px">{e(Eg["not"])}</p>{srcs(Eg["src"])}"""

def build_updates():
    items = "".join(f'<article class="upd" id="u{e(u["date"])}"><p class="upd-d"><time datetime="{e(u["date"])}">{date.fromisoformat(u["date"]).strftime("%b %-d, %Y")}</time></p><h2>{e(u["title"])}</h2><ul>' + "".join(f"<li>{e(x)}</li>" for x in u["items"]) + "</ul></article>" for u in UPDATES["entries"])
    body = f"""<h1>What's new on Maple Classic Guide</h1>
<p class="lede">Every fix and addition, newest first. Spotted something wrong? Use "Was this page right?" at the bottom of any page.</p>{items}"""
    write("/updates/", page("/updates/", "What's New | Maple Classic Guide", "What's new on the Maple Classic Guide: every new page, tool and data fix, logged after each MapleStory Classic World patch and event.", body,
                            crumbs=[("/", "Guide"), (None, "What's new")]))

def build_static():
    about = f'''<h1>About this guide</h1>
<p class="lede">A fan-made quick reference for MapleStory Classic World, built to stay open on your phone while you play.</p>
<h2>Where the data comes from</h2><p>We compile Classic-specific information from community databases and guides, chiefly <a href="https://meowdb.com/msclassic" rel="nofollow noopener">MeowDB</a> (becoming NiaDB), <a href="https://mapleclassic.wiki" rel="nofollow noopener">mapleclassic.wiki</a>, <a href="https://metaroad.gg/maplestory-classic" rel="nofollow noopener">Metaroad</a>, <a href="https://maplestory.quest" rel="nofollow noopener">maplestory.quest</a> and launch-week player reports, and we link the source on each entry. All of it is rewritten in our own words.</p>
<h2>Huge thanks</h2><p>Most Classic numbers on this site trace back to the community's own research, above all <a href="https://meowdb.com/msclassic" rel="noopener">NiaMeowDB</a>. If you want the full database (every item, map and drop), go there. We link the exact source on each entry.</p>
<h2>How this site is made</h2><p>We gather Classic facts from the sources above, rewrite them as short answers, and tag how sure we are. AI tools helped us research and draft it, which is why every entry carries a confidence tag and a source link. We're checking routes and builds in game after launch and fix anything players report. No meso sellers, boosting or account services, ever.</p>
<h2>How sure are we?</h2><p>{conf("high")} several Classic sources agree. {conf("medium")} one Classic source, or partly our estimate. {conf("low")} unverified, or content that isn't live yet.</p>
{f'<h2>Support the guide</h2><p>No ads, no paywalls, no sign-ups, ever. The guide runs entirely on player donations. If it helped you, {coffee_btn()}</p>' if COFFEE else ""}
<h2>Found a mistake?</h2><p>Classic is new and numbers change with patches. Email <a href="mailto:robertlazau@gmail.com?subject=Maple%20Classic%20Guide%20fix">robertlazau@gmail.com</a> with what you saw in game and we'll fix it.</p>
<h2>Not affiliated with Nexon</h2><p>This is an unofficial fan site. MapleStory and related names are trademarks of Nexon Korea Corporation and Nexon America Inc.</p>'''
    write("/about/", page("/about/", "About & Sources | Maple Classic Guide", "Where the Maple Classic Guide gets its MapleStory Classic data, how we mark what's confirmed, and how to send us a fix. No ads, kept alive by players.", about, crumbs=[("/", "Guide"), (None, "About")]))
    priv = f'''<h1>Privacy policy</h1><p>Last updated {CHECKED}.</p>
<p>This site doesn't ask for accounts or personal information. Your last job and level in the "Your run" picker are saved only in your own browser.</p>
<h2>Analytics</h2><p>We use Vercel Web Analytics to count page views. It doesn't use cookies or track you across sites.</p>
<h2>No ads</h2><p>This site runs no ads and no ad trackers. It's kept alive by player donations through <a href="https://buymeacoffee.com/goldenboypro" rel="noopener">Buy Me a Coffee</a>, which has its own privacy policy if you choose to donate.</p>
<h2>Contact</h2><p><a href="mailto:robertlazau@gmail.com">robertlazau@gmail.com</a></p>'''
    write("/privacy/", page("/privacy/", "Privacy Policy | Maple Classic Guide", "Privacy policy for the Maple Classic Guide: no accounts, no ads, no ad trackers and cookie-free analytics. Your settings stay on your own device.", priv, crumbs=[("/", "Guide"), (None, "Privacy")]))
    nf = page("/404", "Page not found | Maple Classic Guide", "Page not found.", '<h1>Lost in the Ant Tunnel?</h1><p class="lede">That page doesn\'t exist. Use a Return Scroll:</p><p><a href="/">Back to the guide →</a></p>')
    with open(os.path.join(OUT, "404.html"), "w") as f:
        f.write(nf.replace(f'<link rel="canonical" href="{SITE}/404">', '<meta name="robots" content="noindex">').replace('<meta name="robots" content="max-image-preview:large">\n', ""))

def main():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    for n in ["style.css", "site.js", "favicon.svg", "og.png", "favicon-48.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png"]:
        p = os.path.join(ROOT, "src", n)
        if os.path.exists(p): shutil.copy(p, OUT)
    if os.path.isdir(os.path.join(ROOT, "src", "fonts")):
        shutil.copytree(os.path.join(ROOT, "src", "fonts"), os.path.join(OUT, "fonts"))
    key_file = os.path.join(ROOT, "src", "indexnow-key.txt")  # IndexNow: search engines fetch /<key>.txt to check pings are ours
    if os.path.exists(key_file):
        key = open(key_file).read().strip()
        with open(os.path.join(OUT, f"{key}.txt"), "w") as f:
            f.write(key)
    with open(os.path.join(OUT, "site.webmanifest"), "w") as f:
        json.dump({"name": NAME, "short_name": "Maple Guide", "description": "MapleStory Classic builds, leveling and secrets",
                   "start_url": "/", "scope": "/", "display": "standalone", "background_color": "#120a05", "theme_color": "#120a05",
                   "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
                             {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}, f, indent=1)
    b64 = os.path.join(ROOT, "src", "og.b64")  # share image kept as text so it can be edited on github.com
    if os.path.exists(b64):
        import base64
        with open(b64) as f, open(os.path.join(OUT, "og.png"), "wb") as g:
            g.write(base64.b64decode(f.read()))
    build_home(); build_leveling(); build_jobs(); build_tiers(); build_tools(); build_crafting(); build_bosses(); build_kpq(); build_quests(); build_quest_pages(); build_money(); build_prices(); build_news(); build_citizenship(); build_events(); build_market(); build_updates(); build_adv(); build_secrets(); build_rules(); build_static()
    idx = [{"t": "Home: pick your class and level", "u": "/", "k": "page"}, {"t": "Grind spots: leveling route 1–100", "u": "/leveling/", "k": "page"},
           {"t": "Builds: all 10 jobs", "u": "/jobs/", "k": "page"}, {"t": "Tier list: best class for you", "u": "/tier-list/", "k": "page", "x": "best class ranking grinding bossing party beginner"}, {"t": "EXP calculator: time to next level", "u": "/tools/#exp", "k": "Tool", "x": "exp table hours level 100 calculator"}, {"t": "Scroll simulator", "u": "/tools/#scrolls", "k": "Tool", "x": "scroll chaos intermediate lesser greater success rate"}, {"t": "What's new", "u": "/updates/", "k": "page", "x": "changelog updates patch"}, {"t": "Crafting: what to keep for each profession", "u": "/crafting/", "k": "page", "x": "crafting smithing weaponcrafting tailoring woodcrafting leatherworking arcforge ore screw leather keep sell"}, {"t": "Job up: 1st and 2nd job advancement", "u": "/job-advancement/", "k": "page"},
           {"t": "Secrets: hidden maps and jump quests", "u": "/secrets/", "k": "page"}, {"t": "Rules: scrolls, EXP, crafting, mesos", "u": "/classic-rules/", "k": "page"}]
    MAIN_STAT = {"warrior": "str strength", "magician": "int intelligence mage wizard", "bowman": "dex dexterity archer", "thief": "luk luck"}
    for c, j in ALLJOBS:
        idx.append({"t": f"{j['name']} build", "u": f"/jobs/{j['id']}/", "k": c["name"], "d": short(f"{c['name']} job · {j['weapon']}", 90),
                    "x": j["weapon"] + " " + c["name"] + " build stats ap sp skills " + MAIN_STAT.get(c["id"], "")})
    for r in sorted(LEV["route"], key=lambda r: (r["from"], r["to"])):
        best = [b for b in (r.get("bestFor") or []) if b != "all"]
        ctx = f"{r.get('region', '').replace('Victoria Island - ', '')} · {r.get('monsters', '')} · monsters lv {r.get('monsterLevel', '')}" + (f" · best for {', '.join(best)}" if best else "")
        idx.append({"t": f"Lv {r['from']}–{r['to']}: {tidy(r['map'])[:70]}", "u": f"/leveling/#lv-{r['from']}-{r['to']}", "k": "Grind spot",
                    "d": ("Opens Nov 18 · " if "Nov 18" in r["map"] else "") + short(ctx), "x": r.get("monsters", "") + " where to train level grind", "lo": r["from"], "hi": r["to"]})
    for s_ in SEC["secrets"]:
        idx.append({"t": s_["name"], "u": "/secrets/#" + re.sub(r"[^a-z]+", "-", s_["name"].split(" (")[0].lower()).strip("-"), "k": "Secret",
                    "d": short(f"{s_['type'].capitalize()} · {s_['region'].replace('Victoria Island - ', '')} · {s_['howToGet']}"), "x": s_["region"] + " " + s_["type"] + " jq hidden"})
    idx += [{"t": "News: launch day, events and patch notes", "u": "/news/", "k": "page", "x": "patch notes events launch halloween guild housing deadline maintenance"}]
    for ev in G["news"]["events"]:
        idx.append({"t": ev["name"] + " (" + ev["when"] + ")", "u": f"/news/#e-{qslug(ev['name'])}", "k": "Event", "d": short(ev["text"]),
                    "x": ev["text"] + (" third job" if "3rd job" in ev["name"] else "") + (" hpq henesys party quest" if "Moon Bunny" in ev["name"] else "")})
    idx += [{"t": "Which Magician? F/P vs I/L vs Cleric", "u": "/jobs/#which-magician", "k": "Builds", "x": "magician mage wizard cleric fire poison ice lightning which job best pick"},
            {"t": "How to level a Cleric", "u": "/jobs/cleric/#how-to-level", "k": "Builds", "x": "cleric leveling undead heal holy arrow training spot"},
            {"t": "Where should I train? Type your level", "u": "/leveling/#quick", "k": "Leveling", "x": "where to level train grind 1 10 20 30 fast route beginner directions how to get there"},
            {"t": "New character: where to put your first stat points", "u": "/jobs/#start", "k": "Builds", "x": "character creation starting stats ap ability points 9 free points dice beginner skill points three snails recovery nimble feet"},
            {"t": "Bosses: respawn timers and drops", "u": "/bosses/", "k": "page", "x": "boss timer respawn drops"},
            {"t": "KPQ: Kerning City Party Quest guide", "u": "/party-quest/", "k": "page", "x": "kpq party quest cloto coupons king slime squishy shoes combos"},
            {"t": "Quests: best quests by level", "u": "/quests/", "k": "page", "x": "quest exp rewards citizenship"},
            {"t": "Price check: what's my item worth?", "u": "/prices/", "k": "page", "x": "price check prices worth value item cost sell mesos live market"},
            {"t": "This week's best money farms", "u": "/prices/#farms", "k": "Mesos", "x": "farm farming money mesos best mob drops profit weekly"},
            {"t": "Money making: how to make mesos", "u": "/money-making/", "k": "page", "x": "mesos money free market prices merch farm sell"},
            {"t": "Citizenship and housing", "u": "/citizenship/", "k": "page", "x": "citizenship housing house home grade henesys kerning arthur roxy donation community board"},
            {"t": "Citizenship grades and unlocks", "u": "/citizenship/#grades", "k": "Citizenship", "x": "grade points discount storage resident's chair"},
            {"t": "Housing: how to get a house", "u": "/citizenship/#housing", "k": "Citizenship", "x": "house home furniture storage crafting station grade 2"},
            {"t": "Citizenship donation items", "u": "/citizenship/#points", "k": "Citizenship", "x": "donate weekly daily greeting community board"},
            {"t": "Events: Mark of the Beta, Halloween, daily gifts", "u": "/events/", "k": "page", "x": "event halloween mark beta journey begins gift"},
            {"t": "Mark of the Beta walkthrough", "u": "/events/#mark", "k": "Event", "x": "jay journal pages pig beach marr's forest ant tunnel hat lv 25"},
            {"t": "Halloween event: Malady's candy hunt", "u": "/events/#halloween", "k": "Event", "x": "halloween candies malady trick or treat pumpkin basket orange slime oct 27 oct 28"},
            {"t": "The Journey Begins daily gifts", "u": "/events/#journey", "k": "Event", "x": "maple leaves maple administrator daily gift 14"},
            {"t": "Free Market: selling, prices and scams", "u": "/free-market/", "k": "page", "x": "free market fm shop store permit sell price scam trade"},
            {"t": "Store permits and opening a shop", "u": "/free-market/#shop", "k": "Market", "x": "store permit shop hired merchant"},
            {"t": "Trade scams to avoid", "u": "/free-market/#scams", "k": "Market", "x": "scam trade switch fake gm"},
            {"t": "Bots, reporting and bans", "u": "/free-market/#bots", "k": "Market", "x": "bot report ban rmt buy mesos"},
            {"t": "Level 60+: where to train", "u": "/leveling/#endgame", "k": "Grind spot", "x": "60 70 80 endgame sleepy dungeon forest of evil sanctuary", "lo": 55, "hi": 100},
            {"t": "Hit chance checker (accuracy)", "u": "/leveling/#hit", "k": "Tool", "x": "accuracy acc miss hit chance avoid"}]
    for b in G["bosses"]:
        idx.append({"t": f"{b['name']} (boss, lv {b['lv']})", "u": f"/bosses/#{b['id']}", "k": "Boss", "d": short(f"{b['where']} · comes back every {b['respawn']}"), "x": b["where"] + " respawn drops"})
    VERDICT = {"must": "Must do", "skip": "Skip it", "future": "Not out yet", "good": "Worth it", "fun": "Just for fun"}
    for q in G["quests"]:
        gq = QGB.get(q["name"])
        if gq:
            v = "future" if gq["status"] == "future" else q["verdict"]
            items = " ".join(dict.fromkeys([c["name"] for c in gq["collect"]] + [k["monster"] for k in gq["kills"]] + [c["name"] for c in gq["chain"]]))
            idx.append({"t": q["name"], "u": qhref(q), "k": "Quest", "d": short(f"{VERDICT.get(v, '')} · Lv {q['lv']}+ · {gq['start']['npc']} in {gq['start']['town'] or gq['start']['map']} · {gq['card']}".lstrip(" ·")),
                        "x": f"level {q['lv']} {gq['start']['npc']} {gq['start']['town']} walkthrough step by step how to {items}"})
        else:
            idx.append({"t": q["name"], "u": qhref(q), "k": "Quest", "d": short(f"{VERDICT.get(q['verdict'], '')} · Lv {q['lv']}+ · {q['npc']} in {q['town']} · {q['task']}".lstrip(" ·")),
                        "x": f"level {q['lv']} {q['npc']} {q['town']}"})
    for i, m in enumerate(SEC["mechanics"]):
        idx.append({"t": m["topic"], "u": f"/classic-rules/#m{i}", "k": "Rules", "d": short(tidy(m["facts"][0]) if m.get("facts") else "")})
    for it in PC_ITEMS:
        wk = PRICES["week"].rsplit(",", 1)[0]
        bits = ([f"~{it['p'][0]:,} mesos ({wk})"] if it["p"] else []) + ([f"Dropped by {', '.join(it['from'][:3])}"] if it["from"] else []) + ([f"Crafters use it for {', '.join(dict.fromkeys(it['use']))}"] if it["use"] else [])
        idx.append({"t": it["n"], "u": "/prices/?item=" + urllib.parse.quote(it["n"]), "k": "Item", "d": short(" · ".join(bits) or "Check its live price"), "x": "price worth sell drop item"})
    later = "/news/#e-" + qslug("3rd job test server")
    idx += [{"t": "Zakum, El Nath, Orbis and Ludibrium", "u": later, "k": "Not in Classic yet", "d": "Classic is Victoria Island and Maple Island for now. Ossyria has no date yet.",
             "x": "zakum el nath orbis ludibrium ossyria aqua road leafre horntail papulatus pianus lpq opq"},
            {"t": "4th job", "u": later, "k": "Not in Classic yet", "d": "The level cap is 100, and 3rd job is planned for 2027.", "x": "fourth job 4th job advancement"}]
    PAGE_DESC = {h: d for _, items in NAV_GROUPS for h, _, d in items}
    PAGE_DESC["/"] = "Pick your class, job and level. Get your grind spot, AP and SP."
    EXTRA = {"/": "new player start beginner noob first time plan", "/tier-list/": "solo which class should i play pick main", "/job-advancement/": "advance advancement 1st 2nd first second job test marble",
             "/secrets/": "jq hidden secret", "/money-making/": "money"}
    blurb = {ev["id"]: ev["blurb"] for ev in L["events"]["now"]}
    HAND = {"/tools/#exp": "How long until your next level, from your EXP per hour", "/tools/#scrolls": "Practice scrolling with Classic's success rates, for free",
            "/jobs/#which-magician": "Fire/Poison, Ice/Lightning or Cleric, side by side", "/jobs/cleric/#how-to-level": "Undead maps, the Heal change and mana tips",
            "/leveling/#quick": "Type your level and get the spot, plus the walk there", "/jobs/#start": "Your starting stats and your first skill points",
            "/prices/#farms": f"The four mobs worth hunting the week of {PRICES['week'].rsplit(',', 1)[0]}", "/citizenship/#grades": "What each citizenship grade unlocks",
            "/citizenship/#housing": "How to get a home and what it's good for", "/citizenship/#points": "What to donate for citizenship points",
            "/events/#mark": blurb.get("mark", ""), "/events/#halloween": blurb.get("halloween", ""), "/events/#journey": blurb.get("journey", ""),
            "/free-market/#shop": "How to open your own shop in the Free Market", "/free-market/#scams": "Common trade tricks and how to dodge them",
            "/free-market/#bots": "Reporting bots, and why buying mesos gets you banned", "/leveling/#endgame": "Where to train once the usual spots run out",
            "/leveling/#hit": "Will you miss? Check your accuracy against a monster"}
    for it in idx:
        if it["u"] in HAND: it.setdefault("d", HAND[it["u"]])
        if it["k"] == "page":
            it.setdefault("d", PAGE_DESC.get(it["u"], ""))
            if it["u"] in EXTRA: it["x"] = (it.get("x", "") + " " + EXTRA[it["u"]]).strip()
    with open(os.path.join(OUT, "search.json"), "w") as f:
        json.dump(idx, f, separators=(",", ":"))
    paths = ["/", "/leveling/", "/jobs/", "/tier-list/", "/tools/", "/crafting/", "/news/", "/events/", "/citizenship/", "/free-market/", "/bosses/", "/party-quest/", "/quests/", "/money-making/", "/prices/", "/updates/", "/job-advancement/", "/secrets/", "/classic-rules/", "/about/", "/privacy/"] + [f"/jobs/{j['id']}/" for _, j in ALLJOBS] + [f"/quests/{g['slug']}/" for g in QG["quests"]]
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{LASTMOD_SEEN.get(p, {}).get('d', TODAY)}</lastmod></url>\n" for p in paths) + "</urlset>\n")
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    if not os.environ.get("VERCEL"):  # local builds keep the dates file current; commit it with your change
        with open(LASTMOD_FILE, "w") as f:
            f.write("{\n" + ",\n".join(f'  {json.dumps(k)}: {json.dumps(v)}' for k, v in sorted(LASTMOD_SEEN.items())) + "\n}\n")
    print("built", len(paths), "pages")

if __name__ == "__main__":
    main()
