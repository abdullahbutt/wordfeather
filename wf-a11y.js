/* Accessibility helpers of the quiz pages (quiz.html, grammar-quiz.html, placement-test.html).
   - WF_A11Y.focus(el): moves the keyboard focus to an element that is not a control (a question, a heading, a result) so that a screen reader
     reads it and the next Tab continues from there. A page that rewrites itself would otherwise leave the focus at the top of the page.
   - the stylesheet below: the skip link, and the text colours that Bootstrap's defaults leave under the 4.5 : 1 contrast of WCAG 2.2 AA. */
(function () {
  var css =
    // skip link: visible only when it has the focus
    '.wf-skip{position:absolute;left:-9999px;top:0;z-index:2000}' +
    '.wf-skip:focus{left:.5rem;top:.5rem;background:#fff;color:#0a58ca;padding:.5rem 1rem;border-radius:.375rem;font-weight:600;box-shadow:0 2px 8px rgba(0,0,0,.35)}' +
    // text that receives the focus by program is not a control: no ring
    'main [tabindex="-1"]:focus{outline:none}' +
    // grey text
    'html:not([data-bs-theme="dark"]) .text-muted,html:not([data-bs-theme="dark"]) .text-secondary,html:not([data-bs-theme="dark"]) .opacity-75{color:#566069!important;opacity:1!important}' +
    '[data-bs-theme="dark"] .text-muted,[data-bs-theme="dark"] .text-secondary{color:#adb5bd!important}' +
    '.wf-en{opacity:1!important}' +
    '.answer-explanation{opacity:1!important}' +
    '.btn .wf-en{color:inherit!important}' +
    // small grey lines of the question cards in the dark scheme (their own slate grey is too dark there)
    '[data-bs-theme="dark"] .prompt-meta,[data-bs-theme="dark"] .gq-en-hint,[data-bs-theme="dark"] .pt-band{color:#adb5bd!important}' +
    // wrong answers in the dark scheme: a lighter red (the standard one is 4.46 : 1 on the tinted background)
    '[data-bs-theme="dark"] .gq-feedback.incorrect,[data-bs-theme="dark"] .gq-mc-btn.incorrect,[data-bs-theme="dark"] .pt-mc-btn.incorrect{color:#fca5a5!important}' +
    // links in the page
    'html:not([data-bs-theme="dark"]) main a:not(.btn):not(.nav-link):not(.wf-skip){color:#0a58ca}' +
    // outline buttons in the dark scheme
    'html:not([data-bs-theme="dark"]) .btn-outline-secondary{--bs-btn-color:#566069;--bs-btn-border-color:#566069}' +
    '[data-bs-theme="dark"] .btn-outline-secondary{--bs-btn-color:#adb5bd;--bs-btn-border-color:#adb5bd}' +
    // the English hint under a grammar answer
    'html:not([data-bs-theme="dark"]) .gq-feedback .gq-en-hint{color:#475569!important}' +
    // buttons of the top bar (colour theme, language)
    '#siteNavbar .btn-outline-light{--bs-btn-color:#fff}';
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  window.WF_A11Y = {
    focus: function (el) {
      if (!el) return;
      if (!el.matches('a[href],button,input,select,textarea,[tabindex]')) el.setAttribute('tabindex', '-1');
      el.focus();
    }
  };
})();
