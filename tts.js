/**
 * WordFeather - Text-to-Speech (tts.js)
 * Adds pronunciation buttons to vocabulary tables and sentence lists.
 * Uses the browser's built-in Web Speech API — free, no API keys needed.
 */
(function () {
  // The guard for a missing German voice (german-voice.js) is loaded next to this file, once.
  if (!window.__wfGermanVoice && document.currentScript && document.currentScript.src) {
    var guard = document.createElement('script');
    guard.src = document.currentScript.src.replace(/tts\.js(\?.*)?$/, 'german-voice.js?v=0.00.04');
    document.head.appendChild(guard);
  }

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

  // recorded: the text is an example sentence or a word of the vocabulary list, so a recorded file may exist (other texts have none and are
  // read at once, inside the tap).
  function createBtn(text, lang, recorded) {
    var btn = document.createElement('button');
    btn.className = 'tts-btn';
    btn.innerHTML = speakerSVG;
    btn.setAttribute('aria-label', 'Listen to pronunciation');
    btn.setAttribute('title', lang === 'de-DE' ? 'Anhören' : 'Listen');
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      speak(text, lang, btn, recorded);
    });
    return btn;
  }

  function speak(text, lang, btn, recorded) {
    // Stop any current speech
    synth.cancel();
    audioTurn++;
    if (player) { player.onended = null; player.onerror = null; player.pause(); }

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

    btn.classList.add('playing');
    activeBtn = btn;

    // The voice of the device is used when it reads German naturally. When it does not (a compact voice, a robot voice or none), a German
    // sentence with a recorded audio file (tools/sentence_audio) is played from the file; a sentence without a file is read by the voice.
    if (recorded && lang.indexOf('de') === 0 && window.wfGermanVoiceNatural && !window.wfGermanVoiceNatural() && window.Audio && window.crypto && window.crypto.subtle) {
      var turn = ++audioTurn;
      unlockPlayer();
      playSentenceFile(text, btn, function () { return turn === audioTurn; }, function () { speakWithVoice(cleanText, lang, btn); });
      return;
    }
    speakWithVoice(cleanText, lang, btn);
  }

  var audioTurn = 0;
  var player = null;
  var unlocked = false;
  var SILENCE = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';

  // Safari (iPhone) lets an audio element play later only if it started a sound inside a tap. The file is fetched after the tap, so the
  // element is made and started (silently) here, inside the tap, once.
  function unlockPlayer() {
    player = player || new Audio();
    if (unlocked) return;
    try {
      var hush = new SpeechSynthesisUtterance('');
      hush.volume = 0;
      synth.speak(hush); // Safari also lets a later read by the voice start only if a speech began inside a tap
    } catch (e) { /* the read by the voice then needs its own tap */ }
    unlocked = true;
    player.src = SILENCE;
    var started = player.play();
    if (started && started.catch) started.catch(function () {});
  }

  function sentenceKey(text) {
    var clean = text.replace(/\s+/g, ' ').trim();
    return window.crypto.subtle.digest('SHA-1', new TextEncoder().encode(clean)).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) { return ('0' + b.toString(16)).slice(-2); }).join('').slice(0, 16);
    });
  }

  function playSentenceFile(text, btn, current, fallback) {
    var base = window.WF_AUDIO_BASE || 'https://abdullahbutt.github.io/wordfeather-audio/audio/de/';
    sentenceKey(text).then(function (key) {
      return fetch(base + key + '.mp3').then(function (res) {
        if (!res.ok) throw new Error('no file');
        return res.blob();
      });
    }).then(function (blob) {
      if (!current()) return;
      player = player || new Audio();
      var url = URL.createObjectURL(blob);
      var rest = function () { URL.revokeObjectURL(url); if (activeBtn === btn) { btn.classList.remove('playing'); activeBtn = null; } };
      player.onended = rest;
      player.onerror = function () { rest(); if (current()) fallback(); };
      player.src = url;
      return player.play();
    }).catch(function () { if (current()) fallback(); });
  }

  function speakWithVoice(cleanText, lang, btn) {
    var utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = lang;
    utterance.rate = 0.9; // Slightly slower for learners

    // A voice is chosen here only when the device has a clearly better one (Enhanced, Premium, Natural). Otherwise the browser's own
    // default voice for the language is used: it is the natural one of the device (on an iPhone the last voice of the list, which this
    // code used to take, was a poor one). German is chosen in german-voice.js.
    var voices = synth.getVoices();
    var langPrefix = lang.split('-')[0];
    var bestVoice = null;
    for (var i = 0; i < voices.length; i++) {
      if (voices[i].lang.replace('_', '-').toLowerCase().indexOf(langPrefix) === 0 &&
          (voices[i].name.indexOf('Enhanced') > -1 || voices[i].name.indexOf('Premium') > -1 || voices[i].name.indexOf('Natural') > -1)) {
        bestVoice = voices[i];
        break;
      }
    }
    if (bestVoice) utterance.voice = bestVoice;

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
    el.parentNode.insertBefore(createBtn(text, lang, true), el.nextSibling);
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
    // The Deutsch column of the vocabulary pages has recorded files; the German cells of other tables have none and are read at once.
    wrapper.appendChild(createBtn(text, lang, lang === 'de-DE' && /Wortschatz/.test(location.pathname)));
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
