/* Shared bar of the quiz pages (quiz.html, grammar-quiz.html, placement-test.html): one row of tabs below the site header,
   so every practice mode and level test is one click away from every quiz page.
   Usage: a div with id "quiz-bar" and data-page "quiz", "grammar" or "placement", followed by a script tag loading /quiz-bar.js.
   On quiz.html the in-page modes are <button>s with the ids and data-mode that quiz.html's own script already uses
   (tab-practice, tab-hoeren, ... ; list #modeTabs); everywhere else they are links to quiz.html#<mode>. */
(function () {
  var mount = document.getElementById('quiz-bar');
  if (!mount) return;
  var page = mount.getAttribute('data-page') || '';

  var items = [
    { key: 'practice', mode: true, icon: '📚', de: 'Wortschatz', en: 'Vocabulary' },
    { key: 'hoeren', mode: true, icon: '🎧', de: 'Hören', en: 'Listening' },
    { key: 'lesen', mode: true, icon: '📰', de: 'Lesen', en: 'Reading' },
    { key: 'grammar', href: '/grammar-quiz.html', icon: '🔤', de: 'Grammatik', en: 'Grammar' },
    { key: 'placement', mode: true, icon: '🎯', de: 'Niveau: Wortschatz', en: 'Level test: vocabulary' },
    { key: 'placement-grammar', href: '/placement-test.html', icon: '🎯', de: 'Niveau: Grammatik', en: 'Level test: grammar' },
    { key: 'mistakes', mode: true, icon: '❌', de: 'Meine Fehler', en: 'My mistakes' },
    { key: 'bookmarks', mode: true, icon: '⭐', de: 'Lesezeichen', en: 'Bookmarks', count: true }
  ];
  var activeOnOtherPages = { grammar: 'grammar', placement: 'placement-grammar' };

  function bookmarkCount() {
    try {
      var raw = localStorage.getItem('wf_quiz_bookmarks_v1');
      return raw ? Object.keys(JSON.parse(raw)).length : 0;
    } catch (e) { return 0; }
  }

  var css = '#quiz-bar{background:var(--bs-tertiary-bg);border-bottom:1px solid var(--bs-border-color)}' +
    '#quiz-bar ul{display:flex;gap:.25rem;list-style:none;margin:0 auto;padding:0 .75rem;max-width:1140px;overflow-x:auto;scrollbar-width:thin}' +
    '#quiz-bar li{flex:0 0 auto}' +
    '#quiz-bar .qb-item{display:block;background:none;border:0;border-bottom:3px solid transparent;border-radius:0;padding:.5rem .75rem;text-align:center;' +
    'white-space:nowrap;line-height:1.2;color:var(--bs-link-color);text-decoration:none;cursor:pointer;font:inherit}' +
    '#quiz-bar .qb-item:hover{color:var(--bs-link-hover-color)}' +
    '#quiz-bar .qb-item:focus-visible{outline:2px solid var(--bs-primary);outline-offset:-2px}' +
    '#quiz-bar .qb-item.active{border-bottom-color:var(--bs-primary);font-weight:600}' +
    '#quiz-bar .qb-en{display:block;font-size:.72rem;font-weight:400;color:var(--bs-secondary-color)}';
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  var html = '<ul id="modeTabs" role="tablist" aria-label="Quiz-Modus wählen / Choose quiz mode">';
  items.forEach(function (it) {
    var label = it.icon + ' ' + it.de + (it.count ? ' (<span id="bookmarkTabCount">' + bookmarkCount() + '</span>)' : '') +
      '<span class="qb-en">' + it.en + '</span>';
    var active = page === 'quiz' ? it.key === 'practice' : activeOnOtherPages[page] === it.key;
    if (it.mode && page === 'quiz') {
      html += '<li role="presentation"><button type="button" class="qb-item' + (active ? ' active' : '') + '" id="tab-' + it.key + '" data-mode="' + it.key +
        '" role="tab" aria-selected="' + active + '" aria-controls="' + it.key + 'Options">' + label + '</button></li>';
    } else {
      var href = it.mode ? '/quiz.html#' + it.key : it.href;
      html += '<li role="presentation"><a class="qb-item' + (active ? ' active' : '') + '" href="' + href + '"' + (active ? ' aria-current="page"' : '') + '>' + label + '</a></li>';
    }
  });
  mount.innerHTML = html + '</ul>';
  mount.setAttribute('role', 'navigation');
  mount.setAttribute('aria-label', 'Quiz');
})();
