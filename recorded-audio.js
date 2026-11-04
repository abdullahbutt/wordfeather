/**
 * WordFeather - recorded audio for the dictionary pages (recorded-audio.js)
 * The German words and example sentences of the vocabulary list are recorded (repository wordfeather-audio, Piper voice kerstin, see
 * tools/sentence_audio). When the device does not read German naturally (german-voice.js decides: wfGermanVoiceNatural()), the speaker
 * buttons play the recorded file instead of the voice of the device; they also play when the silent switch of an iPhone is on, which
 * mutes the voice of the device. window.wfRecorded.play(texts, done, fail) tries the files of the given texts (the first one found is
 * played) and returns false at once when recordings are not to be used here, so that the caller reads the text with the voice.
 * The file name is the first 16 hex characters of the SHA-1 of the text with white space collapsed (same rule as tts.js and the app).
 */
(function () {
  if (window.wfRecorded) return;
  var BASE = window.WF_AUDIO_BASE || 'https://audio.wordfeather.com/audio/de/';
  var SILENCE = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';
  var player = null;
  var unlocked = false;
  var turn = 0;

  function available() {
    return !!(window.Audio && window.fetch && window.crypto && window.crypto.subtle && window.wfGermanVoiceNatural && !window.wfGermanVoiceNatural());
  }

  function sentenceKey(text) {
    var clean = String(text).replace(/\s+/g, ' ').trim();
    return window.crypto.subtle.digest('SHA-1', new TextEncoder().encode(clean)).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) { return ('0' + b.toString(16)).slice(-2); }).join('').slice(0, 16);
    });
  }

  function fetchFile(text) {
    return sentenceKey(text).then(function (key) {
      return fetch(BASE + key + '.mp3');
    }).then(function (res) {
      return res.ok ? res.blob() : null;
    }).catch(function () { return null; });
  }

  // Safari lets an audio element play after a download, and the voice of the device speak after a failed download, only if a sound
  // began inside the tap. So the element is started (silently) here, inside the tap, once.
  function unlock() {
    player = player || new Audio();
    if (unlocked) return;
    unlocked = true;
    try {
      if ('speechSynthesis' in window) {
        var hush = new SpeechSynthesisUtterance('');
        hush.volume = 0;
        window.speechSynthesis.speak(hush);
      }
    } catch (e) { /* the read by the voice then needs its own tap */ }
    player.src = SILENCE;
    var started = player.play();
    if (started && started.catch) started.catch(function () {});
  }

  function stop() {
    turn++;
    if (player) { player.onended = null; player.onerror = null; player.pause(); }
  }

  function play(texts, done, fail) {
    if (!available()) return false;
    var mine = ++turn;
    unlock();
    Promise.all(texts.map(fetchFile)).then(function (blobs) {
      if (mine !== turn) return;
      var blob = null;
      for (var i = 0; i < blobs.length && !blob; i++) blob = blobs[i];
      if (!blob) { fail(); return; }
      var url = URL.createObjectURL(blob);
      player.onended = function () { URL.revokeObjectURL(url); if (mine === turn) done(); };
      player.onerror = function () { URL.revokeObjectURL(url); if (mine === turn) fail(); };
      player.src = url;
      return player.play();
    }).catch(function () { if (mine === turn) fail(); });
    return true;
  }

  window.wfRecorded = { play: play, stop: stop };
})();
