// Maple Classic Guide: "your run" picker, search, secret filters, tools.
(function () {
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
    (el.tagName === "H2" ? el : (el.querySelector("h3, h2") || el)).appendChild(b);
  });

  // ---- Return Scroll: back to the top once you've scrolled a bit
  var rs = document.createElement("button");
  rs.type = "button"; rs.className = "return-scroll"; rs.setAttribute("aria-label", "Back to top");
  rs.innerHTML = '<span aria-hidden="true">📜</span><b>Return</b>';
  document.body.appendChild(rs);
  rs.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: matchMedia("(prefers-reduced-motion:reduce)").matches ? "auto" : "smooth" }); toast("Used a Return Scroll. Whoosh!"); });
  var lastY = window.scrollY;
  var onScroll = function () {
    var y = window.scrollY;
    rs.classList.toggle("on", y > 900);
    // tuck the phone tab bar away while scrolling down, bring it back on any scroll up
    if (Math.abs(y - lastY) > 6) { document.body.classList.toggle("tb-hidden", y > lastY && y > 240 && window.innerHeight + y < document.documentElement.scrollHeight - 40); lastY = y; }
  };
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

  // ---- Tap to explain: dotted words (AP, KPQ, mesos...) and the Confirmed/Likely tags open a little bubble.
  // Hover titles never show on phones, so every explanation also works with a tap or the keyboard.
  var tipEl = null, tipFor = null, tipY = 0;
  function hideTip() { if (tipEl) tipEl.classList.remove("on"); tipFor = null; }
  function showTip(el) {
    var text = el.getAttribute("data-tip") || el.getAttribute("title");
    if (!text) return;
    if (tipFor === el) { hideTip(); return; }
    if (!tipEl) { tipEl = document.createElement("div"); tipEl.className = "tipbub"; tipEl.setAttribute("role", "status"); document.body.appendChild(tipEl); }
    tipEl.style.left = "0px"; tipEl.style.top = "0px";
    tipEl.innerHTML = "<b>" + esc(el.textContent.trim()) + "</b> " + esc(text);
    tipEl.classList.add("on"); tipFor = el; tipY = window.scrollY;
    var r = el.getBoundingClientRect(), w = tipEl.offsetWidth, h = tipEl.offsetHeight;
    var left = Math.max(10, Math.min(window.innerWidth - w - 10, r.left + r.width / 2 - w / 2));
    var top = r.top - h - 8;
    if (top < 64) top = r.bottom + 8;
    tipEl.style.left = left + "px"; tipEl.style.top = top + "px";
  }
  var TIPS = "abbr[title], .chip[title], [data-tip]";
  document.querySelectorAll("main abbr[title], main .chip[title]").forEach(function (el) { if (!el.closest("a, button")) el.tabIndex = 0; });
  document.addEventListener("click", function (e) {
    var el = e.target.closest(TIPS);
    if (el && !el.closest("a, button, summary")) { showTip(el); return; }
    if (tipFor && !e.target.closest(".tipbub")) hideTip();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hideTip();
    else if ((e.key === "Enter" || e.key === " ") && document.activeElement && document.activeElement.matches && document.activeElement.matches(TIPS)) { e.preventDefault(); showTip(document.activeElement); }
  });
  window.addEventListener("scroll", function () { if (tipFor && Math.abs(window.scrollY - tipY) > 40) hideTip(); }, { passive: true });

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

  // ---- Search: quick answers from search.json (levels, items, slang), then full-text matches from Pagefind
  var box = document.getElementById("search"), q = document.getElementById("q"), hits = document.getElementById("hits");
  var idx = null, sel = 0, quickHits = [], pfHits = [], pfState = "idle", pf = null, pfTok = 0, pfTimer = 0, curText = "";
  var STOP = {}, LVW = {};
  ("a an the to of in on at for from and or is are am be do does did how what whats where wheres when which who why should can could would " +
   "i im me my you your it its get got go find vs versus with about there this that want need please much many some any").split(" ").forEach(function (w) { STOP[w] = 1; });
  "lv lvl level levels leveling train training grind grinding spot spots map maps exp xp".split(" ").forEach(function (w) { LVW[w] = 1; });
  // Words players type -> words the guide uses
  var SYN = { archer: ["bowman", "hunter", "crossbowman"], archers: ["bowman"], bow: ["bowman", "hunter"], mage: ["magician", "wizard", "cleric"], mages: ["magician"],
    wizard: ["magician"], sin: ["assassin"], dit: ["bandit"], xbow: ["crossbowman", "crossbow"], priest: ["cleric"], fp: ["f/p", "fire/poison"], il: ["i/l", "ice/lightning"],
    "1st": ["first"], first: ["1st"], "2nd": ["second"], second: ["2nd"], "3rd": ["third"], third: ["3rd"], "4th": ["fourth"],
    money: ["mesos", "meso"], meso: ["mesos"], cash: ["nx"], nx: ["cash shop"], train: ["grind", "leveling"], grind: ["train", "leveling"], leveling: ["grind", "train"], xp: ["exp"],
    boat: ["maple island"], pq: ["party quest"], jq: ["jump quest"], hpq: ["moon bunny"], home: ["housing", "house"], house: ["housing"], shop: ["store", "free market"],
    fm: ["free market"], jobup: ["advancement"], advance: ["advancement"], founders: ["founder"], noob: ["beginner", "new player"], newbie: ["beginner"] };
  var TRY = ["lvl 35", "Halloween", "Iron Ore", "best class", "KPQ", "2nd job"];
  function norm(s) { return " " + String(s || "").toLowerCase().replace(/['’]/g, "").replace(/[^a-z0-9%/+]+/g, " ").trim() + " "; }
  // Words match at the start of a word ("mush" finds Mushmom); 1-2 letter words must match a whole word ("sp" isn't "Spearman")
  function has(hay, w) {
    var alts = [w].concat(SYN[w] || []);
    for (var i = 0; i < alts.length; i++) {
      var a = alts[i];
      if (a.length <= 2 ? new RegExp("[ /]" + a + "[ /]").test(hay) : hay.indexOf(" " + a) >= 0) return a;
    }
    return null;
  }
  function score(it, words, lvl, any, lvTalk) {
    var t = it._t || (it._t = norm(it.t)), hay = it._h || (it._h = norm(it.t + " " + (it.k || "") + " " + (it.x || "") + " " + (it.d || ""))), s = 0, got = 0;
    for (var i = 0; i < words.length; i++) {
      var m = has(hay, words[i]);
      if (!m) { if (any) continue; return 0; }
      if (any && words[i].length <= 2) continue;  // "hp wash": don't match on "hp" alone
      got++; s += t.indexOf(" " + m) >= 0 ? 3 : 1; if (t.indexOf(" " + m + " ") >= 0) s += 1;
    }
    if (any && !got) return 0;
    if (lvl != null) { if (it.lo == null || lvl < it.lo || lvl > it.hi) return 0; s += 5; }
    if (lvTalk && it.u.indexOf("/leveling/") === 0) s += 3;  // "where to level" -> the leveling page first
    return s + (it.k === "page" ? 0.5 : 0);
  }
  function parse(text) {
    var raw = norm(text).trim().split(" ").filter(Boolean), lvl = null, words = [];
    raw.forEach(function (w) {
      var m = w.match(/^(?:lv|lvl|level)?(\d{1,3})$/);
      if (m && +m[1] >= 1 && +m[1] <= 100 && lvl == null) lvl = +m[1]; else if (!STOP[w]) words.push(w);
    });
    if (lvl != null && !words.every(function (w) { return LVW[w]; })) { words.push(String(lvl)); lvl = null; }  // "cleric 35": a word, not a level search
    else if (lvl != null) words = [];  // "where to train 35", "lvl 35"
    if (!words.length && lvl == null) words = raw;
    return { words: words, lvl: lvl };
  }
  function quick(text) {
    if (!text.trim()) return idx.filter(function (i) { return i.k === "page"; });
    var p = parse(text), lvTalk = p.lvl == null && p.words.length > 0 && p.words.every(function (w) { return LVW[w]; });
    var run = function (any) {
      return idx.map(function (i) { return [score(i, p.words, p.lvl, any, lvTalk), i]; }).filter(function (x) { return x[0] > 0; })
        .sort(function (a, b) { return b[0] - a[0]; }).slice(0, 8).map(function (x) { return x[1]; });
    };
    var r = run(false);
    return r.length || p.words.length < 2 ? r : run(true);  // nothing has every word: show what has the most
  }
  function loadPF() {
    if (!pf) pf = import("/pagefind/pagefind.js").then(function (m) {
      return Promise.resolve(m.options ? m.options({ excerptLength: 22 }) : null).then(function () { return m; });
    }).catch(function () { return null; });
    return pf;
  }
  function fullText(text, tok) {
    loadPF().then(function (m) {
      if (!m || tok !== pfTok) return null;
      return m.search(text).then(function (res) { return tok === pfTok ? Promise.all(res.results.slice(0, 5).map(function (r) { return r.data(); })) : null; });
    }).then(function (rows) {
      if (tok !== pfTok) return;
      var seen = {};
      pfHits = (rows || []).map(function (d) {
        var subs = d.sub_results || [], best = subs.slice().sort(function (a, b) { return ((b.locations || []).length) - ((a.locations || []).length); })[0] || d;
        var page = (d.meta && d.meta.title) || d.url;
        return { u: best.url || d.url, t: page, sub: best.title && best.title !== page ? best.title : "", ex: String(best.excerpt || d.excerpt || "").replace(/<(?!\/?mark>)[^>]*>/g, "") };
      }).filter(function (h) { if (seen[h.u]) return false; seen[h.u] = 1; return true; });
      pfState = "done"; draw();
    }).catch(function () { if (tok === pfTok) { pfHits = []; pfState = "done"; draw(); } });
  }
  function draw() {
    if (!hits) return;
    if (!idx) { hits.innerHTML = '<li class="muted">Loading…</li>'; return; }
    var html = quickHits.map(function (it) {
      return '<li role="option"><a href="' + esc(it.u) + '"><span class="h-t"><b>' + esc(it.t) + "</b>" + (it.d ? "<small>" + esc(it.d) + "</small>" : "") +
        '</span><span class="h-k">' + esc(it.k === "page" ? "Page" : it.k) + "</span></a></li>";
    }).join("");
    if (pfHits.length) {
      html += '<li class="h-sec" aria-hidden="true">On the pages</li>' + pfHits.map(function (h) {
        return '<li role="option" class="pf"><a href="' + esc(h.u) + '"><span class="h-t"><b>' + esc(h.t) + (h.sub ? ' <i>› ' + esc(h.sub) + "</i>" : "") + "</b><small>" + h.ex + "</small></span></a></li>";
      }).join("");
    } else if (curText.trim().length >= 3 && pfState === "busy") html += '<li class="muted h-sec">Searching every page…</li>';
    if (!quickHits.length && !pfHits.length && pfState !== "busy") {
      html = '<li class="muted empty"><span aria-hidden="true">🐌</span><div>Even the snail looked everywhere. Try one of these:<p class="h-try">' +
        TRY.map(function (t) { return '<button type="button" data-try="' + esc(t) + '">' + esc(t) + "</button>"; }).join("") + "</p></div></li>";
    }
    hits.innerHTML = html;
    var li = hits.querySelectorAll("[role=option]");
    sel = Math.min(sel, Math.max(0, li.length - 1));
    li.forEach(function (x, i) { x.setAttribute("aria-selected", String(i === sel)); });
  }
  function renderHits(text) {
    curText = text; sel = 0; pfTok++; clearTimeout(pfTimer);
    quickHits = idx ? quick(text) : []; pfHits = [];
    var tok = pfTok, t = text.trim();
    pfState = t.length >= 3 ? "busy" : "idle";
    if (pfState === "busy") pfTimer = setTimeout(function () { fullText(t, tok); }, 160);
    draw();
  }
  function openSearch() {
    if (!box) return;
    box.hidden = false; document.body.classList.add("noscroll"); q.value = ""; renderHits(""); q.focus();
    if (!idx) fetch("/search.json").then(function (r) { return r.json(); }).then(function (d) { idx = d; renderHits(q.value); }).catch(function () {});
    loadPF();
  }
  function closeSearch() { if (box) { box.hidden = true; document.body.classList.remove("noscroll"); } }
  document.addEventListener("click", function (e) {
    var tr = e.target.closest("[data-try]");
    if (tr) { q.value = tr.dataset.try; renderHits(q.value); q.focus(); return; }
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
    } else if (box && !box.hidden && e.key === "Enter") {
      var a = hits.querySelectorAll("[role=option] a")[sel];
      if (a) { e.preventDefault(); location.href = a.getAttribute("href"); closeSearch(); }
    }
  });
  if (q) q.addEventListener("input", function () { renderHits(q.value); });

  // ---- "Was this page right?" feedback (Web3Forms when a key is set, email otherwise)
  var fb = document.querySelector(".fb");
  if (fb) {
    var fbForm = fb.querySelector(".fb-form"), fbKey = fb.dataset.fbKey, page = location.pathname;
    fb.addEventListener("click", function (e) {
      var b = e.target.closest("[data-fb]"); if (!b) return;
      fb.querySelectorAll("[data-fb]").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      if (b.dataset.fb === "up") { fbForm.hidden = true; store.set("mccs-fb" + page, "up"); toast("Thanks! +1 EXP for the guide"); }
      else { fbForm.hidden = false; fbForm.querySelector("textarea").focus(); }
    });
    fbForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var msg = fbForm.message.value.trim(); if (!msg || fbForm.botcheck.checked) return;
      var subject = "Maple Guide fix: " + page;
      if (!fbKey) { location.href = "mailto:robertlazau@gmail.com?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(msg + "\n\nPage: " + location.href); return; }
      var btn = fbForm.querySelector("button[type=submit]"); btn.disabled = true; btn.textContent = "Sending…";
      fetch("https://api.web3forms.com/submit", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ access_key: fbKey, subject: subject, from_name: "Maple Classic Guide", page: location.href, message: msg }) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.success) throw new Error(d.message || "failed");
          fb.innerHTML = '<p class="fb-q">Got it, thank you! 🍁</p><p class="muted">We check every report against the game and log fixes on <a href="/updates/">What\'s new</a>.</p>';
          toast("Fix sent! +5 EXP");
        })
        .catch(function () { btn.disabled = false; btn.textContent = "Send fix"; toast("Couldn't send. Try again in a sec?"); });
    });
  }

  // ---- EXP calculator (/tools/)
  var xc = document.getElementById("expcalc");
  if (xc) {
    var T = JSON.parse(document.getElementById("exp-data").textContent).toNext;
    var f = { lv: document.getElementById("xc-lv"), pct: document.getElementById("xc-pct"), goal: document.getElementById("xc-goal"), rate: document.getElementById("xc-rate") };
    var xo = document.getElementById("xc-out"), timerEl = document.getElementById("xc-timer"), startBtn = document.getElementById("xc-start");
    var fmt = function (n) { return Math.round(n).toLocaleString("en-US"); };
    var big = function (n) { return n >= 1e9 ? (n / 1e9).toFixed(n >= 1e10 ? 1 : 2) + "B" : n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e4 ? Math.round(n / 1e3) + "k" : fmt(n); };
    var dur = function (h) {
      if (!isFinite(h)) return "";
      if (h < 1) return Math.max(1, Math.round(h * 60)) + " min";
      if (h < 48) return Math.floor(h) + " h " + Math.round((h % 1) * 60) + " min";
      if (h < 24 * 365) return Math.round(h / 24) + " days of non-stop grinding";
      return (h / 24 / 365).toFixed(1) + " years of non-stop grinding";
    };
    var saved = store.get("mccs-exp") || {};
    var qs2 = new URLSearchParams(location.search);
    if (qs2.get("lv") && Number(qs2.get("lv")) !== Number(saved.lv)) { saved.lv = Number(qs2.get("lv")); saved.pct = 0; }
    ["lv", "pct", "goal", "rate"].forEach(function (k) { if (saved[k] != null && saved[k] !== "") f[k].value = saved[k]; });
    if (qs2.get("lv") && !qs2.get("goal")) f.goal.value = Math.min(100, Number(qs2.get("lv")) + 1);
    var clamp = function (v, a, b) { v = Number(v); return isNaN(v) ? a : Math.max(a, Math.min(b, v)); };
    var expAt = function () { var lv = clamp(f.lv.value, 1, 99); return { lv: lv, pct: clamp(f.pct.value, 0, 99.99) }; };
    var calc = function () {
      var c = expAt(), goal = clamp(f.goal.value, c.lv + 1, 100), rate = Number(f.rate.value) || 0;
      store.set("mccs-exp", { lv: f.lv.value, pct: f.pct.value, goal: f.goal.value, rate: f.rate.value });
      var need = T[c.lv - 1] * (1 - c.pct / 100);
      for (var l = c.lv + 1; l < goal; l++) need += T[l - 1];
      var toNext = T[c.lv - 1] * (1 - c.pct / 100);
      var h = '<div class="xc-big"><span>EXP to level ' + goal + '</span><b>' + big(need) + '</b><small>' + fmt(need) + ' EXP</small></div>';
      if (rate > 0) {
        var hrs = need / rate, eta = new Date(Date.now() + hrs * 36e5);
        h += '<div class="xc-big"><span>At ' + big(rate) + ' EXP/hour</span><b>' + dur(hrs) + '</b>' + (hrs < 24 * 60 ? '<small>Done around ' + eta.toLocaleString(undefined, { weekday: "short", hour: "numeric", minute: "2-digit" }) + '</small>' : '') + '</div>';
        h += '<p class="xc-line">Next level (' + (c.lv + 1) + ') in <b>' + dur(toNext / rate) + '</b>.</p>';
      } else h += '<p class="xc-line">Add your EXP per hour (or measure it below) to see how long that takes.</p>';
      var quip = goal >= 100 && c.lv >= 90 ? "Level 99 to 100 alone is 9.5 billion EXP. Bring snacks. Lots of snacks."
        : goal > 90 ? "Heads up: from level 90 every level costs 2.1× the one before. The wall is real."
        : goal >= 30 && c.lv < 30 ? "Level 30 means your 2nd job test. Stock up on potions first."
        : goal >= 10 && c.lv < 10 ? "Level 10 means 1st job. Ride the taxi to your job town before you advance (Beginner discount)." : "";
      if (quip) h += '<p class="xc-quip">' + esc(quip) + '</p>';
      xo.innerHTML = h;
    };
    Object.keys(f).forEach(function (k) { f[k].addEventListener("input", calc); });
    // stopwatch: measure EXP/hour from two readings
    var run = store.get("mccs-exp-run");
    var tick = function () {
      if (!run) { timerEl.textContent = ""; startBtn.textContent = "⏱ Measure my EXP/hour"; return; }
      var m = Math.floor((Date.now() - run.t) / 60000);
      startBtn.textContent = "✅ Stop & calculate"; timerEl.textContent = "Measuring… " + m + " min. Update your level and EXP %, then tap stop.";
    };
    var totalAt = function (lv, pct) { var s = 0; for (var i = 1; i < lv; i++) s += T[i - 1]; return s + T[lv - 1] * pct / 100; };
    startBtn.addEventListener("click", function () {
      var c = expAt();
      if (!run) { run = { t: Date.now(), lv: c.lv, pct: c.pct }; store.set("mccs-exp-run", run); toast("Stopwatch started. Go grind!"); tick(); return; }
      var hrs = (Date.now() - run.t) / 36e5, gained = totalAt(c.lv, c.pct) - totalAt(run.lv, run.pct);
      if (hrs < 1 / 60 || gained <= 0) { toast("Grind a bit longer, then update your EXP %."); return; }
      f.rate.value = Math.round(gained / hrs); run = null; store.set("mccs-exp-run", null); tick(); calc();
      toast("Measured: " + big(Number(f.rate.value)) + " EXP/hour");
    });
    setInterval(tick, 30000); tick(); calc();
  }

  // ---- Scroll simulator (/tools/)
  var ss = document.getElementById("scrollsim");
  if (ss) {
    var G = { lesser: { p: 1, n: "Lesser" }, inter: { p: 0.6, n: "Intermediate" }, greater: { p: 0.1, n: "Greater" }, chaos: { p: 0.1, n: "Chaos", boom: 0.5 } };
    // Classic launch values per scroll type: weapon attack 1/2/4/5, magic attack 2/4/8/10, stats 1/2/3/4
    var T = { watk: { lesser: 1, inter: 2, greater: 4, chaos: 5, u: "ATK", w: "Weapon" }, matk: { lesser: 2, inter: 4, greater: 8, chaos: 10, u: "M.ATK", w: "Staff" }, stat: { lesser: 1, inter: 2, greater: 3, chaos: 4, u: "stat", w: "Item" } };
    var typeEl = document.getElementById("ss-type");
    var ty = function () { return T[(typeEl && typeEl.value) || "watk"]; };
    var grade = document.getElementById("ss-grade"), slotsIn = document.getElementById("ss-slots"), itemEl = document.getElementById("ss-item"), log = document.getElementById("ss-log");
    var it;
    var fresh = function () { it = { slots: Math.max(1, Math.min(10, Number(slotsIn.value) || 7)), plus: 0, used: 0, pass: 0, boom: false }; log.innerHTML = ""; draw(); };
    var draw = function () {
      var left = it.slots - it.used;
      itemEl.className = "item" + (it.boom ? " boom" : "");
      itemEl.innerHTML = it.boom ? '<b>💥 BOOM</b><span>Your item is gone. That\'s Chaos for you.</span>'
        : '<b>' + ty().w + ' +' + it.plus + ' ' + ty().u + '</b><span>' + left + ' slot' + (left === 1 ? "" : "s") + ' left · ' + it.pass + ' of ' + it.used + ' passed</span>';
      document.getElementById("ss-one").disabled = document.getElementById("ss-all").disabled = it.boom || left <= 0;
    };
    var one = function () {
      if (it.boom || it.used >= it.slots) return;
      var g = G[grade.value], ok = Math.random() < g.p, li = document.createElement("li");
      it.used++;
      var gain = ty()[grade.value];
      if (ok) { it.plus += gain; it.pass++; li.className = "ok"; li.textContent = "✨ " + g.n + " passed: +" + gain; }
      else if (g.boom && Math.random() < g.boom) { it.boom = true; li.className = "boom"; li.textContent = "💥 " + g.n + " failed and destroyed the item"; }
      else { li.className = "fail"; li.textContent = "💨 " + g.n + " failed (slot used)"; }
      log.prepend(li); draw();
    };
    document.getElementById("ss-one").addEventListener("click", one);
    document.getElementById("ss-all").addEventListener("click", function () { while (!it.boom && it.used < it.slots) one(); if (!it.boom && it.used) toast(it.plus >= it.slots * ty().inter ? "Perfect item! Screenshot it." : "Done: +" + it.plus + " " + ty().u); });
    if (typeEl) typeEl.addEventListener("change", fresh);
    document.getElementById("ss-reset").addEventListener("click", fresh);
    slotsIn.addEventListener("change", fresh);
    fresh();
  }

  // ---- "More" menu on the phone tab bar
  var moreBtn = document.querySelector("[data-more]"), sheet = document.getElementById("more-sheet");
  if (moreBtn && sheet) {
    var setMore = function (open) {
      sheet.hidden = !open; moreBtn.setAttribute("aria-expanded", String(open));
      document.documentElement.style.overflow = open ? "hidden" : "";
      if (open) sheet.querySelector(".more-box").focus({ preventScroll: true }); else moreBtn.focus({ preventScroll: true });
    };
    moreBtn.addEventListener("click", function () { setMore(sheet.hidden); });
    sheet.addEventListener("click", function (e) { if (e.target === sheet || e.target.closest("[data-more-close]")) setMore(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !sheet.hidden) setMore(false); });
  }

  // ---- Event countdowns (/news/) and the home launch banner
  var nowT = Date.now();
  document.querySelectorAll("[data-at]").forEach(function (el) {
    var at = Date.parse(el.dataset.at), card = el.closest(".evt"), badge = card && card.querySelector(".evt-live");
    if (!badge || isNaN(at)) return;
    var days = Math.ceil((at - nowT) / 86400000);
    var endT = el.dataset.end ? Date.parse(el.dataset.end) : NaN;
    if (!isNaN(endT) && nowT >= endT) { badge.textContent = "Ended"; badge.className = "evt-live off"; }
    else if (nowT >= at) { badge.textContent = "Live now"; badge.className = "evt-live on"; }
    else { badge.textContent = days <= 1 ? "Tomorrow" : "In " + days + " days"; badge.className = "evt-live soon"; }
  });
  var lb = document.querySelector("[data-launch-news]");
  if (lb && nowT >= Date.parse("2026-10-21T18:00:00Z")) lb.textContent = "Classic World is live: events and patch notes";

  // ---- Top bar dropdowns: one open at a time, close on outside click or Escape
  var dds = document.querySelectorAll(".nav .dd");
  dds.forEach(function (d) { d.addEventListener("toggle", function () { if (d.open) dds.forEach(function (o) { if (o !== d) o.open = false; }); }); });
  document.addEventListener("click", function (e) { if (!e.target.closest(".nav .dd")) dds.forEach(function (d) { d.open = false; }); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") dds.forEach(function (d) { if (d.open) { d.open = false; d.querySelector("summary").focus(); } }); });

  // ---- Deadline countdowns (home): hide anything past its date
  document.querySelectorAll("[data-left]").forEach(function (el) {
    var end = Date.parse(el.dataset.left), host = el.closest("[data-dl]");
    if (isNaN(end)) return;
    var ms = end - nowT;
    if (ms <= 0) { if (host) host.hidden = true; return; }
    var d = Math.floor(ms / 86400000);
    el.textContent = d < 1 ? "Last day!" : d === 1 ? "1 day left" : d + " days left";
    if (d < 3) el.classList.add("urgent");
  });
  var dlb = document.querySelector(".dlbar");
  if (dlb && !dlb.querySelector("[data-dl]:not([hidden])")) dlb.hidden = true;

  // ---- Citizenship grade planner (/citizenship/): saved on this device only
  var gsel = document.getElementById("gsel"), gdEl = document.getElementById("gdata");
  if (gsel && gdEl) {
    var gd = JSON.parse(gdEl.textContent), gout = document.getElementById("gout");
    var drawG = function () {
      var g = Number(gsel.value), n = gd[g];
      document.querySelectorAll("tr[data-g]").forEach(function (tr) { var x = Number(tr.dataset.g); tr.classList.toggle("have", x <= g); tr.classList.toggle("next", x === g + 1); });
      if (g === 0) gout.innerHTML = "<b>Next:</b> sign up at level 12 with Arthur (Henesys) or Roxy (Kerning).";
      else if (!n) gout.innerHTML = "<b>Citizen of Honor!</b> You maxed it. Enjoy those earrings.";
      else gout.innerHTML = "<b>Next: grade " + n[0] + ", " + esc(n[1]) + ".</b> Level " + n[2] + " and " + n[3].toLocaleString("en-US") + " points, about " + n[7] + " days. Unlocks: " + esc(n[6]) + ".";
    };
    var sg = store.get("mccs-cit");
    if (sg != null) gsel.value = String(sg);
    gsel.addEventListener("change", function () { store.set("mccs-cit", Number(gsel.value)); drawG(); if (Number(gsel.value) === 2) toast("Grade 2! Go buy that house 🏠"); });
    drawG();
  }

  // ---- The Journey Begins gift tracker (/events/)
  var jbEl = document.querySelector("[data-jb]");
  if (jbEl) {
    var got = store.get("mccs-jb") || [], jbBtns = jbEl.querySelectorAll(".jb-g button"), jbOut = document.getElementById("jb-out");
    var drawJb = function () {
      jbBtns.forEach(function (b, i) { b.setAttribute("aria-pressed", String(got.indexOf(i) > -1)); });
      jbOut.textContent = got.length + " of 14 claimed" + (got.length === 14 ? " 🎉" : "");
    };
    jbBtns.forEach(function (b, i) {
      b.addEventListener("click", function () {
        var k = got.indexOf(i);
        if (k > -1) got.splice(k, 1); else { got.push(i); toast(got.length === 14 ? "All 14 gifts! Nice." : "Gift claimed! +1 EXP"); }
        store.set("mccs-jb", got); drawJb();
      });
    });
    drawJb();
  }

  // ---- Hit chance checker (/leveling/#hit), NiaMeowDB's hit formula
  var hc = document.getElementById("hitchk");
  if (hc) {
    var hl = document.getElementById("hc-lv"), ha = document.getElementById("hc-acc"), sv = store.get("mccs-acc");
    if (sv) { hl.value = sv.lv; ha.value = sv.acc; }
    var phit = function (acc, plv, mlv, eva) {
      var L = Math.max(0, mlv - plv), A = acc * 100 / (10 * L + 255);
      if (A <= 0) return 0;
      var f = 0.15 + 0.20 / (1 + Math.exp((A - eva) / 12)), q = eva / A;
      if (q <= 1 - f) return 1; if (q >= 1 + f) return 0;
      return (1 + f - q) / (2 * f);
    };
    var drawH = function () {
      var lv = Math.max(1, Math.min(100, Number(hl.value) || 1)), acc = Math.max(0, Number(ha.value) || 0);
      store.set("mccs-acc", { lv: lv, acc: acc });
      hc.querySelectorAll("tr[data-lv]").forEach(function (tr) {
        var mlv = Number(tr.dataset.lv), av = Number(tr.dataset.av), pct = Math.floor(phit(acc, lv, mlv, av) * 100), need = 0;
        for (var a = 1; a < 800; a++) { if (phit(a, lv, mlv, av) >= 1) { need = a; break; } }
        var c = tr.querySelector(".hc-out");
        c.className = "hc-out " + (pct >= 100 ? "ok" : pct >= 70 ? "meh" : "bad");
        c.innerHTML = "<b>" + pct + "%</b><small>" + (pct >= 100 ? "never miss" : "need " + need + " ACC") + "</small>";
      });
    };
    [hl, ha].forEach(function (x) { x.addEventListener("input", drawH); });
    drawH();
  }

  // ---- Boss respawn timers (/bosses/): saved on this device only
  var timers = store.get("mccs-boss") || {};
  var tEls = document.querySelectorAll(".timer[data-boss]");
  function fmt(ms) { var m = Math.max(0, Math.round(ms / 60000)); return m >= 60 ? Math.floor(m / 60) + "h " + (m % 60) + "m" : m + "m"; }
  function drawTimers() {
    var now = Date.now();
    tEls.forEach(function (el) {
      var t = timers[el.dataset.boss], out = el.querySelector(".timer-out"), b = el.querySelector("[data-kill]");
      if (!t) { out.textContent = ""; out.classList.remove("ready"); b.textContent = "⏱ I just killed it"; return; }
      var lo = t + Number(el.dataset.min) * 60000, hi = t + Number(el.dataset.max) * 60000;
      b.textContent = "⏱ Killed it again";
      if (now < lo) { out.classList.remove("ready"); out.textContent = "Back in " + fmt(lo - now) + (hi > lo ? " to " + fmt(hi - now) : ""); }
      else if (now < hi) { out.classList.add("ready"); out.textContent = "Spawn window open now! Up to " + fmt(hi - now) + " left."; }
      else { out.classList.add("ready"); out.textContent = "Should be up. Go check!"; }
    });
  }
  if (tEls.length) {
    tEls.forEach(function (el) {
      el.querySelector("[data-kill]").addEventListener("click", function () {
        timers[el.dataset.boss] = Date.now(); store.set("mccs-boss", timers); drawTimers();
        toast("Timer started. GG!");
      });
    });
    drawTimers(); setInterval(drawTimers, 30000);
  }

  // ---- KPQ combo tracker: tap combos as you try them, long-press or double-tap the winner
  document.querySelectorAll("[data-combo]").forEach(function (box) {
    box.addEventListener("click", function (e) {
      if (e.target.closest(".combo-reset")) { box.querySelectorAll(".combo-g button").forEach(function (b) { b.setAttribute("aria-pressed", "false"); b.classList.remove("win"); }); return; }
      var b = e.target.closest(".combo-g button"); if (!b) return;
      var on = b.getAttribute("aria-pressed") !== "true";
      b.setAttribute("aria-pressed", String(on)); b.classList.remove("win");
      var left = box.querySelectorAll('.combo-g button[aria-pressed="false"]').length;
      if (on && left === 1) toast("Only one left. That's gotta be it!");
    });
    box.addEventListener("dblclick", function (e) {
      var b = e.target.closest(".combo-g button"); if (!b) return;
      b.setAttribute("aria-pressed", "false"); b.classList.add("win"); toast("Cleared! On to the next stage.");
    });
  });

  // ---- Quest checklist (/quests/)
  var qs = document.querySelectorAll(".quest[data-q]");
  if (qs.length) {
    var done = store.get("mccs-quests") || {};
    var drawBands = function () {
      document.querySelectorAll("[data-bandgrid]").forEach(function (g) {
        var all = g.querySelectorAll(".quest").length, d = g.querySelectorAll(".quest.done").length;
        var p = document.querySelector('[data-band="' + g.dataset.bandgrid + '"]');
        if (p) p.textContent = d ? "✓ " + d + "/" + all : "";
      });
    };
    qs.forEach(function (q) {
      var b = q.querySelector(".q-done");
      var set = function (v) { q.classList.toggle("done", v); b.setAttribute("aria-pressed", String(v)); b.textContent = v ? "✓ Done" : "Mark done"; };
      set(!!done[q.dataset.q]);
      b.addEventListener("click", function () {
        var v = !done[q.dataset.q]; if (v) done[q.dataset.q] = 1; else delete done[q.dataset.q];
        store.set("mccs-quests", done); set(v); drawBands();
        if (v) toast("Quest complete! +EXP");
      });
    });
    drawBands();
  }

  // ---- Quest walkthrough (/quests/<slug>/): tick steps as you go; ticking the last one marks the quest done on /quests/ too
  var qp = document.querySelector("[data-qpage]");
  if (qp) {
    var qkey = qp.dataset.qpage, allSteps = store.get("mccs-steps") || {}, mine = allSteps[qkey] || [];
    var qdone = store.get("mccs-quests") || {};
    var boxes = [].slice.call(qp.querySelectorAll(".qstep input"));
    var qbtn = qp.querySelector(".qp-done"), qprog = qp.querySelector(".qp-prog");
    var setQ = function (v) {
      if (v) qdone[qkey] = 1; else delete qdone[qkey];
      store.set("mccs-quests", qdone);
      qbtn.setAttribute("aria-pressed", String(v)); qbtn.textContent = v ? "✓ Quest done" : "Mark quest done";
    };
    var drawQ = function () {
      var n = boxes.filter(function (b) { return b.checked; }).length;
      qprog.textContent = n ? "✓ " + n + "/" + boxes.length : "";
    };
    boxes.forEach(function (b, i) {
      b.checked = mine.indexOf(i) > -1;
      b.closest("li").classList.toggle("ok", b.checked);
      b.addEventListener("change", function () {
        mine = mine.filter(function (x) { return x !== i; }); if (b.checked) mine.push(i);
        allSteps[qkey] = mine; store.set("mccs-steps", allSteps);
        b.closest("li").classList.toggle("ok", b.checked); drawQ();
        if (b.checked && mine.length === boxes.length) { setQ(true); toast("Quest complete! +EXP"); }
      });
    });
    setQ(!!qdone[qkey]); drawQ();
    qbtn.addEventListener("click", function () { var v = !qdone[qkey]; setQ(v); if (v) toast("Quest complete! +EXP"); });
  }

  // ---- Leveling (/leveling/): "I'm level __" picks the best spot, highlights it and scrolls there
  var pickIn = document.getElementById("pick-lv");
  if (pickIn) {
    var pickOut = document.getElementById("pick-out");
    var routeLis = [].slice.call(document.querySelectorAll(".route li[data-from]"));
    var calm = matchMedia("(prefers-reduced-motion:reduce)").matches;
    var pickSpot = function () {
      var lv = Math.round(Number(pickIn.value));
      if (!lv || lv < 1 || lv > 100) { pickOut.textContent = "Type a level from 1 to 100."; return; }
      var inBand = function (li) { return +li.dataset.from <= lv && lv <= +li.dataset.to; };
      var fits = routeLis.filter(function (li) { return inBand(li) && !li.classList.contains("future"); });
      if (!fits.length) fits = routeLis.filter(inBand);
      fits.sort(function (a, b) { return (("all" in b.dataset) - ("all" in a.dataset)) || (b.dataset.from - a.dataset.from) || (a.dataset.to - b.dataset.to); });
      routeLis.forEach(function (x) { x.classList.remove("hit"); });
      var li = fits[0];
      if (!li) { pickOut.textContent = "No set spot at that level. Grind wherever you kill fastest."; return; }
      li.classList.add("hit");
      var name = (li.querySelector(".map").firstChild.textContent || "").trim();
      pickOut.innerHTML = "Level " + lv + "? Head to <b>" + esc(name) + "</b>." + (fits.length > 1 ? " " + (fits.length - 1) + " more option" + (fits.length > 2 ? "s" : "") + " right below it." : "");
      li.scrollIntoView({ behavior: calm ? "auto" : "smooth", block: "start" });
      store.set("mccs-pick-lv", lv);
      if (history.replaceState) history.replaceState(null, "", "#" + li.id);
    };
    var savedLv = store.get("mccs-pick-lv");
    if (savedLv) pickIn.value = savedLv;
    document.getElementById("pick-go").addEventListener("click", pickSpot);
    pickIn.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); pickSpot(); } });
  }

  // ---- Price check (/prices/): search an item, then one tap opens a price site and copies the item name
  var pcData = document.getElementById("pc-data");
  if (pcData) {
    var PC = JSON.parse(pcData.textContent);
    var pcQ = document.getElementById("pc-q"), pcOut = document.getElementById("pc-out");
    var norm = function (t) { return String(t || "").toLowerCase().replace(/[^a-z0-9%]+/g, " ").trim(); };
    var pcCard = function (it) {
      var ic = it.ic ? '<img class="pc-ic" src="' + PC.api + "/item/" + it.ic + '/icon" alt="" referrerpolicy="no-referrer" onerror="this.remove()">' : '<span class="pc-ic emo" aria-hidden="true">📦</span>';
      var price = it.p ? '<p class="pc-p"><b>~' + Number(it.p[0]).toLocaleString("en-US") + " mesos</b> <span>" + esc(it.p[1]) + "</span></p>"
        : '<p class="pc-p muted">No price on this page yet. Check it live:</p>';
      var meta = (it.from && it.from.length ? "<span>Dropped by " + esc(it.from.join(", ")) + "</span>" : "") + (it.use && it.use.length ? "<span>Crafters use it for " + esc(it.use.join(", ")) + "</span>" : "");
      var btns = PC.sites.map(function (s) { return '<a class="btn btn-ghost sm" href="' + s[1] + '" target="_blank" rel="noopener" data-copy="' + esc(it.n) + '">' + esc(s[0]) + " ↗</a>"; }).join("");
      return '<div class="pc-card">' + ic + '<div class="pc-b"><h3>' + esc(it.n) + "</h3>" + price + (meta ? '<p class="pc-m">' + meta + "</p>" : "") + '<div class="pc-btns">' + btns + "</div></div></div>";
    };
    var pcShow = function (text) {
      var q = norm(text);
      if (q.length < 2) { pcOut.innerHTML = ""; return; }
      var hits = PC.items.filter(function (it) { return norm(it.n).indexOf(q) > -1; })
        .sort(function (a, b) { return (norm(b.n).indexOf(q) === 0) - (norm(a.n).indexOf(q) === 0) || (!!b.p - !!a.p) || a.n.length - b.n.length; }).slice(0, 6);
      pcOut.innerHTML = hits.length ? hits.map(pcCard).join("") : pcCard({ n: String(text).trim(), ic: null, from: [], use: [], p: null });
    };
    pcQ.addEventListener("input", function () { pcShow(pcQ.value); });
    document.querySelector(".pc-chips").addEventListener("click", function (e) {
      var b = e.target.closest("[data-item]"); if (!b) return;
      pcQ.value = b.dataset.item; pcShow(pcQ.value); toast("Nice pick. Tap a site to see its live price.");
    });
    pcOut.addEventListener("click", function (e) {
      var a = e.target.closest("[data-copy]"); if (!a) return;
      var n = a.dataset.copy;
      if (navigator.clipboard) navigator.clipboard.writeText(n).then(function () { toast('Copied "' + n + '". Paste it into their search.'); }, function () {});
    });
    var asked = new URLSearchParams(location.search).get("item");
    if (asked) { pcQ.value = asked; pcShow(asked); }
  }

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
  // AP, STR, DEX... become tap-to-explain words in the result boxes
  function gl(s) {
    var done = {};
    return esc(s).replace(/\b(AP|SP|STR|DEX|INT|LUK|HP|MP)\b/g, function (k) {
      if (done[k] || !D.gloss || !D.gloss[k]) return k;
      done[k] = 1; return '<abbr title="' + esc(D.gloss[k]) + '">' + k + "</abbr>";
    });
  }
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
    var now = Date.now(), here = D.route.filter(function (r) { return lv >= r.from && lv <= r.to; });
    var spots = here.filter(function (r) { return !r.opens || now >= Date.parse(r.opens); });
    var soon = here.filter(function (r) { return r.opens && now < Date.parse(r.opens); });
    var next = lv < 10 ? "Hit level 10, then talk to " + c.npc + " in " + c.town + " for 1st job. No stat requirement."
      : lv < 30 ? "2nd job at level 30. " + job.adv.test
      : "You're set until 3rd job drops (planned for 2027). Cap is level 100.";
    var ap = pick(job.ap, lv);
    if (lv < 10 && c.start) ap.unshift("New character: " + c.start[0] + " STR / " + c.start[1] + " DEX / " + c.start[2] + " INT / " + c.start[3] + " LUK.");
    var sp = lv < 10 ? ["Beginner: 3 points each into Three Snails, Recovery and Nimble Feet."] : pick(lv < 30 ? job.sp1 : job.sp2, lv);
    var h = "";
    h += '<div class="box grind"><h3>🗺️ Grind here rn</h3>' + (spots.length ? spots.map(function (r) {
      var mm = r.mm ? '<img class="spot-mm" src="' + D.api + "/map/" + r.mm + '/minimap" alt="Minimap: ' + esc(r.map) + '" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">' : "";
      return '<div class="spot"><div class="spr">' + r.sprites.map(sprite).join("") + '</div><div><b>' + esc(r.map) + '</b><span>' + (r.region ? esc(r.region) + " · " : "") + esc(r.monsters) +
        '</span><span>Monsters are lv ' + esc(String(r.monsterLevel).replace("-", "–")) + "</span>" + mm + '<a href="/leveling/#lv-' + r.from + "-" + r.to + '">How to get there →</a></div></div>';
    }).join("") : "<p>No set spot at this level yet. Grind wherever you kill fastest.</p>") + soon.map(function (r) {
      return '<p class="soon">🔒 Opens ' + new Date(r.opens).toLocaleDateString("en-US", { month: "short", day: "numeric" }) + ': <a href="/leveling/#lv-' + r.from + "-" + r.to + '">' + esc(r.map.split(" (")[0]) + "</a> (lv " + r.from + "–" + r.to + ")</p>";
    }).join("") + "</div>";
    h += '<div class="box"><h3>💪 Your ' + gl("AP") + ' rn</h3><p>' + (ap.length ? ap.map(gl).join("<br>") : gl(job.apSummary)) + "</p></div>";
    h += '<div class="box"><h3>✨ Your ' + gl("SP") + ' rn</h3><p>' + (sp.length ? sp.map(gl).join("<br>") : "Follow the skill order on your build page.") + "</p></div>";
    h += '<div class="box"><h3>⏭️ Next up</h3><p>' + esc(next) + "</p></div>";
    h += '<a class="btn btn-primary full" href="/jobs/' + state.job + '/">Full ' + esc(job.name) + " build →</a>";
    h += '<button type="button" class="btn btn-ghost full share-run">🔗 Share my run</button>';
    if (lv < 100) h += '<a class="btn btn-ghost full" href="/tools/?lv=' + lv + '#exp">⏱ How long until level ' + (lv + 1) + '?</a>';
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
