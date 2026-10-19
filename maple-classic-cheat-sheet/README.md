# Maple Classic Cheat Sheet

Static fan guide for MapleStory Classic World. No dependencies.

- Content lives in `data/*.json` (jobs, leveling, secrets).
- Design and scripts live in `src/` (`style.css`, `site.js`).
- Run `python3 build.py` to rebuild every page into `public/`, then commit. Vercel serves `public/` as-is.

## Turning on ads
1. Get approved for Google AdSense (privacy policy is at /privacy/).
2. Put your publisher ID in `src/site.js` (`ADSENSE_CLIENT = "ca-pub-..."`) and add `public/ads.txt` with the line AdSense gives you.
3. Rebuild and commit. Ad slots (top banner, in-content, desktop sidebar) appear only when the ID is set.

## Updating after a patch
Edit the JSON, change `CHECKED` in `build.py`, rebuild, commit.
