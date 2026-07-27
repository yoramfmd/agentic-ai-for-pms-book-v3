/* site-extras.js — outbound click tracking for agenticaiproductmanagement.com.
   Loaded alongside the Umami tag. No dependencies, no cookies, no UI.
   One delegated listener covers every link on every page, so there is
   nothing to maintain in the builders when pages are regenerated.
   Safe to load twice; guarded. */
(function () {
  if (window.__siteExtras) return;
  window.__siteExtras = true;

  function track(name, data) {
    try { if (window.umami) window.umami.track(name, data || {}); } catch (e) {}
  }

  var params = new URLSearchParams(location.search);
  var campaign = params.get('utm_campaign') || '';
  var variant = params.get('utm_content') || '';

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (!/^https?:/i.test(href)) return;

    var host;
    try { host = new URL(href, location.href).hostname.replace(/^www\./, ''); }
    catch (err) { return; }
    if (host === location.hostname.replace(/^www\./, '')) return;

    var name = 'outbound';
    if (/amazon\.|amzn\./.test(host))                       name = 'amazon-click';
    else if (/data-decisions-and-clinics\.com$/.test(host))  name = 'blog-click';
    else if (/linkedin\.com$/.test(host))                    name = 'linkedin-click';

    track(name, {
      href: href.slice(0, 200),
      from: location.pathname,
      campaign: campaign,
      variant: variant
    });
  }, true);
})();
