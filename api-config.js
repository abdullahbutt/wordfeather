// WordFeather - API configuration (thesis backend).
// Picks the API base URL from the page hostname: local development talks to the
// EnvKit backend, everything else to production. Not yet loaded by any page.
(function () {
  var h = window.location.hostname;
  var isLocal = h === 'localhost' || h === '127.0.0.1' ||
                h === 'wordfeather.test' || h.slice(-17) === '.wordfeather.test';
  window.WF_API_BASE = isLocal ? 'https://api.wordfeather.test' : 'https://api.wordfeather.com';

  function readCookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : null;
  }

  // Usage: wfApi('/v1/...', { method: 'POST', body: {...} })
  // Sends the Sanctum session cookie and the CSRF header on state-changing requests.
  window.wfApi = function (path, options) {
    options = options || {};
    var method = (options.method || 'GET').toUpperCase();
    var headers = { 'Accept': 'application/json' };
    var body;
    if (options.body !== undefined) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(options.body);
    }
    function send() {
      if (method !== 'GET') {
        var token = readCookie('XSRF-TOKEN');
        if (token) { headers['X-XSRF-TOKEN'] = token; }
      }
      return fetch(window.WF_API_BASE + path, {
        method: method, headers: headers, body: body, credentials: 'include'
      });
    }
    if (method === 'GET' || readCookie('XSRF-TOKEN')) { return send(); }
    // First state-changing call of a session: fetch the CSRF cookie first.
    return fetch(window.WF_API_BASE + '/sanctum/csrf-cookie', { credentials: 'include' }).then(send);
  };
})();
