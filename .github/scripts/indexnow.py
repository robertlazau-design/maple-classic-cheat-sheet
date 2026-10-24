"""Submit the Maple Classic Guide pages that changed in this push to IndexNow (Bing and friends).

Which pages changed comes from maple-classic-cheat-sheet/data/lastmod.json (a hash and a date per page):
any page whose entry changed between the previous main and now. If no page content changed
(titles, descriptions, styling), every page is submitted, since search results can still change.
We wait until the live site serves the new dates before submitting, so engines crawl the new version.
"""
import json, os, subprocess, sys, time, urllib.request, urllib.error

SITE = "https://www.mapleclassicguide.com"
HOST = "www.mapleclassicguide.com"
ROOT = "maple-classic-cheat-sheet"
KEY = open(f"{ROOT}/src/indexnow-key.txt").read().strip()


def lastmod(rev):
    try:
        return json.loads(subprocess.check_output(["git", "show", f"{rev}:{ROOT}/data/lastmod.json"], stderr=subprocess.DEVNULL))
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "maple-indexnow/1.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def live_dates():
    xml = get(f"{SITE}/sitemap.xml?t={int(time.time())}")
    out = {}
    for block in xml.split("<url>")[1:]:
        loc = block.split("<loc>")[1].split("</loc>")[0].replace(SITE, "")
        out[loc] = block.split("<lastmod>")[1].split("</lastmod>")[0] if "<lastmod>" in block else ""
    return out


now = lastmod("HEAD")
before = os.environ.get("BEFORE", "")
old = lastmod(before) if before and set(before) != {"0"} else {}
changed = sorted(p for p, v in now.items() if old.get(p) != v)
if os.environ.get("SUBMIT_ALL") == "true" or not changed:
    changed, reason = sorted(now), "every page (no page content changed, or a full submit was asked for)"
else:
    reason = f"{len(changed)} page(s) whose content changed"
print(f"Submitting {reason}: {changed}")

# Wait for Vercel: the key file must be live, and the live sitemap must show the new dates.
deadline = time.time() + 15 * 60
time.sleep(60)
while True:
    try:
        key_ok = get(f"{SITE}/{KEY}.txt").strip() == KEY
        live = live_dates()
        fresh = all(live.get(p) == now[p]["d"] for p in changed if p in now)
        if key_ok and fresh:
            break
        print(f"Waiting for the deploy (key file live: {key_ok}, new dates live: {fresh})")
    except (urllib.error.URLError, IndexError, TimeoutError) as e:
        print(f"Waiting for the deploy ({e})")
    if time.time() > deadline:
        sys.exit("The deploy didn't show up within 15 minutes; nothing was submitted.")
    time.sleep(20)
time.sleep(30)  # let the CDN settle for pages whose only change was the title or description

body = {"host": HOST, "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt", "urlList": [SITE + p for p in changed]}
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        status = r.status
except urllib.error.HTTPError as e:
    sys.exit(f"IndexNow said {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
msg = f"IndexNow accepted {len(changed)} URL(s) (HTTP {status})."
print(msg)
summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    with open(summary, "a") as f:
        f.write(f"### {msg}\n\n" + "\n".join(f"- {SITE}{p}" for p in changed) + "\n")
