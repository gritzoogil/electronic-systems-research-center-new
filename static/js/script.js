(function () {
  'use strict';

  /* ── NAV SCROLL ─────────────────────────────────────────────── */
  var nav = document.getElementById('siteNav');
  window.addEventListener('scroll', function () {
    nav.classList.toggle('scrolled', window.scrollY > 20);
    document.getElementById('scrollTop').classList.toggle('show', window.scrollY > 400);
  }, { passive: true });

  /* ── MOBILE NAV ─────────────────────────────────────────────── */
  var toggle = document.getElementById('navToggle');
  var mobileNav = document.getElementById('mobileNav');
  var isOpen = false;
  function setMenu(open) {
    isOpen = open;
    toggle.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', open.toString());
    mobileNav.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  }
  toggle.addEventListener('click', function () { setMenu(!isOpen); });
  mobileNav.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () { setMenu(false); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isOpen) setMenu(false);
  });

  /* ── SCROLL REVEAL ───────────────────────────────────────────── */
  var revealIO = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('visible'); revealIO.unobserve(e.target); }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach(function (el) { revealIO.observe(el); });

  /* ── STATS COUNTER ───────────────────────────────────────────── */
  function animateCounter(el) {
    var target = parseInt(el.dataset.target, 10);
    var dur = 1800;
    var start = performance.now();
    function step(now) {
      var p = Math.min((now - start) / dur, 1);
      var ease = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.floor(ease * target) + (el.dataset.suffix || '');
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  var statsIO = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        animateCounter(e.target);
        statsIO.unobserve(e.target);
      }
    });
  }, { threshold: 0.4 });
  document.querySelectorAll('[data-target]').forEach(function (el) { statsIO.observe(el); });

  /* ── CONTACT FORM ─────────────────────────────────────────────── */
  var form = document.getElementById('contactForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('[type=submit]');
      btn.textContent = 'Sending…';
      btn.disabled = true;
      setTimeout(function () {
        btn.textContent = 'Message Sent ✓';
        btn.style.background = 'linear-gradient(135deg,#22C55E,#16A34A)';
        setTimeout(function () {
          form.reset();
          btn.textContent = 'Send Message';
          btn.disabled = false;
          btn.style.background = '';
        }, 3000);
      }, 1400);
    });
  }

  /* ── SMOOTH SCROLL FOR HASH LINKS ─────────────────────────────── */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        var offset = 76;
        var top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top: top, behavior: 'smooth' });
      }
    });
  });

  /* ── SCROLL TO TOP ─────────────────────────────────────────────── */
  var scrollTopBtn = document.getElementById('scrollTop');
  if (scrollTopBtn) {
    scrollTopBtn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ── STAGGERED CARD REVEAL ─────────────────────────────────────── */
  var staggerParents = document.querySelectorAll('[data-stagger]');
  staggerParents.forEach(function (parent) {
    var cards = parent.querySelectorAll('.reveal');
    cards.forEach(function (card, i) {
      card.style.transitionDelay = (i * 0.07) + 's';
    });
  });

/* ─────────────────────────────────────────────
   PARTNERS AUTO SCROLL + DRAG
───────────────────────────────────────────── */

const mask = document.querySelector(".partners-mask");
const track = document.querySelector(".partners-track");

if (mask && track) {

    let position = 0;
    let speed = 1.5;      // pixels/frame

    let isDragging = false;
    let startX = 0;
    let startPosition = 0;

    const loopWidth = track.scrollWidth / 2;

    function animate() {

        if (!isDragging) {

            position -= speed;

            if (Math.abs(position) >= loopWidth) {
                position = 0;
            }

            track.style.transform =
                `translateX(${position}px)`;
        }

        requestAnimationFrame(animate);
    }

    animate();

    // -------------------------
    // Mouse Drag
    // -------------------------

    mask.addEventListener("mousedown", e => {

        isDragging = true;

        mask.classList.add("dragging");

        startX = e.clientX;

        startPosition = position;
    });

    window.addEventListener("mousemove", e => {

        if (!isDragging) return;

        const dx = e.clientX - startX;

        position = startPosition + dx;

        if (position > 0)
            position -= loopWidth;

        if (position < -loopWidth)
            position += loopWidth;

        track.style.transform =
            `translateX(${position}px)`;
    });

    window.addEventListener("mouseup", () => {

        isDragging = false;

        mask.classList.remove("dragging");
    });

    // -------------------------
    // Touch Support
    // -------------------------

    mask.addEventListener("touchstart", e => {

        isDragging = true;

        startX = e.touches[0].clientX;

        startPosition = position;

    }, { passive: true });

    window.addEventListener("touchmove", e => {

        if (!isDragging) return;

        const dx = e.touches[0].clientX - startX;

        position = startPosition + dx;

        if (position > 0)
            position -= loopWidth;

        if (position < -loopWidth)
            position += loopWidth;

        track.style.transform =
            `translateX(${position}px)`;

    }, { passive: true });

    window.addEventListener("touchend", () => {

        isDragging = false;

    });

}

})();

/* ── CENTER HIGHLIGHTS LIVE SEARCH ─────────────────────────────── */
(function () {
  var searchInput = document.querySelector('#center-highlights-page .pub-search input[name="q"]');
  var resultsEl = document.getElementById('highlightsResults');
  if (!searchInput || !resultsEl) return;

  var yearInput = document.querySelector('#center-highlights-page .pub-search input[name="year"]');
  var debounceTimer = null;
  var currentController = null; // tracks the in-flight request so we can cancel it

  function fetchResults() {
    var q = encodeURIComponent(searchInput.value.trim());
    var year = encodeURIComponent(yearInput ? yearInput.value : 'all');
    var url = '/center-highlights?q=' + q + '&year=' + year;

    // Cancel any still-pending previous request before starting a new one
    if (currentController) currentController.abort();
    currentController = new AbortController();

    fetch(url, {
      headers: { 'X-Requested-With': 'fetch' },
      signal: currentController.signal
    })
      .then(function (res) { return res.text(); })
      .then(function (html) {
        resultsEl.innerHTML = html;
        history.replaceState(null, '', url);
        initHighlightCarousels();
      })
      .catch(function (err) {
        if (err.name === 'AbortError') return; // expected when a newer request supersedes this one
        console.error('Highlights search failed:', err);
      });
  }

  searchInput.addEventListener('input', function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(fetchResults, 350);
  });

  var form = searchInput.closest('form');
  if (form) form.addEventListener('submit', function (e) { e.preventDefault(); });

  document.querySelectorAll('#center-highlights-page .pub-filters a').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var url = new URL(a.href);
      if (yearInput) yearInput.value = url.searchParams.get('year') || 'all';
      document.querySelectorAll('#center-highlights-page .pub-filters a').forEach(function (x) {
        x.classList.toggle('active', x === a);
      });
      fetchResults();
    });
  });

  resultsEl.addEventListener('click', function (e) {
    var link = e.target.closest('.pub-pagination a:not(.disabled)');
    if (!link) return;
    e.preventDefault();
    var url = new URL(link.href);

    if (currentController) currentController.abort();
    currentController = new AbortController();

    fetch(url.pathname + url.search, {
      headers: { 'X-Requested-With': 'fetch' },
      signal: currentController.signal
    })
      .then(function (res) { return res.text(); })
      .then(function (html) {
        resultsEl.innerHTML = html;
        history.replaceState(null, '', url);
        initHighlightCarousels();
        resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      })
      .catch(function (err) {
        if (err.name === 'AbortError') return;
        console.error('Highlights pagination failed:', err);
      });
  });
})();