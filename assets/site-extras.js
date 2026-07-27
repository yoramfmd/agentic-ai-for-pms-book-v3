/* site-extras.js — outbound click tracking for agenticaiproductmanagement.com.
   Loaded alongside the Umami tag. No dependencies, no cookies, no UI.

   Catches outbound navigation two ways:
     1. clicks on real <a href> elements (capture phase)
     2. programmatic window.open(...), used by the hub's buy badges,
        which are <span onclick="...window.open(...)"> rather than links
   Safe to load twice; guarded. */
(function () {
  if (window.__siteExtras) return;
  window.__siteExtras = true;

  var params   = new URLSearchParams(location.search);
  var campaign = params.get('utm_campaign') || '';
  var variant  = params.get('utm_content')  || '';

  function track(name, data) {
    try { if (window.umami) window.umami.track(name, data); } catch (e) {}
  }

  /* Classify an absolute URL and record it if it leaves this site. */
  function report(href) {
    if (!href || !/^https?:/i.test(href)) return;
    var host;
    try { host = new URL(href, location.href).hostname.replace(/^www\./, ''); }
    catch (e) { return; }
    if (host === location.hostname.replace(/^www\./, '')) return;

    var name = 'outbound';
    if (/(^|\.)(amazon\.|amzn\.to$|a\.co$)/.test(host))     name = 'amazon-click';
    else if (/data-decisions-and-clinics\.com$/.test(host)) name = 'blog-click';
    else if (/linkedin\.com$/.test(host))                   name = 'linkedin-click';

    track(name, {
      href: href.slice(0, 200),
      from: location.pathname,
      campaign: campaign,
      variant: variant
    });
  }

  /* 1. real links. Capture phase, so stopPropagation() upstream cannot hide it. */
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (a) report(a.getAttribute('href'));
  }, true);

  /* 2. window.open, used by the hub buy badges. Wrap, record, pass through. */
  var nativeOpen = window.open;
  window.open = function (url) {
    try { report(String(url)); } catch (e) {}
    return nativeOpen.apply(window, arguments);
  };
})();
