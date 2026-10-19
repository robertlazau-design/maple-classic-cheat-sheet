#!/usr/bin/env python3
"""Builds the Maple Classic Cheat Sheet into ./public as plain static HTML.
Edit the JSON in ./data, run `python3 build.py`, commit, and Vercel serves ./public.
No dependencies."""
import json, os, re, shutil, html
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "public")
SITE = "https://www.mapleclassiccheatsheet.com"
NAME = "Maple Classic Cheat Sheet"
CHECKED = "Oct 19, 2026"
CHECKED_ISO = "2026-10-19"
DATA_NOTE = "Founder's Access data"

def load(n):
    with open(os.path.join(ROOT, "data", n)) as f:
        return json.load(f)

JOBS = load("jobs.json"); LEV = load("leveling.json"); SEC = load("secrets.json"); IMG = load("images.json")
API = "https://maplestory.io/api/GMS/83"

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)

def tidy(s):
    """Small copy fixes on research text before it reaches readers."""
    s = str(s)
    s = s.replace(" Don't promise readers a route to 100.", "")
    s = re.sub(r"\(inference(, verify)?\)", "(our estimate)", s)
    s = s.replace("(MeowDB)", "").replace("  ", " ")
    return s.strip()

def conf(c):
    c = (c or "medium").lower()
    label = {"high": "Confirmed", "medium": "Likely", "low": "Unconfirmed"}.get(c, c)
    return f'<span class="chip c-{e(c)}" title="How sure we are">{label}</span>'

def srcs(s):
    if not s: return ""
    items = s if isinstance(s, list) else [x.strip() for x in str(s).split(";")]
    links = []
    for u in items:
        u = u.strip()
        if not u.startswith("http"): continue
        host = re.sub(r"^https?://(www\.)?", "", u).split("/")[0]
        links.append(f'<a href="{e(u)}" rel="nofollow noopener" target="_blank">{e(host)}</a>')
    return f'<p class="src">Source: {", ".join(links)}</p>' if links else ""

def _img(src, alt, cls):
    return f'<img class="{cls}" src="{src}" alt="{e(alt)}" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.remove()">'
def mob_img(name, cls="sprite"):
    i = IMG["mobs"].get(name)
    return _img(f"{API}/mob/{i}/render/stand", name, cls) if i else ""
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

NAV = [("/", "Home"), ("/leveling/", "Grind spots"), ("/jobs/", "Builds"), ("/job-advancement/", "Job up"), ("/secrets/", "Secrets"), ("/classic-rules/", "Rules")]

