/* Shared GA4 integration. Each site supplies its own measurement ID. */
(function () {
  'use strict';
  if (window.__websiteAnalytics) return;
  var script = document.currentScript;
  var id = script && script.getAttribute('data-ga-id');
  if (!/^G-[A-Z0-9]+$/.test(id || '')) return;
  window.__websiteAnalytics = true;
  var key = 'analytics-consent-' + id;
  var loaded = false;
  var panel, settings;
  function choice() {
    try { return localStorage.getItem(key); } catch (_) { return null; }
  }
  function cleanUrl(value, campaign) {
    try {
      var u = new URL(value, location.href);
      var result = u.origin + u.pathname;
      if (campaign) {
        var q = new URLSearchParams();
        ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(function (k) {
          var v = u.searchParams.get(k);
          if (v && !/@|%40/i.test(v)) q.set(k, v.slice(0, 100));
        });
        if (q.toString()) result += '?' + q.toString();
      }
      return result;
    } catch (_) { return ''; }
  }
  function start() {
    if (loaded || choice() !== 'granted') return;
    loaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag('consent', 'default', {
      analytics_storage: 'granted', ad_storage: 'denied',
      ad_user_data: 'denied', ad_personalization: 'denied'
    });
    window.gtag('js', new Date());
    window.gtag('config', id, {
      cookie_prefix: id.replace(/-/g, '_'), cookie_domain: location.hostname, cookie_expires: 60 * 60 * 24 * 180,
      allow_google_signals: false, allow_ad_personalization_signals: false,
      page_location: cleanUrl(location.href, true),
      page_referrer: document.referrer ? cleanUrl(document.referrer, false) : ''
    });
    var tag = document.createElement('script');
    tag.async = true;
    tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id);
    document.head.appendChild(tag);
  }
  function clearCookies() {
    var domains = [location.hostname, '.' + location.hostname];
    var pathParts = location.pathname.split('/');
    var paths = ['/'];
    for (var i = 1; i < pathParts.length; i++) paths.push(pathParts.slice(0, i + 1).join('/'));
    document.cookie.split(';').forEach(function (entry) {
      var name = entry.trim().split('=')[0];
      if (name.indexOf(id.replace(/-/g, '_') + '_') !== 0) return;
      paths.forEach(function (p) {
        document.cookie = name + '=; Max-Age=0; path=' + p;
        domains.forEach(function (d) { document.cookie = name + '=; Max-Age=0; path=' + p + '; domain=' + d; });
      });
    });
  }
  function save(value) {
    try { localStorage.setItem(key, value); } catch (_) {}
    panel.hidden = true;
    settings.focus();
    if (value === 'granted') {
      // If storage is unavailable, remember this page's explicit choice only.
      if (choice() !== 'granted') {
        var previous = choice;
        choice = function () { return 'granted'; };
        start();
        choice = previous;
      } else start();
    } else if (loaded) {
      window['ga-disable-' + id] = true;
      window.gtag('consent', 'update', { analytics_storage: 'denied' });
      clearCookies();
      location.reload();
    }
  }
  function amazonClick(value) {
    if (!loaded || choice() !== 'granted') return;
    try {
      var u = new URL(value, location.href);
      if (!/(^|\.)(amazon\.[a-z.]+|amzn\.to|a\.co)$/.test(u.hostname)) return;
      window.gtag('event', 'amazon_click', {send_to:id, link_url:cleanUrl(u.href, false), link_domain:u.hostname});
    } catch (_) {}
  }
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (a) amazonClick(a.href);
  }, true);
  var originalOpen = window.open;
  if (originalOpen) window.open = function (url) {
    amazonClick(String(url));
    return originalOpen.apply(this, arguments);
  };
  function ui() {
    var style = document.createElement('style');
    style.textContent = '#site-analytics-panel{position:fixed;bottom:52px;left:16px;right:16px;max-width:540px;z-index:2147483646;background:#fff;color:#17202a;border:1px solid #aeb6bf;border-radius:8px;padding:16px;box-shadow:0 3px 20px #0002;font:14px/1.5 system-ui,sans-serif;text-align:left}#site-analytics-panel[hidden]{display:none}#site-analytics-panel p{margin:0 0 12px;color:inherit;font:inherit}#site-analytics-panel button,#site-analytics-settings{background:#fff;color:#17202a;border:1px solid #66717d;border-radius:5px;padding:8px 12px;font:14px/1.3 system-ui,sans-serif;cursor:pointer}#site-analytics-panel button{margin:0 8px 0 0}#site-analytics-panel button:focus-visible,#site-analytics-settings:focus-visible{outline:3px solid #1d70b8;outline-offset:2px}#site-analytics-settings{position:fixed;bottom:12px;left:16px;z-index:2147483645;font-size:12px;padding:6px 9px}@media print{#site-analytics-panel,#site-analytics-settings{display:none!important}}';
    document.head.appendChild(style);
    panel = document.createElement('section');
    panel.id = 'site-analytics-panel';
    panel.setAttribute('aria-label', 'Analytics preferences');
    var text = document.createElement('p');
    text.textContent = 'Allow Google Analytics cookies to help us understand visits, popular pages, and links people use? You can decline and use the whole site. Change your choice with Analytics settings.';
    panel.appendChild(text);
    [['Allow analytics','granted'], ['Decline','denied']].forEach(function (option) {
      var b = document.createElement('button');
      b.type = 'button'; b.textContent = option[0];
      b.addEventListener('click', function () { save(option[1]); });
      panel.appendChild(b);
    });
    settings = document.createElement('button');
    settings.id = 'site-analytics-settings'; settings.type = 'button';
    settings.textContent = 'Analytics settings';
    settings.addEventListener('click', function () {
      panel.hidden = !panel.hidden;
      if (!panel.hidden) panel.querySelector('button').focus();
    });
    panel.hidden = choice() !== null;
    document.body.appendChild(panel); document.body.appendChild(settings);
    start();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ui, {once:true});
  else ui();
})();
