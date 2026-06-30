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

  /* ── PUBLICATIONS SEARCH + FILTER ───────────────────────────── */
  var searchInput = document.getElementById('pubSearch');
  var filterBtns  = document.querySelectorAll('.f-btn');
  var pubItems    = document.querySelectorAll('.pub-item');
  var activeFilter = 'all';

  function filterPubs() {
    var q = searchInput ? searchInput.value.toLowerCase() : '';
    pubItems.forEach(function (item) {
      var type = (item.dataset.type || '').toLowerCase();
      var text = item.textContent.toLowerCase();
      var matchFilter = activeFilter === 'all' || type === activeFilter;
      var matchSearch = !q || text.includes(q);
      item.style.display = matchFilter && matchSearch ? '' : 'none';
    });
  }

  if (searchInput) searchInput.addEventListener('input', filterPubs);

  filterBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      filterBtns.forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      activeFilter = btn.dataset.filter || 'all';
      filterPubs();
    });
  });

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

})();