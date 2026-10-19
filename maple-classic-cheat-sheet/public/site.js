// Maple Classic Cheat Sheet: ads switch, level finder, secret filters.
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

  var esc = function (t) { return String(t == null ? "" : t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };

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

  // ---- Level finder
  var form = document.getElementById("finder");
  var dataEl = document.getElementById("finder-data");
  if (!form || !dataEl) return;
  var D = JSON.parse(dataEl.textContent);
  var out = document.getElementById("finder-out");
  var jobSel = form.querySelector("[name=job]"), lvIn = form.querySelector("[name=lv]");

  function ranges(text) {
    // "Lv11-15", "Lv 30", "Lv31-70", "lv 21-30"
    var m = String(text).match(/lv\s?(\d+)\s*(?:[-–]\s*(\d+))?/i);
    if (!m) return null;
    return [Number(m[1]), Number(m[2] || m[1])];
  }
  function pick(list, lv) {
    var hits = [];
    (list || []).forEach(function (t) { var r = ranges(t); if (r && lv >= r[0] && lv <= r[1]) hits.push(t); });
    return hits;
  }
  function render() {
    var job = D.jobs[jobSel.value]; var lv = Math.max(1, Math.min(100, Number(lvIn.value) || 1));
    if (!job) { out.innerHTML = ""; return; }
    var spots = D.route.filter(function (r) { return lv >= r.from && lv <= r.to; });
    var html = "";
    // what's next
    var next = lv < 10 ? "Make your 1st job at level 10 with " + job.cls.npc + " in " + job.cls.town + ". There's no stat requirement in Classic."
      : lv < 30 ? "2nd job opens at level 30: " + job.adv.test
      : "You're in 2nd job until 3rd job arrives (planned for 2027). Level cap is 100.";
    html += '<div class="box"><h3>Next milestone</h3><p>' + esc(next) + "</p></div>";
    html += '<div class="box"><h3>Train here</h3>' + (spots.length ? "<ul>" + spots.map(function (r) {
      return "<li><b>" + esc(r.map) + "</b> <span class=\"chip c-" + r.confidence + "\">" + r.confidence + "</span><br><span>" + esc(r.monsters) + " (lv " + esc(r.monsterLevel) + ")</span></li>";
    }).join("") + "</ul>" : "<p>No set spot for this level yet. Grind wherever you kill fastest.</p>") + '<p style="margin-top:6px"><a href="/leveling/">Full leveling route →</a></p></div>';
    var ap = pick(job.ap, lv);
    html += '<div class="box"><h3>Your AP right now</h3><p>' + (ap.length ? ap.map(esc).join("<br>") : esc(job.apSummary)) + "</p></div>";
    var sp = lv < 10 ? ["Beginner: put your 9 SP into Three Snails, Recovery and Nimble Feet (3 each)."] : pick(lv < 30 ? job.sp1 : job.sp2, lv);
    html += '<div class="box"><h3>Your SP right now</h3><p>' + (sp.length ? sp.map(esc).join("<br>") : "Follow the skill order on the build page.") + "</p></div>";
    html += '<p><a href="/jobs/' + jobSel.value + '/">Full ' + esc(job.name) + " build →</a></p>";
    out.innerHTML = html;
    try { localStorage.setItem("mccs-finder", JSON.stringify({ job: jobSel.value, lv: lv })); } catch (e) {}
  }
  try { var saved = JSON.parse(localStorage.getItem("mccs-finder") || "null"); if (saved && D.jobs[saved.job]) { jobSel.value = saved.job; lvIn.value = saved.lv; } } catch (e) {}
  form.addEventListener("input", render);
  form.addEventListener("submit", function (e) { e.preventDefault(); render(); });
  render();
})();
