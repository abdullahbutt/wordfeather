/* Language choice of the quiz pages (quiz.html, grammar-quiz.html, placement-test.html): German and English together (the default),
   German only, or English only. The choice is kept in localStorage ('wf_ui_lang') and set as data-ui-lang on <html> before the page is
   drawn; the stylesheet below hides the language that is not wanted, so switching is instant and needs no redraw.

   In the page:   <span class="wf-pair"><span class="wf-de">Alle</span> <span class="wf-en">All</span></span>   (one line, "/" between)
                  <p class="wf-de">…</p><p class="wf-en">…</p>                                                (two blocks)
   In a script:   WF_LANG.bi('Alle', 'All')   gives the markup of the first form;   WF_LANG.t('Hallo', 'Hello')   gives plain text
                  for alert(), aria-label and the like, in the language that is chosen now ("de\nen" when both are chosen).
   The bar of the quiz pages (quiz-bar.js) and the names of the exercises always show both languages, as in the app. */
(function () {
  var KEY = 'wf_ui_lang';
  var MODES = ['both', 'de', 'en'];
  var root = document.documentElement;

  function get() {
    try {
      var v = localStorage.getItem(KEY);
      return MODES.indexOf(v) !== -1 ? v : 'both';
    } catch (e) { return 'both'; }
  }
  function apply(mode) {
    root.setAttribute('data-ui-lang', mode);
    root.setAttribute('lang', mode === 'en' ? 'en' : 'de');
  }
  apply(get());

  var css = 'html[data-ui-lang="de"] .wf-en,html[data-ui-lang="en"] .wf-de{display:none!important}' +
    'html[data-ui-lang="both"] .wf-pair>.wf-en::before{content:"/ "}' +
    // one language alone: it gets the look of the main text, not the muted look of the second language
    'html[data-ui-lang="en"] .wf-en{opacity:1!important}' +
    'html[data-ui-lang="en"] .wf-pair>.wf-en{color:inherit!important;font-weight:inherit!important}' +
    '#wfLangSwitch .btn{font-size:.75rem;padding:.2rem .5rem;line-height:1.2}' +
    '#wfLangSwitch .btn.active{background:#fff;color:#1d4ed8;border-color:#fff}';
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  var LABELS = { both: 'DE · EN', de: 'DE', en: 'EN' };
  var TITLES = { both: 'Deutsch und English / German and English', de: 'Nur Deutsch / German only', en: 'English only / Nur Englisch' };

  function syncSwitch() {
    var box = document.getElementById('wfLangSwitch');
    if (!box) return;
    var cur = get();
    Array.prototype.forEach.call(box.querySelectorAll('button'), function (b) {
      var on = b.getAttribute('data-mode') === cur;
      b.classList.toggle('active', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  function set(mode) {
    if (MODES.indexOf(mode) === -1) return;
    try { localStorage.setItem(KEY, mode); } catch (e) { /* not remembered */ }
    apply(mode);
    syncSwitch();
    document.dispatchEvent(new CustomEvent('wf-lang', { detail: mode }));
  }

  // The switch sits in the top bar, in front of the colour-theme button. The bar is loaded after the page starts (header.html), so
  // it is added as soon as the theme button exists.
  function mountSwitch() {
    if (document.getElementById('wfLangSwitch')) return true;
    var theme = document.getElementById('themeToggle');
    if (!theme || !theme.parentNode) return false;
    var box = document.createElement('div');
    box.id = 'wfLangSwitch';
    box.className = 'btn-group me-2';
    box.setAttribute('role', 'group');
    box.setAttribute('aria-label', 'Sprache / Language');
    MODES.forEach(function (mode) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn btn-outline-light';
      b.setAttribute('data-mode', mode);
      b.title = TITLES[mode];
      b.textContent = LABELS[mode];
      b.addEventListener('click', function () { set(mode); });
      box.appendChild(b);
    });
    theme.parentNode.insertBefore(box, theme);
    syncSwitch();
    return true;
  }
  function watchHeader() {
    if (mountSwitch()) return;
    var target = document.getElementById('header-placeholder') || document.body;
    var obs = new MutationObserver(function () { if (mountSwitch()) obs.disconnect(); });
    obs.observe(target, { childList: true, subtree: true });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', watchHeader);
  else watchHeader();

  window.WF_LANG = {
    get: get,
    set: set,
    bi: function (de, en) {
      return '<span class="wf-pair"><span class="wf-de">' + de + '</span> <span class="wf-en">' + en + '</span></span>';
    },
    // for <option> and other places that take text only: "de / en" on one line when both are chosen
    s: function (de, en) {
      var m = get();
      return m === 'de' ? de : m === 'en' ? en : de + ' / ' + en;
    },
    t: function (de, en) {
      var m = get();
      return m === 'de' ? de : m === 'en' ? en : de + '\n' + en;
    }
  };
})();
