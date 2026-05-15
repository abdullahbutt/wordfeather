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

  function addButtonsToTables() {
    var tables = document.querySelectorAll('table');

    tables.forEach(function (table) {
      var headers = table.querySelectorAll('thead th');
      if (headers.length === 0) return;

      // Build column map
      var colMap = {};
      headers.forEach(function (th, i) {
        var text = th.textContent.trim().toLowerCase();
        if (text === 'deutsch') colMap.de = i;
        else if (text === 'englisch') colMap.en = i;
        else if (text === 'beispielsatz') colMap.example = i;
      });

      // Skip tables without Deutsch/Englisch columns
      if (colMap.de === undefined && colMap.en === undefined) return;

      // Process each data row
      var rows = table.querySelectorAll('tbody tr');
      rows.forEach(function (row) {
        var cells = row.querySelectorAll('td');
        if (cells.length === 0) return;

        // German word
        if (colMap.de !== undefined && cells[colMap.de]) {
          wrapCell(cells[colMap.de], 'de-DE');
        }

        // English translation
        if (colMap.en !== undefined && cells[colMap.en]) {
          wrapCell(cells[colMap.en], 'en-US');
        }

        // Example sentence (German)
        if (colMap.example !== undefined && cells[colMap.example]) {
          wrapCell(cells[colMap.example], 'de-DE');
        }
      });
    });
  }

  function wrapCell(cell, lang) {
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
