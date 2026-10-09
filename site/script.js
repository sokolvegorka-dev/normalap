(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Год в подвале ---------- */
  var y = $("#year");
  if (y) y.textContent = new Date().getFullYear();

  /* ---------- Шапка: тень при прокрутке + мобильное меню ---------- */
  var nav = $(".nav");
  var onScroll = function () { nav.classList.toggle("scrolled", window.scrollY > 12); };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  var burger = $("#burger");
  var links = $("#navLinks");
  function setMenu(open) {
    links.classList.toggle("open", open);
    nav.classList.toggle("menu-open", open);
    burger.setAttribute("aria-expanded", String(open));
    burger.setAttribute("aria-label", open ? "Закрыть меню" : "Открыть меню");
  }
  burger.addEventListener("click", function () { setMenu(!links.classList.contains("open")); });
  $$("a", links).forEach(function (a) { a.addEventListener("click", function () { setMenu(false); }); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });

  /* ---------- Подсветка текущего раздела в меню ---------- */
  var navMap = {};
  $$("a", links).forEach(function (a) { navMap[a.getAttribute("href")] = a; });
  var secs = ["problem", "solution", "how", "screens", "pricing", "roadmap", "download"]
    .map(function (id) { return document.getElementById(id); }).filter(Boolean);
  if ("IntersectionObserver" in window) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          $$("a", links).forEach(function (a) { a.style.color = ""; a.style.background = ""; });
          var a = navMap["#" + en.target.id];
          if (a && !a.classList.contains("nav__cta-mobile")) { a.style.color = "var(--sage-d)"; a.style.background = "rgba(102,136,117,.12)"; }
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    secs.forEach(function (s) { spy.observe(s); });
  }

  /* ---------- Появление блоков ---------- */
  var reveals = $$(".reveal");
  if (reduce || !("IntersectionObserver" in window)) {
    reveals.forEach(function (el) { el.classList.add("in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Счётчики в полосе цифр ---------- */
  function countUp(el) {
    var to = parseFloat(el.dataset.count);
    var suffix = el.dataset.suffix || "";
    if (reduce || to === 0) { el.textContent = to + suffix; return; }
    var t0 = null, dur = 1400;
    function step(t) {
      if (!t0) t0 = t;
      var p = Math.min((t - t0) / dur, 1);
      var e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(to * e) + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  var counters = $$("[data-count]");
  if ("IntersectionObserver" in window && !reduce) {
    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { countUp(en.target); co.unobserve(en.target); }
      });
    }, { threshold: 0.6 });
    counters.forEach(function (c) { if (parseFloat(c.dataset.count) > 0) c.textContent = "0"; co.observe(c); });
  }

  /* ---------- Вкладки «Экраны приложения» ---------- */
  var tabs = $$(".tab");
  function showTab(name) {
    tabs.forEach(function (t) {
      var on = t.dataset.tab === name;
      t.classList.toggle("on", on);
      t.setAttribute("aria-selected", String(on));
    });
    $$(".pane").forEach(function (p) { p.classList.toggle("on", p.dataset.pane === name); });
    $$(".scr").forEach(function (s) { s.classList.toggle("on", s.dataset.scr === name); });
    var nav2 = $$(".phone--stage .app-nav span");
    var idx = { ration: 1, breeds: 2, weight: 0, game: 3 }[name];
    nav2.forEach(function (n, i) { n.classList.toggle("on", i === idx); });
  }
  tabs.forEach(function (t) { t.addEventListener("click", function () { showTab(t.dataset.tab); stopAuto(); }); });

  var order = ["ration", "breeds", "weight", "game"], cur = 0, timer = null;
  function stopAuto() { if (timer) { clearInterval(timer); timer = null; } }
  var stageEl = $(".stage");
  if (stageEl && "IntersectionObserver" in window && !reduce) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && !timer) {
          timer = setInterval(function () { cur = (cur + 1) % order.length; showTab(order[cur]); }, 5200);
        } else if (!en.isIntersecting) { stopAuto(); }
      });
    }, { threshold: 0.5 }).observe(stageEl);
    stageEl.addEventListener("pointerdown", stopAuto);
  }

  /* ---------- Калькулятор нормы (тот же принцип, что в приложении) ---------- */
  var st = { species: "cat", age: "adult", act: "medium", ster: true };
  var wIn = $("#cWeight"), wOut = $("#cWeightOut");
  var rK = $("#rKcal"), rG = $("#rGrams"), rM = $("#rMeal");

  function factor() {
    var w = parseFloat(wIn.value);
    var young = st.age === "young";
    var der;
    if (st.species === "cat") {
      der = young ? 2.5 : (st.ster ? 1.2 : 1.4);
      if (!young) { if (st.act === "high") der += 0.1; }
    } else {
      der = young ? 2.0 : (st.ster ? 1.4 : 1.6);
      if (!young) { if (st.act === "high") der += 0.15; }
      if (!young && w > 40) der *= 0.95;
    }
    return der;
  }
  function setNum(el, v) {
    if (String(v) === el.textContent) return;
    el.textContent = v;
    el.classList.remove("bump"); void el.offsetWidth; el.classList.add("bump");
  }
  function calc() {
    var w = parseFloat(wIn.value);
    wOut.textContent = String(w.toFixed(1)).replace(".", ",") + " кг";
    var pct = ((w - wIn.min) / (wIn.max - wIn.min)) * 100;
    wIn.style.setProperty("--fill", pct + "%");
    var kcal = Math.round(70 * Math.pow(Math.max(w, 0.3), 0.75) * factor());
    var grams = Math.round(kcal / 370 * 100 / 5) * 5;
    setNum(rK, kcal);
    setNum(rG, grams);
    setNum(rM, Math.round(grams / 3));
  }
  function bindSeg(id, key) {
    var box = $(id);
    if (!box) return;
    $$("span", box).forEach(function (s) {
      s.addEventListener("click", function () {
        $$("span", box).forEach(function (o) { o.classList.remove("on"); });
        s.classList.add("on");
        st[key] = s.dataset.v;
        if (key === "species") {
          var isDog = st.species === "dog";
          wIn.value = isDog ? 15 : 4.2;
        }
        calc();
      });
    });
  }
  if (wIn) {
    bindSeg("#cSpecies", "species");
    bindSeg("#cAge", "age");
    bindSeg("#cAct", "act");
    var sw = $("#cSter");
    sw.addEventListener("click", function () {
      var i = $("i", sw);
      i.classList.toggle("on");
      st.ster = i.classList.contains("on");
      calc();
    });
    wIn.addEventListener("input", calc);
    calc();
  }

  /* ---------- Размер файла для скачивания (если открыт по http/https) ---------- */
  var sizeEl = $("#dlSize");
  if (sizeEl && /^https?:/.test(location.protocol)) {
    fetch("downloads/NormaLap-Windows.zip", { method: "HEAD" }).then(function (r) {
      var n = parseInt(r.headers.get("content-length") || "0", 10);
      if (n > 0) sizeEl.textContent = "архив " + Math.round(n / 1048576) + " МБ";
    }).catch(function () {});
  }
})();
