# Maple Classic Cheat Sheet

Static fan guide for MapleStory Classic World. No dependencies.

- Content lives in `data/*.json`; design and scripts live in `src/` (`style.css`, `site.js`).
- Run `python3 build.py` to rebuild every page into `public/` and check it locally. Vercel runs the same build (plus Pagefind search) on every deploy.
- Full notes for whoever works on it next: `CLAUDE.md` and `notes/` at the repo root.

## No ads
The site runs no ads and no ad trackers; it's kept alive by donations (Buy Me a Coffee). The privacy page says so too.

## Updating after a patch
Edit the JSON, change `CHECKED` in `build.py`, rebuild, commit.
