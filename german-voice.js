/**
 * WordFeather - German voice guard (german-voice.js)
 * Every speaker button of the static pages ends in speechSynthesis.speak(). A page cannot install a voice (only the operating
 * system can), and without a German voice the browser would read German with an English voice, which sounds wrong. So when the
 * browser lists voices and none is German, German text is not read; a small box says why and shows how to install a German voice
 * for the visitor's system (German and English), with a "check again" button. English text is read as before.
 * When the browser lists no voices at all (some Android versions), reading is tried anyway.
 * Loaded by tts.js and by the pages that have their own speaker code; it patches SpeechSynthesis.prototype.speak once.
 */
(function () {
  if (window.__wfGermanVoice) return;
  window.__wfGermanVoice = true;
  if (!('speechSynthesis' in window) || typeof SpeechSynthesisUtterance === 'undefined' || !window.SpeechSynthesis) return;

  var synth = window.speechSynthesis;
  var proto = window.SpeechSynthesis.prototype;
  var original = proto.speak;

  // 'yes': a German voice exists. 'no': voices are listed and none is German. 'unknown': no voices listed.
  function voiceState() {
    var voices = synth.getVoices();
    if (!voices || !voices.length) return 'unknown';
    for (var i = 0; i < voices.length; i++) {
      var lang = String(voices[i].lang || '').toLowerCase().replace('_', '-');
      if (lang === 'de' || lang.indexOf('de-') === 0) return 'yes';
    }
    return 'no';
  }

  function isGerman(utterance) {
    var lang = String(utterance.lang || (utterance.voice && utterance.voice.lang) || '').toLowerCase().replace('_', '-');
    return lang === 'de' || lang.indexOf('de-') === 0;
  }

  function platform() {
    var ua = navigator.userAgent || '';
    if (/android/i.test(ua)) return 'android';
    if (/iphone|ipad|ipod/i.test(ua)) return 'ios';
    if (/windows/i.test(ua)) return 'windows';
    if (/mac os x|macintosh/i.test(ua)) return 'mac';
    return 'other';
  }

  var STEPS = {
    windows: {
      de: 'Chrome und Edge bringen meist eine deutsche Online-Stimme mit. Firefox nutzt die Stimmen von Windows: Einstellungen → Zeit & Sprache → Sprache & Region → Sprache hinzufügen → Deutsch (mit Sprachausgabe), danach den Browser neu starten.',
      en: 'Chrome and Edge usually bring a German online voice. Firefox uses the voices of Windows: Settings → Time & language → Language & region → Add a language → German (with text-to-speech), then restart the browser.'
    },
    mac: {
      de: 'Safari, Chrome und Firefox nutzen die Stimmen von macOS: Systemeinstellungen → Bedienungshilfen → Gesprochene Inhalte → Systemstimme → Stimmen verwalten → Deutsch → eine Stimme laden. Danach den Browser neu starten.',
      en: 'Safari, Chrome and Firefox use the voices of macOS: System Settings → Accessibility → Spoken Content → System Voice → Manage Voices → German → download a voice. Then restart the browser.'
    },
    ios: {
      de: 'Auf iPhone und iPad nutzen alle Browser (Safari, Chrome, Firefox) die Stimmen von iOS: Einstellungen → Bedienungshilfen → Gesprochene Inhalte → Stimmen → Deutsch → eine Stimme laden. Danach den Browser neu öffnen.',
      en: 'On iPhone and iPad all browsers (Safari, Chrome, Firefox) use the voices of iOS: Settings → Accessibility → Spoken Content → Voices → German → download a voice. Then reopen the browser.'
    },
    android: {
      de: 'Chrome und Firefox nutzen den Sprachdienst von Android: Einstellungen → System → Sprachen & Eingabe → Text-in-Sprache-Ausgabe → (Google) Einstellungen → Sprachdaten installieren → Deutsch. Der Pfad kann je nach Gerät abweichen.',
      en: 'Chrome and Firefox use the Android speech service: Settings → System → Languages & input → Text-to-speech output → (Google) Settings → Install voice data → German. The path can differ by device.'
    },
    other: {
      de: 'Unter Linux nutzt der Browser speech-dispatcher: Installieren Sie es mit einer deutschen Stimme (z. B. die Pakete speech-dispatcher und espeak-ng) und starten Sie den Browser neu. Chrome bringt unter Umständen eine deutsche Online-Stimme mit.',
      en: 'On Linux the browser uses speech-dispatcher: install it with a German voice (for example the packages speech-dispatcher and espeak-ng) and restart the browser. Chrome may bring a German online voice.'
    }
  };

  var box = null;

  function addStyle() {
    var style = document.createElement('style');
    style.textContent =
      '.wf-voice{position:fixed;left:12px;right:12px;bottom:12px;max-width:36rem;margin:0 auto;z-index:2147483000;' +
        'background:#fef3c7;color:#451a03;border:1px solid #f59e0b;border-radius:10px;padding:12px 14px;' +
        'font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;box-shadow:0 6px 24px rgba(0,0,0,.25);}' +
      '.wf-voice[hidden]{display:none;}' +
      '.wf-voice p{margin:0 0 6px;}' +
      '.wf-voice .wf-voice-en{opacity:.85;}' +
      '.wf-voice details{margin:6px 0;}' +
      '.wf-voice summary{cursor:pointer;font-weight:600;}' +
      '.wf-voice button{font:inherit;border:1px solid #92400e;background:#fff;color:#451a03;border-radius:6px;padding:4px 10px;margin:6px 8px 0 0;cursor:pointer;min-height:32px;}' +
      '.wf-voice button:focus-visible,.wf-voice summary:focus-visible{outline:3px solid #1d4ed8;outline-offset:2px;}' +
      '[data-bs-theme="dark"] .wf-voice{background:#422006;color:#fef3c7;border-color:#b45309;}' +
      '[data-bs-theme="dark"] .wf-voice button{background:#1c1917;color:#fef3c7;border-color:#b45309;}';
    document.head.appendChild(style);
  }

  function build() {
    addStyle();
    var steps = STEPS[platform()];
    box = document.createElement('div');
    box.className = 'wf-voice';
    box.setAttribute('role', 'status');
    box.innerHTML =
      '<p lang="de"><strong>Keine deutsche Stimme gefunden.</strong> Auf diesem Gerät ist keine deutsche Sprachausgabe installiert. ' +
        'Mit einer anderen Stimme würde das Deutsch falsch klingen, deshalb wird nichts vorgelesen.</p>' +
      '<p lang="en" class="wf-voice-en"><strong>No German voice found.</strong> No German text-to-speech voice is installed on this device. ' +
        'German would sound wrong with another voice, so nothing is read aloud.</p>' +
      '<details><summary><span lang="de">So installieren Sie eine deutsche Stimme</span> / <span lang="en">How to install a German voice</span></summary>' +
        '<p lang="de"></p><p lang="en" class="wf-voice-en"></p></details>' +
      '<button type="button" data-act="recheck"><span lang="de">Erneut prüfen</span> / <span lang="en">Check again</span></button>' +
      '<button type="button" data-act="close"><span lang="de">Schließen</span> / <span lang="en">Close</span></button>';
    var texts = box.querySelectorAll('details p');
    texts[0].textContent = steps.de;
    texts[1].textContent = steps.en;
    box.addEventListener('click', function (e) {
      var act = e.target.closest ? e.target.closest('button') : null;
      if (!act) return;
      if (act.getAttribute('data-act') === 'close') box.hidden = true;
      if (act.getAttribute('data-act') === 'recheck') {
        if (voiceState() !== 'no') box.hidden = true; // a German voice exists now
      }
    });
    document.body.appendChild(box);
  }

  function showBox() {
    if (!document.body) return;
    if (!box) build();
    box.hidden = false;
  }

  // A voice that arrives later (the list loads asynchronously, or the learner installed one) closes the box.
  synth.addEventListener('voiceschanged', function () {
    if (box && voiceState() !== 'no') box.hidden = true;
  });

  proto.speak = function (utterance) {
    if (utterance && isGerman(utterance) && voiceState() === 'no') {
      showBox();
      // The page's own code waits for the end or the error of the utterance to reset its button: tell it, without speaking.
      setTimeout(function () {
        try { utterance.dispatchEvent(new Event('error')); } catch (e) { /* the button resets itself on the next click */ }
      }, 0);
      return;
    }
    return original.apply(this, arguments);
  };
})();
