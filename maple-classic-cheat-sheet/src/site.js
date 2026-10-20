// Maple Classic Guide: ads switch, "your run" picker, search, secret filters.
(function () {
  // ---- Ads: paste your AdSense publisher ID here once approved (e.g. "ca-pub-1234567890"). Empty = no ad space shown.
  var ADSENSE_CLIENT = "";
  if (ADSENSE_CLIENT) {
    document.documentElement.classList.add("ads-on");
    var s = document.createElement("script");
    s.async = true; s.crossOrigin = "anonymous";
    s.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + ADSENSE_CLIENT;
    document.head.appendChild(s);
    document.querySelectorAll(".ad").forEach(function (slot) {
      var ins = document.createElement("ins");
      ins.className = "adsbygoogle"; ins.style.display = "block"; ins.style.width = "100%";
      ins.setAttribute("data-ad-client", ADSENSE_CLIENT);
      if (slot.dataset.slot) ins.setAttribute("data-ad-slot", slot.dataset.slot);
      ins.setAttribute("data-ad-format", slot.classList.contains("ad-side") ? "vertical" : "auto");
      ins.setAttribute("data-full-width-responsive", "true");
      slot.appendChild(ins);
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    });
  }

  // ---- Launch label flips to "live now" from Oct 21, 2026 (Pacific)
  var k = document.querySelector("[data-launch]");
  if (k && Date.now() >= Date.parse("2026-10-21T00:00:00-07:00")) k.textContent = "Classic World · live now";

  // ---- Toasts: little game-style popups at the bottom of the screen
  var toastEl = null, toastT = 0;
  function toast(msg) {
    if (!toastEl) { toastEl = document.createElement("div"); toastEl.className = "toast"; toastEl.setAttribute("role", "status"); document.body.appendChild(toastEl); }
    toastEl.textContent = msg; toastEl.classList.add("on");
    clearTimeout(toastT); toastT = setTimeout(function () { toastEl.classList.remove("on"); }, 2200);
  }
  function copy(text, msg) {
    var done = function () { toast(msg || "Link copied! +1 EXP"); };
    if (navigator.share && matchMedia("(pointer:coarse)").matches) {
      navigator.share({ title: document.title, url: text }).catch(function () {});
      return;
    }
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, function () { prompt("Copy this link:", text); });
    else prompt("Copy this link:", text);
  }

  // ---- Copy-link buttons on section headings and secret cards
  document.querySelectorAll("main h2[id], main article[id]").forEach(function (el) {
    var b = document.createElement("button");
    b.type = "button"; b.className = "linkbtn"; b.setAttribute("aria-label", "Copy link to this section"); b.title = "Copy link";
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>';
    b.addEventListener("click", function () { copy(location.origin + location.pathname + "#" + el.id); });
    (el.tagName === "H2" ? el : (el.querySelector("h3") || el)).appendChild(b);
  });

  // ---- Return Scroll: back to the top once you've scrolled a bit
  var rs = document.createElement("button");
  rs.type = "button"; rs.className = "return-scroll"; rs.setAttribute("aria-label", "Back to top");
  rs.innerHTML = '<span aria-hidden="true">📜</span><b>Return</b>';
  document.body.appendChild(rs);
  rs.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: matchMedia("(prefers-reduced-motion:reduce)").matches ? "auto" : "smooth" }); toast("Used a Return Scroll. Whoosh!"); });
  var onScroll = function () { rs.classList.toggle("on", window.scrollY > 900); };
  window.addEventListener("scroll", onScroll, { passive: true }); onScroll();

  // ---- Poke the monsters on the home page: they hop
  document.querySelectorAll(".cast img").forEach(function (img) {
    img.style.pointerEvents = "auto"; img.style.cursor = "pointer";
    img.addEventListener("click", function () { img.classList.remove("hop"); void img.offsetWidth; img.classList.add("hop"); });
    img.addEventListener("animationend", function (ev) { if (ev.animationName === "hop") img.classList.remove("hop"); });
  });

  var esc = function (t) { return String(t == null ? "" : t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var store = {
    get: function (k) { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };

  // ---- Secrets filters
  var fb = document.querySelector("[data-filters]");
  if (fb) {
    fb.addEventListener("click", function (e) {
      var b = e.target.closest("button"); if (!b) return;
      fb.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      var f = b.dataset.f;
      document.querySelectorAll("[data-type]").forEach(function (c) { c.hidden = !(f === "all" || c.dataset.type === f); });
    });
  }

  // ---- Search
  var box = document.getElementById("search"), q = document.getElementById("q"), hits = document.getElementById("hits");
  var idx = null, sel = 0, last = [];
  function openSearch() {
    if (!box) return;
    box.hidden = false; document.body.classList.add("noscroll"); q.value = ""; renderHits(""); q.focus();
    if (!idx) fetch("/search.json").then(function (r) { return r.json(); }).then(function (d) { idx = d; renderHits(q.value); }).catch(function () {});
  }
  function closeSearch() { if (box) { box.hidden = true; document.body.classList.remove("noscroll"); } }
  function score(it, words, lvl) {
    var hay = (it.t + " " + (it.k || "") + " " + (it.x || "")).toLowerCase(), s = 0;
    for (var i = 0; i < words.length; i++) { var w = words[i]; if (!w) continue; var p = hay.indexOf(w); if (p < 0) return 0; s += p === 0 ? 3 : 1; if (it.t.toLowerCase().indexOf(w) >= 0) s += 2; }
    if (lvl != null) { if (it.lo == null) return 0; if (lvl < it.lo || lvl > it.hi) return 0; s += 5; }
    return s;
  }
  function renderHits(text) {
    if (!hits) return;
    if (!idx) { hits.innerHTML = '<li class="muted">Loading…</li>'; return; }
    var t = text.trim().toLowerCase(), lvl = null;
    var m = t.match(/(?:lv|level|lvl)?\s*(\d{1,3})$/);
    if (m && Number(m[1]) <= 100 && /^(lv|level|lvl)?\s*\d{1,3}$/.test(t)) { lvl = Number(m[1]); t = ""; }
    var words = t.split(/\s+/);
    last = !t && lvl == null ? idx.filter(function (i) { return i.k === "page"; })
      : idx.map(function (i) { return [score(i, words, lvl), i]; }).filter(function (x) { return x[0] > 0; }).sort(function (a, b) { return b[0] - a[0]; }).slice(0, 12).map(function (x) { return x[1]; });
    sel = 0;
    hits.innerHTML = last.length ? last.map(function (it, i) {
      return '<li role="option" aria-selected="' + (i === 0) + '"><a href="' + esc(it.u) + '"><b>' + esc(it.t) + "</b><span>" + esc(it.k === "page" ? "Page" : it.k) + "</span></a></li>";
    }).join("") : '<li class="muted empty"><span aria-hidden="true">🐌</span>Even the snail looked everywhere. Try a job, a monster or a level number.</li>';
  }
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-search]")) { e.preventDefault(); openSearch(); }
    else if (e.target.closest("[data-close]") || e.target === box) closeSearch();
    else if (e.target.closest("#hits a")) closeSearch();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && box && box.hidden && !/input|textarea|select/i.test(document.activeElement.tagName)) { e.preventDefault(); openSearch(); }
    else if (e.key === "Escape" && box && !box.hidden) closeSearch();
    else if (box && !box.hidden && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      e.preventDefault(); var li = hits.querySelectorAll("[role=option]"); if (!li.length) return;
      sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + li.length) % li.length;
      li.forEach(function (x, i) { x.setAttribute("aria-selected", String(i === sel)); }); li[sel].scrollIntoView({ block: "nearest" });
    } else if (box && !box.hidden && e.key === "Enter" && last[sel]) { location.href = last[sel].u; closeSearch(); }
  });
  if (q) q.addEventListener("input", function () { renderHits(q.value); });

  // ---- Your run (home page)
  var dataEl = document.getElementById("finder-data");
  if (!dataEl) return;
  var D = JSON.parse(dataEl.textContent);
  var out = document.getElementById("finder-out"), chips = document.getElementById("jobchips");
  var lvIn = document.getElementById("lv"), lvOut = document.getElementById("lvout");
  var saved = store.get("mccs-run") || {};
  var qs = new URLSearchParams(location.search);
  if (qs.get("job") && D.jobs[qs.get("job")]) saved = { cls: D.jobs[qs.get("job")].cls, job: qs.get("job"), lv: Number(qs.get("lv")) || 1 };
  var state = { cls: saved.cls || null, job: saved.job || null, lv: Math.max(1, Math.min(100, Number(saved.lv) || 1)) };
  var MILESTONES = { 10: "Time for your 1st job!", 30: "2nd job time. Go take the test!", 70: "Level 70. You've seen it all (for now).", 100: "LEVEL 100. Absolute legend." };
  function levelUp(from, to) {
    var hit = null;
    Object.keys(MILESTONES).forEach(function (m) { m = Number(m); if (from < m && to >= m) hit = m; });
    if (!hit) return;
    var box = document.querySelector(".lvl"); if (!box) return;
    var el = document.createElement("div"); el.className = "levelup"; el.setAttribute("role", "status");
    el.innerHTML = "<b>LEVEL UP!</b><span>" + esc(MILESTONES[hit]) + "</span>";
    box.appendChild(el); setTimeout(function () { el.remove(); }, 2600);
  }

  function ranges(text) { var m = String(text).match(/lv\s?(\d+)\s*(?:[-–]\s*(\d+))?/i); return m ? [Number(m[1]), Number(m[2] || m[1])] : null; }
  function pick(list, lv) { return (list || []).filter(function (t) { var r = ranges(t); return r && lv >= r[0] && lv <= r[1]; }); }
  function sprite(id) { return '<img src="' + D.api + "/mob/" + id + '/render/stand" alt="" referrerpolicy="no-referrer" onerror="this.remove()">'; }

  function drawChips() {
    document.querySelectorAll(".cls").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.cls === state.cls)); });
    var c = D.classes.filter(function (x) { return x.id === state.cls; })[0];
    chips.innerHTML = c ? c.jobs.map(function (id) {
      return '<button type="button" class="chipbtn" data-job="' + id + '" aria-pressed="' + (id === state.job) + '">' + esc(D.jobs[id].name) + "</button>";
    }).join("") : '<p class="muted">Pick a class first.</p>';
  }
  function render() {
    lvIn.value = state.lv; lvOut.textContent = state.lv;
    lvIn.style.setProperty("--p", ((state.lv - 1) / 99 * 100) + "%");
    store.set("mccs-run", state);
    var job = D.jobs[state.job];
    if (!job) { out.innerHTML = '<p class="muted">Pick your class and job, then slide to your level.</p>'; return; }
    var lv = state.lv, c = D.classes.filter(function (x) { return x.id === job.cls; })[0];
    var spots = D.route.filter(function (r) { return lv >= r.from && lv <= r.to; });
    var next = lv < 10 ? "Hit level 10, then talk to " + c.npc + " in " + c.town + " for 1st job. No stat requirement."
      : lv < 30 ? "2nd job at level 30. " + job.adv.test
      : "You're set until 3rd job drops (planned for 2027). Cap is level 100.";
    var ap = pick(job.ap, lv), sp = lv < 10 ? ["Beginner: 3 points each into Three Snails, Recovery and Nimble Feet."] : pick(lv < 30 ? job.sp1 : job.sp2, lv);
    var h = "";
    h += '<div class="box grind"><h3>🗺️ Grind here rn</h3>' + (spots.length ? spots.map(function (r) {
      return '<div class="spot"><div class="spr">' + r.sprites.map(sprite).join("") + '</div><div><b>' + esc(r.map) + '</b><span>' + esc(r.monsters) + " · lv " + esc(r.monsterLevel) + '</span><a href="/leveling/#lv-' + r.from + "-" + r.to + '">Details →</a></div></div>';
    }).join("") : "<p>No set spot at this level yet. Grind wherever you kill fastest.</p>") + "</div>";
    h += '<div class="box"><h3>💪 Your AP rn</h3><p>' + (ap.length ? ap.map(esc).join("<br>") : esc(job.apSummary)) + "</p></div>";
    h += '<div class="box"><h3>✨ Your SP rn</h3><p>' + (sp.length ? sp.map(esc).join("<br>") : "Follow the skill order on your build page.") + "</p></div>";
    h += '<div class="box"><h3>⏭️ Next up</h3><p>' + esc(next) + "</p></div>";
    h += '<a class="btn btn-primary full" href="/jobs/' + state.job + '/">Full ' + esc(job.name) + " build →</a>";
    h += '<button type="button" class="btn btn-ghost full share-run">🔗 Share my run</button>';
    out.innerHTML = h;
  }
  document.querySelector(".classes").addEventListener("click", function (e) {
    var b = e.target.closest(".cls"); if (!b) return;
    state.cls = b.dataset.cls;
    var c = D.classes.filter(function (x) { return x.id === state.cls; })[0];
    if (!state.job || D.jobs[state.job].cls !== state.cls) state.job = c.jobs[0];
    drawChips(); render();
  });
  chips.addEventListener("click", function (e) { var b = e.target.closest("[data-job]"); if (!b) return; state.job = b.dataset.job; drawChips(); render(); });
  lvIn.addEventListener("input", function () { var was = state.lv; state.lv = Number(lvIn.value); render(); levelUp(was, state.lv); });
  out.addEventListener("click", function (e) {
    if (!e.target.closest(".share-run")) return;
    copy(location.origin + "/?job=" + state.job + "&lv=" + state.lv + "#run", "Run link copied! Send it to your party.");
  });
  document.querySelectorAll(".lv-btn").forEach(function (b) {
    b.addEventListener("click", function () { var was = state.lv; state.lv = Math.max(1, Math.min(100, state.lv + Number(b.dataset.step))); render(); levelUp(was, state.lv); });
  });
  drawChips(); render();
})();
