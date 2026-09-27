/* Privacy-focused website analytics. No consent UI, cookies, or identity tracking. */
(function () {
  'use strict';
  if (window.__websiteAnalytics) return;
  window.__websiteAnalytics = true;
  var config = document.currentScript;
  var id = config && config.getAttribute('data-umami-id');
  if (!id) return;
  var books = {
    book3: 'Agentic AI for Busy Product Managers',
    book4: 'Why Agentic AI Products Fail',
    book5: 'The Agentic AI Team',
    book6: 'The Agentic AI Practitioner',
    book7: 'Agentic AI for Product Leaders, the OneBook'
  };
  var isBooks = id === '6701185a-719e-4b6f-baaf-dcd504ef6b1a';
  var bookKey = isBooks ? location.pathname.split('/')[1] : '';
  var book = books[bookKey] || '';
  var utmKeys = ['utm_source','utm_medium','utm_campaign','utm_content','utm_term'];
  function cleanUrl(value, campaign) {
    if (!value) return '';
    try {
      var u = new URL(value, location.href);
      var q = new URLSearchParams();
      if (campaign) utmKeys.forEach(function (key) {
        var v = u.searchParams.get(key);
        if (v && !/@|%40/i.test(v)) q.set(key, v.slice(0, 100));
      });
      u.search = q.toString(); u.hash = '';
      return /^[a-z]+:\/\//i.test(value) ? u.origin + u.pathname + u.search : u.pathname + u.search;
    } catch (e) { return ''; }
  }
  window.websiteAnalyticsBeforeSend = function (type, payload) {
    if (payload.url) payload.url = cleanUrl(payload.url, true);
    if (payload.referrer) payload.referrer = cleanUrl(payload.referrer, false);
    if (isBooks) payload.tag = book || 'Book site: other pages';
    return payload;
  };
  var script = document.createElement('script');
  script.defer = true;
  script.src = 'https://cloud.umami.is/script.js';
  script.setAttribute('data-website-id', id);
  script.setAttribute('data-before-send', 'websiteAnalyticsBeforeSend');
  script.setAttribute('data-exclude-hash', 'true');
  script.setAttribute('data-do-not-track', 'true');
  if (isBooks) script.setAttribute('data-tag', book || 'Book site: other pages');
  document.head.appendChild(script);

  var amazonBooks = {
    '/d/0dCz9Lbx': books.book3,
    '/d/0cdvAyjn': books.book4,
    '/d/0jhGrB91': books.book5
  };
  var clickBook = '';
  function report(href, element) {
    var u;
    try { u = new URL(href, location.href); } catch (e) { return; }
    if (!/^https?:$/.test(u.protocol) || u.hostname === location.hostname) return;
    var amazon = /(^|\.)(amazon\.[a-z.]+|amzn\.to|a\.co)$/.test(u.hostname);
    var name = amazon ? 'amazon-click' : /(^|\.)linkedin\.com$/.test(u.hostname) ? 'linkedin-click' : u.hostname === 'data-decisions-and-clinics.com' ? 'blog-click' : 'outbound';
    var title = amazon ? amazonBooks[u.pathname] || '' : '';
    // A series link is not evidence of interest in a particular book.
    if (amazon && element && /series on amazon/i.test(element.textContent || '')) title = 'Series (not a specific book)';
    if (!title && amazon && u.pathname.indexOf('/dp/B0H6311T43') === 0) title = 'Series (not a specific book)';
    if (!title) title = clickBook || book || 'Unassigned';
    var data = {href: cleanUrl(u.href, false), from: location.pathname, book: title};
    var params = new URLSearchParams(location.search);
    ['utm_campaign','utm_content'].forEach(function (key) {
      var value = params.get(key);
      if (value && !/@|%40/i.test(value)) data[key === 'utm_campaign' ? 'campaign' : 'variant'] = value.slice(0,100);
    });
    try { if (window.umami) window.umami.track(name, data); } catch (e) {}
  }
  document.addEventListener('click', function (event) {
    var target = event.target;
    var card = target && target.closest ? target.closest('.book-card, .book-wide') : null;
    clickBook = '';
    if (isBooks && card) {
      try { clickBook = books[new URL(card.getAttribute('href'), location.href).pathname.split('/')[1]] || ''; } catch (e) {}
    }
    var a = target && target.closest ? target.closest('a[href]') : null;
    if (a) report(a.getAttribute('href'), a);
    setTimeout(function () { clickBook = ''; }, 0);
  }, true);
  var nativeOpen = window.open;
  window.open = function (url) {
    report(String(url), null);
    return nativeOpen.apply(window, arguments);
  };
})();
