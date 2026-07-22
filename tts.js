/**
 * Deutsch Learning Hub - Text-to-Speech (tts.js)
 * Adds pronunciation buttons to vocabulary tables and sentence lists.
 * Uses the browser's built-in Web Speech API — free, no API keys needed.
 */
(function () {
  // Check browser support
  if (!('speechSynthesis' in window)) return;

  var synth = window.speechSynthesis;
  var activeBtn = null;

  // CSS for speaker buttons
  var style = document.createElement('style');
  style.textContent =
    '.tts-btn{' +
      'display:inline-flex;align-items:center;justify-content:center;' +
      'width:24px;height:24px;border:none;background:none;' +
      'cursor:pointer;opacity:0.4;transition:opacity 0.2s;' +
      'padding:0;margin-left:4px;vertical-align:middle;flex-shrink:0;' +
      'border-radius:50%;font-size:14px;line-height:1;' +
    '}' +
    '.tts-btn:hover{opacity:0.8;background:rgba(29,78,216,0.1);}' +
    '.tts-btn.playing{opacity:1;color:#1d4ed8;background:rgba(29,78,216,0.15);}' +
    '.tts-btn svg{width:14px;height:14px;fill:currentColor;}' +
    'td .tts-wrap{display:flex;align-items:center;gap:2px;}' +
    'td .tts-wrap span{flex:1;}' +
    '[data-bs-theme="dark"] .tts-btn:hover{background:rgba(99,102,241,0.2);}' +
    '[data-bs-theme="dark"] .tts-btn.playing{color:#818cf8;background:rgba(99,102,241,0.25);}';
  document.head.appendChild(style);

  // Speaker SVG icon
  var speakerSVG = '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">' +
    '<path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>' +
    '</svg>';

  function createBtn(text, lang) {
    var btn = document.createElement('button');
    btn.className = 'tts-btn';
    btn.innerHTML = speakerSVG;
    btn.setAttribute('aria-label', 'Listen to pronunciation');
    btn.setAttribute('title', lang === 'de-DE' ? 'Anhören' : 'Listen');
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      speak(text, lang, btn);
    });
    return btn;
  }

  function speak(text, lang, btn) {
    // Stop any current speech
    synth.cancel();

    // If clicking the same button that's playing, just stop
    if (activeBtn === btn) {
      if (activeBtn) activeBtn.classList.remove('playing');
      activeBtn = null;
      return;
    }

    // Reset previous
    if (activeBtn) activeBtn.classList.remove('playing');

    // Clean text for speech
    var cleanText = text
      .replace(/\s*[,]\s*-\w+/g, '')  // Remove plural forms like ", -e"
      .replace(/[—–]/g, '')            // Remove dashes
      .replace(/\(.*?\)/g, '')         // Remove parenthetical notes
      .replace(/\s+/g, ' ')
      .trim();

    if (!cleanText) return;

    var utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = lang;
    utterance.rate = 0.9; // Slightly slower for learners

    // Try to find a good voice for the language
    var voices = synth.getVoices();
    var langPrefix = lang.split('-')[0];
    var bestVoice = null;
    for (var i = 0; i < voices.length; i++) {
      if (voices[i].lang.indexOf(langPrefix) === 0) {
        bestVoice = voices[i];
        // Prefer non-compact/enhanced voices
        if (voices[i].name.indexOf('Enhanced') > -1 ||
            voices[i].name.indexOf('Premium') > -1 ||
            voices[i].name.indexOf('Natural') > -1) {
          break;
        }
      }
    }
    if (bestVoice) utterance.voice = bestVoice;

    btn.classList.add('playing');
    activeBtn = btn;

    utterance.onend = function () {
      btn.classList.remove('playing');
      activeBtn = null;
    };
    utterance.onerror = function () {
      btn.classList.remove('playing');
      activeBtn = null;
    };

    synth.speak(utterance);
  }

  function addButtonsToExampleSentences() {
    // The "Beispielsatz" column (and dictionary.html's .word-example div)
    // always holds BOTH a German and an English span together in the same
    // cell — unlike a pure "Deutsch" or "Englisch" column, wrapping the
    // whole cell as one blob is never correct here (it reads both
    // languages together with a single, wrong-for-half-of-it voice, and
    // on the Wortschatz page it even swallows the nested drill table's
    // text too, since that lives in the same cell). Target the two spans
    // directly instead, each getting its own correctly-tagged button.
    document.querySelectorAll('.ex-de').forEach(function (el) { wrapInlineText(el, 'de-DE'); });
    document.querySelectorAll('.ex-en').forEach(function (el) { wrapInlineText(el, 'en-US'); });
  }

  function wrapInlineText(el, lang) {
    // Like wrapCell(), but for a <span> rather than a <td> — appends the
    // speaker button as a sibling after the span instead of wrapping its
    // contents, so it doesn't disturb the span's own text/classes.
    if (el.nextElementSibling && el.nextElementSibling.classList.contains('tts-btn')) return;
    var text = el.textContent.trim();
    if (!text || text === '—' || text === '-') return;
    el.parentNode.insertBefore(createBtn(text, lang), el.nextSibling);
  }

  function addButtonsToPersonDrills() {
    // Deliberately its own function, NOT folded into addButtonsToTables()'s
    // generic header-text matching. That generic path scans every <table>
    // on the page and matches columns by header text (e.g. "Beispielsatz"),
    // which is exactly the kind of broad matching that once caused the
    // search filter to reach into this same nested table and hide its rows.
    // Scoping explicitly to .word-person-drill by position (not text)
    // avoids that whole class of bug entirely.
    document.querySelectorAll('.word-person-drill tbody tr').forEach(function (row) {
      var cells = row.querySelectorAll('td');
      if (cells.length < 2) return;
      wrapCell(cells[0], 'de-DE');
      wrapCell(cells[1], 'en-US');
    });
  }

  function addButtonsToTables() {
    var tables = document.querySelectorAll('table');

    tables.forEach(function (table) {
      // Person-drill tables are handled exclusively by
      // addButtonsToPersonDrills() below — skip them here so there's a
      // single, deterministic code path for them regardless of any
      // incidental header-text overlap (e.g. this table's own headers
      // happen to say "Deutsch"/"English", same as the main vocab tables).
      if (table.closest('.word-person-drill')) return;

      var headers = table.querySelectorAll('thead th');
      
      // Dictionary page: no thead, uses de-col/en-col classes
      if (headers.length === 0) {
        var deColCells = table.querySelectorAll('td.de-col');
        var enColCells = table.querySelectorAll('td.en-col');
        if (deColCells.length > 0) {
          deColCells.forEach(function (cell) { wrapCell(cell, 'de-DE'); });
          enColCells.forEach(function (cell) { wrapCell(cell, 'en-US'); });
          return;
        }
        return;
      }

      // Build column map (supports duplicate headers like Deutsch, Englisch, Deutsch, Englisch)
      var colMap = { de: [], en: [] };
      headers.forEach(function (th, i) {
        var text = th.textContent.trim().toLowerCase();
        if (text === 'deutsch' || text === 'kollokation' || text === 'wendung' ||
            text === 'einfaches verb' || text === 'bedeutung' ||
            text === 'neutral') {
          colMap.de.push(i);
        } else if (text === 'englisch') {
          colMap.en.push(i);
        }
      });

      // Skip tables without recognized columns
      if (colMap.de.length === 0 && colMap.en.length === 0) return;

      // Process each data row
      var rows = table.querySelectorAll('tbody tr');
      rows.forEach(function (row) {
        var cells = row.querySelectorAll('td');
        if (cells.length === 0) return;

        // German columns
        colMap.de.forEach(function (idx) {
          if (cells[idx]) wrapCell(cells[idx], 'de-DE');
        });

        // English columns
        colMap.en.forEach(function (idx) {
          if (cells[idx]) wrapCell(cells[idx], 'en-US');
        });
      });
    });

    addButtonsToExampleSentences();
    addButtonsToPersonDrills();

    // Route to the right handler based on page type
    var path = window.location.pathname;
    if (path.indexOf('Saetze') > -1) {
      addButtonsToSaetze();
    } else {
      addButtonsToSprechen();
    }
  }

  function addButtonsToSprechen() {
    var items = document.querySelectorAll('.markdown-content ul li, .markdown-content ol li');

    items.forEach(function (li) {
      // Skip if already processed by addButtonsToSaetze
      if (li.querySelector('.tts-btn')) return;

      var strongs = li.querySelectorAll('strong');
      var ems = li.querySelectorAll('em');

      // Only process if there's at least a strong tag
      if (strongs.length === 0) return;

      // Add German speaker after each <strong>
      strongs.forEach(function (el) {
        var text = el.textContent.trim();
        if (text && text !== '—' && text.length > 1) {
          el.parentNode.insertBefore(createBtn(text, 'de-DE'), el.nextSibling);
        }
      });

      // Add English speaker after each <em>
      ems.forEach(function (el) {
        var text = el.textContent.trim();
        if (text && text !== '—' && text.length > 1) {
          el.parentNode.insertBefore(createBtn(text, 'en-US'), el.nextSibling);
        }
      });
    });
  }

  function addButtonsToSaetze() {
    var items = document.querySelectorAll('.markdown-content ol li');

    items.forEach(function (li) {
      var strong = li.querySelector('strong');
      if (!strong) return;

      var germanText = strong.textContent.trim();
      var fullText = li.textContent.trim();

      // Split on — or - to get English part
      var parts = fullText.split(/\s*[—–]\s*/);
      var englishText = parts.length > 1 ? parts.slice(1).join(' — ').trim() : '';

      // Build new content: 🔊 German — 🔊 English
      var wrapper = document.createElement('span');

      var deSpan = document.createElement('strong');
      deSpan.textContent = germanText;
      wrapper.appendChild(deSpan);
      wrapper.appendChild(createBtn(germanText, 'de-DE'));

      if (englishText) {
        var dash = document.createTextNode(' — ');
        wrapper.appendChild(dash);

        var enSpan = document.createElement('span');
        enSpan.textContent = englishText;
        wrapper.appendChild(enSpan);
        wrapper.appendChild(createBtn(englishText, 'en-US'));
      }

      li.innerHTML = '';
      li.appendChild(wrapper);
    });
  }

  function wrapCell(cell, lang) {
    // Guard against double-processing: the generic addButtonsToTables()
    // path matches tables by header text (e.g. "Deutsch"), and the
    // person-drill table's own header happens to say "Deutsch" too — so
    // without this guard, a cell could get wrapped twice (once by each
    // path) and end up with two speaker buttons instead of one.
    if (cell.querySelector('.tts-wrap')) return;

    var text = cell.textContent.trim();
    if (!text || text === '—' || text === '-') return;

    var wrapper = document.createElement('div');
    wrapper.className = 'tts-wrap';
    var span = document.createElement('span');
    span.innerHTML = cell.innerHTML;
    wrapper.appendChild(span);
    wrapper.appendChild(createBtn(text, lang));
    cell.innerHTML = '';
    cell.appendChild(wrapper);
  }

  // Voices may load async — wait for them
  var initialized = false;
  function init() {
    if (initialized) return;
    initialized = true;
    addButtonsToTables();
  }

  if (synth.getVoices().length > 0) {
    init();
  } else {
    synth.addEventListener('voiceschanged', function () {
      init();
    });
    // Fallback: init after short delay if voiceschanged never fires
    setTimeout(init, 500);
  }
})();