def page(path, title, desc, body, crumbs=None, schema=None, side_extra="", hero=""):
    canon = SITE + path
    nav = "".join(f'<a href="{h}"{" aria-current=page" if h == path else ""}>{t}</a>' for h, t in NAV)
    bc = ""
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE + "/"}] if path == "/" else []
    if crumbs:
        bc = '<nav class="crumbs" aria-label="Breadcrumb">' + " › ".join(f'<a href="{h}">{e(t)}</a>' if h else e(t) for h, t in crumbs) + "</nav>"
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": t, **({"item": SITE + h} if h else {})} for i, (h, t) in enumerate(crumbs)]})
    if schema: ld.append(schema)
    tabs = [("/", "🏠", "Home"), ("/leveling/", "🗺️", "Grind"), ("/jobs/", "⚔️", "Builds"), ("/secrets/", "🤫", "Secrets")]
    tabbar = "".join(f'<a href="{h}"{" aria-current=page" if h == path else ""}><span aria-hidden="true">{ic}</span>{t}</a>' for h, ic, t in tabs) + '<button type="button" data-search><span aria-hidden="true">🔍</span>Search</button>'
    ldtxt = "".join(f'<script type="application/ld+json">{json.dumps(x)}</script>' for x in ld)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE}/og.png"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#3b2210">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="/style.css">
{ldtxt}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="frame">{LEAVES}
<header class="site-h"><div class="wrap">
<a class="brand" href="/">{LEAF}<span>Maple Classic <span>Cheat Sheet</span></span></a>
<nav class="nav" aria-label="Main">{nav}</nav>
<button class="search-btn" type="button" data-search aria-label="Search the cheat sheet"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M16.5 16.5L21 21" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg><span>Search</span><kbd>/</kbd></button>
</div></header>
{hero}
<div class="wrap"><div class="ad ad-top" data-slot=""></div>
<div class="layout{" has-side" if side_extra else ""}">
<main id="main">{bc}{body}</main>
<aside class="side" aria-label="Sidebar"><div class="sticky">{side_extra}<div class="ad ad-side" data-slot=""></div></div></aside>
</div></div>
<footer class="site-f"><div class="wrap">
<a class="brand" href="/">{LEAF}<span>Maple Classic <span>Cheat Sheet</span></span></a>
<nav aria-label="Footer">{"".join(f'<a href="{h}">{t}</a>' for h, t in NAV)}<a href="/about/">About &amp; sources</a><a href="/privacy/">Privacy</a></nav>
<p>Fan-made guide, not affiliated with or endorsed by Nexon. MapleStory is a trademark of Nexon. Data checked {CHECKED} ({DATA_NOTE}); we re-check after every patch.</p>
<p>Game sprites and minimaps © Nexon, loaded from <a href="https://maplestory.io" rel="nofollow noopener">maplestory.io</a>. Built by <a href="https://www.robertlazau.com">Golden Boy Productions</a>.</p>
</div></footer>
</div>
<nav class="tabbar" aria-label="Quick nav">{tabbar}</nav>
<div class="search" id="search" hidden><div class="search-box" role="dialog" aria-modal="true" aria-label="Search">
<input id="q" type="search" placeholder="Try: assassin, mushmom, level 35, scrolls" autocomplete="off" aria-label="Search the cheat sheet"><button type="button" class="search-x" data-close aria-label="Close search">Esc</button>
<ul id="hits" role="listbox"></ul></div></div>
<script src="/site.js" defer></script>
</body>
</html>"""

def stamp():
    return f'<p class="stamp"><b>✓ Checked {CHECKED}</b><span>{DATA_NOTE}. Tags show how sure we are: {conf("high")} {conf("medium")} {conf("low")}</span></p>'

def write(path, text):
    d = os.path.join(OUT, path.strip("/"))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w") as f:
        f.write(text)

ALLJOBS = [(c, j) for c in JOBS["classes"] for j in c["jobs"]]

def route_li(r):
    cls = "future" if "Nov 18" in r["map"] or "from Nov" in r["map"] else ("wall" if r["from"] >= 80 else "")
    lv = f'{r["from"]}–{r["to"]}'
    best = ", ".join(r.get("bestFor") or [])
    sprites = "".join(mob_img(m) for m in mobs_in(r.get("monsters", "")))
    mm = next((v for k, v in IMG["routeMaps"].items() if k in r["map"]), None)
    pics = f'<div class="pics">{map_img(mm, tidy(r["map"]).split(" / ")[0].split(" (")[0]) if mm else ""}<div class="sprites">{sprites}</div></div>' if (sprites or mm) else ""
    return f'''<li class="{cls}" id="lv-{r["from"]}-{r["to"]}"><span class="lv">Lv {lv}</span>{pics}
<span class="map">{e(tidy(r["map"]))} {conf(r.get("confidence"))}</span>
<span class="sub">{e(r.get("region",""))} · {e(r.get("monsters",""))} (lv {e(r.get("monsterLevel",""))}){" · best for " + e(best) if best and best != "all" else ""}</span>
<span class="tip">{e(tidy(r.get("tip","")))}</span></li>'''

def build_home():
    route = sorted([r for r in LEV["route"]], key=lambda r: ("Nov 18" in r["map"], r["from"], r["to"]))
    fdata = {"route": [{"from": r["from"], "to": r["to"], "map": tidy(r["map"]), "monsters": r.get("monsters", ""), "monsterLevel": r.get("monsterLevel", ""), "confidence": r.get("confidence", "medium"),
                        "sprites": [IMG["mobs"][m] for m in mobs_in(r.get("monsters", ""), 2)]} for r in route],
             "classes": [{"id": c["id"], "name": c["name"], "npc": c["firstJob"]["npc"], "town": c["firstJob"]["town"], "sprite": IMG["classNpc"][c["id"]][0],
                          "jobs": [j["id"] for j in c["jobs"]]} for c in JOBS["classes"]],
             "jobs": {j["id"]: {"name": j["name"], "cls": c["id"], "weapon": j["weapon"], "play": tidy(j["playstyle"]), "adv": {"test": tidy(j["advancement"]["test"])},
                                 "apSummary": tidy(j["ap"]["summary"]), "ap": [tidy(x) for x in j["ap"]["steps"]], "sp1": [tidy(x) for x in j["sp"]["firstJob"]], "sp2": [tidy(x) for x in j["sp"]["secondJob"]]} for c, j in ALLJOBS},
             "api": API}
    cards = [("/leveling/", "🗺️ Grind spots", "Where to train at every level, 1 to 100.", "mob/1210103"),
             ("/jobs/", "⚔️ Builds", "AP + SP for all 10 jobs. Resets cost 7,000 NX, so don't wing it.", "npc/1012100"),
             ("/job-advancement/", "⬆️ Job up", "Who to talk to at 10 and 30, and how the marble test works.", "npc/1032001"),
             ("/secrets/", "🤫 Secrets", f'{len(SEC["secrets"])} hidden maps, jump quests and boss rooms.', "mob/6130101"),
             ("/classic-rules/", "📜 Rules", "Scroll odds, the EXP wall, crafting and making mesos.", "mob/1110100")]
    musts = ["Finish every Maple Island quest before you take the boat. It's one-way.",
             "Taxi to your job town while you're still a Beginner. It's 90% off.",
             "Plan your AP and SP. Fixing a mistake costs 7,000 NX.",
             "Carry a Return Scroll. There's no cab back out of the Ant Tunnel.",
             "Buy Orange Potions or Lemons for MP, not Blue Potions. Better value."]
    cast = [("mob", 210100, "mob", 10, 20, 2.4, .4), ("mob", 1210102, "mob", 38, 10, 2.3, .9), ("mob", 100101, "mob", 70, 24, 2.8, 1.3),
            ("npc", 1022000, "npc", 2, 58, 1.9, 0), ("npc", 1032001, "npc", 27, 50, 1.6, .6), ("npc", 1012100, "npc", 49, 58, 1.9, 1.1), ("npc", 1052001, "npc", 70, 48, 1.25, 1.6)]
    castimg = "".join(f'<img src="{API}/{kind}/{i}/render/stand" alt="" loading="eager" referrerpolicy="no-referrer" onerror="this.remove()" style="left:{left}%;top:{top}%;--k:{k};--d:{d}s">' for _, i, kind, left, top, k, d in cast)
    hero = f'''<section class="hero"><div class="wrap">
<div class="hero-copy">{HOUSE}<p class="kicker">Classic World · launches Oct 21</p><h1>MapleStory Classic<br>Cheat Sheet</h1>
<p class="sub">Pick your class. Get your build, your grind spot and the secrets. That's it.</p>
<div class="btns"><a class="btn btn-primary" href="#run">Start here {LEAF_SM}</a><button class="btn btn-ghost" type="button" data-search>Search anything</button></div>
{stamp()}</div>
<div class="cast" aria-hidden="true">{castimg}</div>
</div></section>'''
    classes = "".join(f'<button type="button" class="cls" data-cls="{e(c["id"])}" aria-pressed="false"><img src="{API}/npc/{IMG["classNpc"][c["id"]][0]}/render/stand" alt="" referrerpolicy="no-referrer" onerror="this.remove()"><b>{e(c["name"])}</b></button>' for c in JOBS["classes"])
    body = f'''<section class="run" id="run" aria-labelledby="runh">
<h2 id="runh">Your run</h2>
<p class="step"><span>1</span>Pick your class</p><div class="classes" role="group" aria-label="Class">{classes}</div>
<p class="step"><span>2</span>Pick your job</p><div class="jobs" id="jobchips" role="group" aria-label="Job"></div>
<p class="step"><span>3</span>Your level</p>
<div class="lvl"><button type="button" class="lv-btn" data-step="-1" aria-label="Level down">−</button><output id="lvout">1</output><button type="button" class="lv-btn" data-step="1" aria-label="Level up">+</button>
<input id="lv" type="range" min="1" max="100" value="1" aria-label="Level"></div>
<div class="result" id="finder-out" aria-live="polite"></div>
<script type="application/json" id="finder-data">{json.dumps(fdata).replace("</", "<\\/")}</script></section>
<div class="ad ad-in" data-slot=""></div>
<h2>Don't be that guy</h2><ol class="musts">{"".join(f"<li>{e(m)}</li>" for m in musts)}</ol>
<h2>Everything else</h2><div class="grid tiles">{"".join(f'<a class="card" href="{h}"><div class="icon">{_img(f"{API}/{ic}/render/stand", "", "")}</div><h3>{t}</h3><p>{d}</p></a>' for h, t, d, ic in cards)}</div>
<div class="facts" style="margin-top:28px"><div><b>Lv 100</b><span>Level cap</span></div><div><b>1st + 2nd job</b><span>3rd job planned for 2027</span></div><div><b>Victoria Island</b><span>Plus Maple Island; no Ossyria yet</span></div><div><b>7,000 NX</b><span>Per AP or SP reset</span></div></div>
<details style="margin-top:20px"><summary>What's different in Classic (60-second version)</summary><ul>{"".join(f"<li>{e(tidy(x))}</li>" for x in JOBS["classicChanges"][:8])}</ul></details>'''
    write("/", page("/", "MapleStory Classic Cheat Sheet: Leveling, Builds & Secrets (2026)",
                    "MapleStory Classic World cheat sheet: pick your class and level and get your build, where to train and the secrets you'll miss. All 10 jobs, mobile-first.", body, hero=hero))

def build_leveling():
    route = sorted(LEV["route"], key=lambda r: (r["from"], r["to"]))
    regions = "".join(f'<tr><td data-th="Region"><b>{e(r["region"])}</b></td><td data-th="Status">{e(r["status"])}</td><td data-th="Notes">{e(tidy(r["notes"]))}</td></tr>' for r in LEV["regionsAvailable"])
    pqs = "".join(f'<div class="card"><h3>{e(p["name"])} {conf(p.get("confidence"))}</h3><p class="meta">Level {e(p["levels"])} · {e(p["where"])}</p><p>{e(tidy(p["notes"]))}</p></div>' for p in LEV["partyQuests"])
    quests = "".join(f'<tr><td data-th="Quest"><b>{e(q["name"])}</b></td><td data-th="Level">{e(q["level"])}</td><td data-th="Where">{e(q["where"])}</td><td data-th="Why">{e(tidy(q["why"]))}</td></tr>' for q in LEV["quests"])
    bosses = "".join(f'<tr><td data-th="Boss">{mob_img(b["name"], "sprite sm")}<b>{e(b["name"])}</b> {conf(b.get("confidence"))}</td><td data-th="Level">{e(b["level"])}</td><td data-th="Where">{e(b["where"])}</td><td data-th="Respawn">{e(b["respawn"])}</td><td data-th="Notes">{e(tidy(b.get("notes","")))}</td></tr>' for b in LEV["bosses"])
    notes = "".join(f'<details><summary>{e(n["class"])}</summary><p>{e(tidy(n["note"]))}</p>{srcs(n.get("source"))}</details>' for n in LEV["classNotes"])
    tips = "".join(f'<li>{e(tidy(t["tip"]))}</li>' for t in LEV["tips"])
    body = f'''<h1>MapleStory Classic Leveling Guide 1–100</h1>
<p class="lede">The fastest route through Maple Island and Victoria Island, level by level, with where each class should train.</p>
{stamp()}
<div class="toc"><a href="#route">Route</a><a href="#class">By class</a><a href="#pq">Party quests</a><a href="#quests">Quests</a><a href="#bosses">Bosses</a><a href="#tips">Tips</a><a href="#map">What's in the game</a></div>
<p class="callout warn" style="margin-top:16px"><b>Heads up:</b> Classic launches with Maple Island and Victoria Island only. Monsters top out around level 75, and every level from 90 to 99 costs about twice the one before. Reaching 100 is a long-haul goal at launch.</p>
<h2 id="route">Leveling route</h2><div class="jump" role="group" aria-label="Jump to level">{"".join(f'<a href="#lv-{r["from"]}-{r["to"]}">{r["from"]}–{r["to"]}</a>' for r in route if not (r["from"] == 39 and r["to"] == 60))}</div><ol class="route">{"".join(route_li(r) for r in route)}</ol>
<div class="ad ad-in" data-slot=""></div>
<h2 id="class">Where each class should train</h2>{notes}
<h2 id="pq">Party quests</h2><div class="grid">{pqs}</div>
<h2 id="quests">Quests worth your time</h2><table class="tbl"><thead><tr><th>Quest</th><th>Level</th><th>Where</th><th>Why</th></tr></thead><tbody>{quests}</tbody></table>
<h2 id="bosses">Bosses and respawn timers</h2><table class="tbl"><thead><tr><th>Boss</th><th>Level</th><th>Where</th><th>Respawn</th><th>Notes</th></tr></thead><tbody>{bosses}</tbody></table>
<h2 id="tips">Leveling tips</h2><ul>{tips}</ul>
<h2 id="map">What's in the game right now</h2><table class="tbl"><thead><tr><th>Region</th><th>Status</th><th>Notes</th></tr></thead><tbody>{regions}</tbody></table>'''
    write("/leveling/", page("/leveling/", "MapleStory Classic Leveling Guide 1–100: Best Training Spots",
                             "Where to train in MapleStory Classic at every level: Maple Island to Victoria Island, Kerning PQ, bosses, quests and class-specific spots.", body,
                             crumbs=[("/", "Cheat sheet"), (None, "Leveling")],
                             schema={"@context": "https://schema.org", "@type": "Article", "headline": "MapleStory Classic Leveling Guide 1–100", "dateModified": CHECKED_ISO}))

def build_jobs():
    blocks = ""
    for c in JOBS["classes"]:
        fj = c["firstJob"]
        jobs = "".join(f'<a class="card" href="/jobs/{e(j["id"])}/"><h3>{e(j["name"])}</h3><p class="meta">{e(j["weapon"])}</p><p>{e(tidy(j["playstyle"]))}</p></a>' for j in c["jobs"])
        cn = IMG["classNpc"][c["id"]]
        blocks += f'''<h2 id="{e(c["id"])}">{e(c["name"])}</h2><div class="npc-row">{npc_img(cn[0], cn[1])}<span>{e(cn[1])}, {e(fj["town"])}</span></div>
<p><b>1st job:</b> level {e(fj["level"])} with {e(fj["npc"])} in {e(fj["town"])}. {e(tidy(fj["notes"]))}</p>
<div class="grid">{jobs}</div>'''
    body = f'''<h1>MapleStory Classic Job Builds</h1>
<p class="lede">AP and SP plans for every 2nd job. You place every point by hand in Classic, and a reset costs 7,000 NX, so plan before you click.</p>
{stamp()}<div class="toc">{"".join(f'<a href="#{e(c["id"])}">{e(c["name"])}</a>' for c in JOBS["classes"])}</div>{blocks}
<div class="ad ad-in" data-slot=""></div>
<h2>What changed for jobs in Classic</h2><ul>{"".join(f"<li>{e(tidy(x))}</li>" for x in JOBS["classicChanges"])}</ul>'''
    write("/jobs/", page("/jobs/", "MapleStory Classic Job Builds: AP & SP for All 10 Jobs",
                         "Every MapleStory Classic 2nd job compared: Fighter, Page, Spearman, F/P, I/L, Cleric, Hunter, Crossbowman, Assassin and Bandit, with AP/SP builds.", body,
                         crumbs=[("/", "Cheat sheet"), (None, "Job builds")]))
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
<div><dt>Skills first</dt><dd>{e(" · ".join([tidy(x) for x in j["sp"]["secondJob"] if re.match(r"^lv", x, re.I)][:2]))}</dd></div>
<div><dt>Job up</dt><dd>Level {e(adv["level"])}, {e(adv["npc"])} in {e(adv["town"])}</dd></div>
<div><dt>Good at</dt><dd>{e(tidy(j["pros"][0]))}</dd></div>
<div><dt>Watch out</dt><dd>{e(tidy(j["cons"][0]))}</dd></div></dl></section>
<div class="toc"><a href="#ap">AP build</a><a href="#sp">SP build</a><a href="#adv">Job advancement</a><a href="#pros">Pros &amp; cons</a></div>
<h2 id="ap">AP build</h2><p class="callout">{e(tidy(j["ap"]["summary"]))}</p>
<ol class="steps" style="margin-top:12px">{steps(j["ap"]["steps"])}</ol>
<div class="ad ad-in" data-slot=""></div>
<h2 id="sp">SP build</h2><h3>1st job (levels 10–29)</h3><ol class="steps" style="margin-top:8px">{steps(j["sp"]["firstJob"])}</ol>
<h3 style="margin-top:20px">2nd job (level 30+)</h3><ol class="steps" style="margin-top:8px">{steps(j["sp"]["secondJob"])}</ol>
<h2 id="adv">Job advancement</h2><div class="pics">{map_img(IMG["testMap"][c["id"]], "2nd job test map")}<div class="sprites">{npc_img(IMG["classNpc"][c["id"]][0], IMG["classNpc"][c["id"]][1])}</div></div><p><b>1st job:</b> level {e(c["firstJob"]["level"])}, {e(c["firstJob"]["npc"])} in {e(c["firstJob"]["town"])}.</p>
<p><b>2nd job:</b> level {e(adv["level"])}, {e(adv["npc"])} in {e(adv["town"])}. {e(tidy(adv["test"]))}</p>
<h2 id="pros">Pros &amp; cons</h2><div class="pc"><div class="card"><h3>Pros</h3><ul>{"".join(f"<li>{e(tidy(x))}</li>" for x in j["pros"])}</ul></div><div class="card"><h3>Cons</h3><ul>{"".join(f"<li>{e(tidy(x))}</li>" for x in j["cons"])}</ul></div></div>
<p style="margin-top:20px">Other {e(c["name"])} jobs: {" · ".join(f'<a href="/jobs/{e(x["id"])}/">{e(x["name"])}</a>' for x in c["jobs"] if x["id"] != j["id"])}</p>
{srcs(j.get("sources"))}'''
        write(f"/jobs/{j['id']}/", page(f"/jobs/{j['id']}/", f"{j['name']} Build Guide: MapleStory Classic AP & SP",
                                        f"MapleStory Classic {j['name']} build: AP stat plan by level, SP skill order for 1st and 2nd job, job advancement and pros/cons.", body,
                                        crumbs=[("/", "Cheat sheet"), ("/jobs/", "Job builds"), (None, j["name"])], side_extra=side,
                                        schema={"@context": "https://schema.org", "@type": "Article", "headline": f"{j['name']} Build Guide: MapleStory Classic", "dateModified": CHECKED_ISO}))

def build_adv():
    first = "".join(f'<tr><td data-th="Class">{npc_img(IMG["classNpc"][c["id"]][0], IMG["classNpc"][c["id"]][1], "sprite sm")}<b>{e(c["name"])}</b></td><td data-th="Level">{e(c["firstJob"]["level"])}</td><td data-th="NPC">{e(c["firstJob"]["npc"])}</td><td data-th="Where">{e(c["firstJob"]["town"])}</td><td data-th="Stat req">{e(c["firstJob"]["statReq"])}</td></tr>' for c in JOBS["classes"])
    second = "".join(f'<tr><td data-th="Job"><a href="/jobs/{e(j["id"])}/"><b>{e(j["name"])}</b></a></td><td data-th="NPC">{e(j["advancement"]["npc"])}, {e(j["advancement"]["town"])}</td><td data-th="Test">{e(tidy(j["advancement"]["test"]))}</td></tr>' for c, j in ALLJOBS)
    body = f'''<h1>MapleStory Classic Job Advancement</h1>
<p class="lede">1st job at level 10 with no stat requirement, 2nd job at level 30 after a short Dark Marble test. Here's who to see and where.</p>
{stamp()}
<h2>1st job (level 10)</h2><table class="tbl"><thead><tr><th>Class</th><th>Level</th><th>NPC</th><th>Where</th><th>Stat req</th></tr></thead><tbody>{first}</tbody></table>
<p style="margin-top:12px">Tip: ride the taxi to your job town while you're still a Beginner. Beginners get 90% off taxis.</p>
<div class="ad ad-in" data-slot=""></div>
<h2>2nd job (level 30)</h2><p>Every class works the same way: your job NPC gives you a letter, the Job Instructor sends you into a test map, you collect 30 Dark Marbles, trade them for The Proof of a Hero and bring it back to choose your path.</p>
<table class="tbl"><thead><tr><th>Job</th><th>Who</th><th>The test</th></tr></thead><tbody>{second}</tbody></table>
<h2>3rd job</h2><p>Not in Classic at launch. Nexon has said a 3rd job test server is planned for early 2027, alongside the Ossyria rework.</p>'''
    write("/job-advancement/", page("/job-advancement/", "MapleStory Classic Job Advancement: 1st & 2nd Job Guide",
                                    "How to job advance in MapleStory Classic: level 10 1st job NPCs, the level 30 2nd job Dark Marble test for all 10 jobs, and when 3rd job arrives.", body,
                                    crumbs=[("/", "Cheat sheet"), (None, "Job advancement")]))

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
<p><b>How to get there:</b> {e(tidy(s["howToGet"]))}</p><p><b>Why go:</b> {e(tidy(s["reward"]))}</p></article>'''
    body = f'''<h1>MapleStory Classic Hidden Maps &amp; Secrets</h1>
<p class="lede">Hidden streets, jump quests, boss rooms and one-time rewards on Maple Island and Victoria Island, with directions.</p>
{stamp()}
<p class="callout warn" style="margin-top:12px"><b>Don't miss:</b> Maple Island is one-way. Finish its quests (including Pio's boxes for the Green Relaxer chair) before you take the boat.</p>
<div class="filters" data-filters role="group" aria-label="Filter by type">{btns}</div>
<div class="grid">{cards}</div>
<div class="ad ad-in" data-slot=""></div>'''
    write("/secrets/", page("/secrets/", "MapleStory Classic Hidden Maps, Jump Quests & Secrets",
                            f"{len(SEC['secrets'])} MapleStory Classic secrets: hidden streets, Forest of Patience and Shumi jump quests, Mushmom and Jr. Balrog rooms, and missable Maple Island rewards.", body,
                            crumbs=[("/", "Cheat sheet"), (None, "Secrets")]))

def build_rules():
    mech = "".join(f'<h2 id="m{i}">{e(m["topic"])}</h2><p>{conf(m.get("confidence"))}</p><ul>{"".join(f"<li>{e(tidy(x))}</li>" for x in m["facts"])}</ul>{srcs(m.get("source"))}' for i, m in enumerate(SEC["mechanics"]))
    money = "".join(f'<div class="card"><h3>{e(m["method"])} {conf(m.get("confidence"))}</h3><p>{e(tidy(m["details"]))}</p></div>' for m in SEC["moneyMaking"])
    toc = "".join(f'<a href="#m{i}">{e(m["topic"])}</a>' for i, m in enumerate(SEC["mechanics"])) + '<a href="#money">Making mesos</a>'
    body = f'''<h1>MapleStory Classic Rules &amp; Mechanics</h1>
<p class="lede">What's different in Classic: scroll odds, resets, death penalty, the EXP curve, crafting, bosses, the Cash Shop and the economy.</p>
{stamp()}<div class="toc">{toc}</div>{mech}
<div class="ad ad-in" data-slot=""></div>
<h2 id="money">Making mesos</h2><div class="grid">{money}</div>'''
    write("/classic-rules/", page("/classic-rules/", "MapleStory Classic Mechanics: Scrolls, EXP, Crafting & Mesos",
                                  "MapleStory Classic rules explained: scroll success rates, AP/SP reset cost, EXP table and the 90+ wall, crafting professions, boss timers and money making.", body,
                                  crumbs=[("/", "Cheat sheet"), (None, "Classic rules")]))

def build_static():
    about = f'''<h1>About this cheat sheet</h1>
<p class="lede">A fan-made quick reference for MapleStory Classic World, built to stay open on your phone while you play.</p>
<h2>Where the data comes from</h2><p>We compile Classic-specific information from community databases and guides, chiefly <a href="https://meowdb.com/msclassic" rel="nofollow noopener">MeowDB</a> (becoming NiaDB), <a href="https://mapleclassic.wiki" rel="nofollow noopener">mapleclassic.wiki</a>, <a href="https://metaroad.gg/maplestory-classic" rel="nofollow noopener">Metaroad</a>, <a href="https://maplestory.quest" rel="nofollow noopener">maplestory.quest</a> and launch-week player reports, and we link the source on each entry. All of it is rewritten in our own words.</p>
<h2>How sure are we?</h2><p>{conf("high")} several Classic sources agree. {conf("medium")} one Classic source, or partly our estimate. {conf("low")} unverified, or content that isn't live yet.</p>
<h2>Found a mistake?</h2><p>Classic is new and numbers change with patches. Email <a href="mailto:robertlazau@gmail.com?subject=Maple%20Classic%20Cheat%20Sheet%20fix">robertlazau@gmail.com</a> with what you saw in game and we'll fix it.</p>
<h2>Not affiliated with Nexon</h2><p>This is an unofficial fan site. MapleStory and related names are trademarks of Nexon Korea Corporation and Nexon America Inc.</p>'''
    write("/about/", page("/about/", "About & Sources | Maple Classic Cheat Sheet", "Where the Maple Classic Cheat Sheet gets its data, how we rate confidence, and how to report a fix.", about, crumbs=[("/", "Cheat sheet"), (None, "About")]))
    priv = f'''<h1>Privacy policy</h1><p>Last updated {CHECKED}.</p>
<p>This site doesn't ask for accounts or personal information. Your last job and level in the cheat-sheet finder are saved only in your own browser.</p>
<h2>Analytics</h2><p>We use Vercel Web Analytics to count page views. It doesn't use cookies or track you across sites.</p>
<h2>Advertising</h2><p>We show ads from Google AdSense. Google and its partners use cookies to serve ads based on your visits to this and other websites. You can opt out of personalized advertising at <a href="https://www.google.com/settings/ads" rel="nofollow noopener">Google Ads Settings</a>, and learn more at <a href="https://policies.google.com/technologies/ads" rel="nofollow noopener">How Google uses information from sites that use its services</a>. Visitors in the EEA, UK and Switzerland are asked for consent before personalized ads are shown.</p>
<h2>Contact</h2><p><a href="mailto:robertlazau@gmail.com">robertlazau@gmail.com</a></p>'''
    write("/privacy/", page("/privacy/", "Privacy Policy | Maple Classic Cheat Sheet", "Privacy policy for the Maple Classic Cheat Sheet, including analytics and Google AdSense cookies.", priv, crumbs=[("/", "Cheat sheet"), (None, "Privacy")]))
    nf = page("/404", "Page not found | Maple Classic Cheat Sheet", "Page not found.", '<h1>Lost in the Ant Tunnel?</h1><p class="lede">That page doesn\'t exist. Use a Return Scroll:</p><p><a href="/">Back to the cheat sheet →</a></p>')
    with open(os.path.join(OUT, "404.html"), "w") as f: f.write(nf.replace('<link rel="canonical" href="https://www.mapleclassiccheatsheet.com/404">', '<meta name="robots" content="noindex">'))

def main():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    for n in ["style.css", "site.js", "favicon.svg", "og.png"]:
        p = os.path.join(ROOT, "src", n)
        if os.path.exists(p): shutil.copy(p, OUT)
    build_home(); build_leveling(); build_jobs(); build_adv(); build_secrets(); build_rules(); build_static()
    idx = [{"t": "Home: pick your class and level", "u": "/", "k": "page"}, {"t": "Grind spots: leveling route 1–100", "u": "/leveling/", "k": "page"},
           {"t": "Builds: all 10 jobs", "u": "/jobs/", "k": "page"}, {"t": "Job up: 1st and 2nd job advancement", "u": "/job-advancement/", "k": "page"},
           {"t": "Secrets: hidden maps and jump quests", "u": "/secrets/", "k": "page"}, {"t": "Rules: scrolls, EXP, crafting, mesos", "u": "/classic-rules/", "k": "page"}]
    for c, j in ALLJOBS:
        idx.append({"t": f"{j['name']} build", "u": f"/jobs/{j['id']}/", "k": c["name"], "x": j["weapon"] + " " + c["name"]})
    for r in sorted(LEV["route"], key=lambda r: (r["from"], r["to"])):
        idx.append({"t": f"Lv {r['from']}–{r['to']}: {tidy(r['map'])[:70]}", "u": f"/leveling/#lv-{r['from']}-{r['to']}", "k": "Grind spot", "x": r.get("monsters", ""), "lo": r["from"], "hi": r["to"]})
    for s_ in SEC["secrets"]:
        idx.append({"t": s_["name"], "u": "/secrets/#" + re.sub(r"[^a-z]+", "-", s_["name"].split(" (")[0].lower()).strip("-"), "k": "Secret", "x": s_["region"] + " " + s_["type"]})
    for b in LEV["bosses"]:
        idx.append({"t": f"{b['name']} (boss, lv {b['level']})", "u": "/leveling/#bosses", "k": "Boss", "x": b["where"]})
    for i, m in enumerate(SEC["mechanics"]):
        idx.append({"t": m["topic"], "u": f"/classic-rules/#m{i}", "k": "Rules"})
    for q in LEV["quests"]:
        idx.append({"t": q["name"], "u": "/leveling/#quests", "k": "Quest", "x": f"level {q['level']} {q['where']}"})
    with open(os.path.join(OUT, "search.json"), "w") as f:
        json.dump(idx, f, separators=(",", ":"))
    paths = ["/", "/leveling/", "/jobs/", "/job-advancement/", "/secrets/", "/classic-rules/", "/about/", "/privacy/"] + [f"/jobs/{j['id']}/" for _, j in ALLJOBS]
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{CHECKED_ISO}</lastmod></url>\n" for p in paths) + "</urlset>\n")
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print("built", len(paths), "pages")

if __name__ == "__main__":
    main()
