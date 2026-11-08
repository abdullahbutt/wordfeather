/* Export and import of the progress that wordfeather.com keeps in this browser (answers of the telc exams, scores, underlines, settings).
   It adds two buttons to the row of telc links (.skillnav-in): "Export" saves one JSON file, "Import" reads such a file back, so that nothing is lost
   when the browser data is cleared or when you change the device. The file has the same format as the backups of the project (saved_at, origin, note, keys).
   Nothing is sent anywhere: the file stays on your device. */
(function () {
    'use strict';
    var KEY_RE = /^wf_[a-z0-9_]+$/;          // the keys of this site; anything else in a file is ignored
    var MAX_ITEM = 1500000, MAX_FILE = 4000000, MAX_KEYS = 60;
    var LABEL = {
        wf_telc_sb_v1: 'Sprachbausteine', wf_telc_lesen_v1: 'Lesen', wf_telc_hoeren_v1: 'Hören', wf_telc_schreiben_v2: 'Schreiben',
        wf_telc_lesen_ul_v1: 'Underlines in Lesen', wf_telc_hoeren_ul_v1: 'Underlines in Hören', wf_telc_sb_en: 'Sprachbausteine: meanings switch',
        wf_lessons_last: 'Last lesson opened', theme: 'Theme (light/dark)'
    };
    var rawSet = Storage.prototype.setItem;  // the pages write their own copy back when they are left: after an import this must not happen

    function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
    function known(k) { return KEY_RE.test(k) || k === 'theme'; }
    function pad(n) { return (n < 10 ? '0' : '') + n; }

    function count(v) {
        try {
            var o = JSON.parse(v);
            if (o && typeof o === 'object') {
                var n = 0;
                Object.keys(o).forEach(function (k) {
                    var e = o[k];
                    if (e && typeof e === 'object' && !Array.isArray(e)) { if (e.done || (e.a && Object.keys(e.a).length) || (e.fin && Object.keys(e.fin).length)) n++; } else n++;
                });
                return n;
            }
        } catch (e) { /* plain text value */ }
        return v ? 1 : 0;
    }

    function validate(text) {
        if (text.length > MAX_FILE) throw new Error('The file is too large for a progress file.');
        var d = JSON.parse(text);
        var keys = d && d.keys && typeof d.keys === 'object' ? d.keys : null;
        if (!keys) throw new Error('This is not a WordFeather progress file (no "keys" in it).');
        var out = {}, skipped = 0, names = Object.keys(keys);
        if (names.length > MAX_KEYS) throw new Error('Too many entries for a progress file.');
        names.forEach(function (k) {
            var v = keys[k];
            if (!known(k) || typeof v !== 'string' || v.length > MAX_ITEM) { skipped++; return; }
            if (k === 'theme') { if (v === 'light' || v === 'dark') out[k] = v; else skipped++; return; }
            if (/_v\d+$/.test(k)) { try { JSON.parse(v); } catch (e) { skipped++; return; } }   // the stores of the exams are JSON
            out[k] = v;
        });
        if (!Object.keys(out).length) throw new Error('The file has no progress of this site in it.');
        return { keys: out, skipped: skipped, saved: d.saved_at || '' };
    }

    function exportProgress(say) {
        var keys = {};
        for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (known(k)) keys[k] = localStorage.getItem(k); }
        var n = Object.keys(keys).length;
        if (!n) { say('There is no progress in this browser yet, so there is nothing to export.', true); return; }
        var now = new Date();
        var name = 'wordfeather_progress_' + now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate()) + '_' + pad(now.getHours()) + pad(now.getMinutes()) + '.json';
        var data = { saved_at: now.toISOString(), origin: location.origin, note: 'localStorage of wordfeather.com: quiz answers and progress.', keys: keys };
        var a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([JSON.stringify(data)], { type: 'application/json' }));
        a.download = name;
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 10000);
        say('Saved ' + n + ' items in the file ' + name + ' (look in your Downloads folder). Keep it safe: on another device or after clearing the browser, use Import with this file.');
    }

    function importProgress(file, say, panel) {
        var r = new FileReader();
        r.onerror = function () { say('The file could not be read.', true); };
        r.onload = function () {
            var res;
            try { res = validate(String(r.result)); } catch (e) { say(e.message || 'The file could not be used.', true); return; }
            panel.textContent = '';
            panel.appendChild(el('strong', null, 'Import ' + file.name + (res.saved ? ' (saved ' + res.saved.slice(0, 16).replace('T', ' ') + ' UTC)' : '') + '?'));
            panel.appendChild(el('div', 'wfp-small', 'Import replaces the progress of these items in this browser with the content of the file. Items that are not in the file stay as they are.'));
            var ul = el('ul', 'wfp-list');
            Object.keys(res.keys).forEach(function (k) {
                var here = localStorage.getItem(k);
                ul.appendChild(el('li', null, (LABEL[k] || k) + ': this browser ' + (here == null ? 'nothing' : count(here)) + ' · file ' + count(res.keys[k])));
            });
            panel.appendChild(ul);
            if (res.skipped) panel.appendChild(el('div', 'wfp-small', res.skipped + ' entries of the file were ignored (not progress of this site).'));
            var yes = el('button', 'wfp-btn wfp-go', 'Replace the progress in this browser'), no = el('button', 'wfp-btn', 'Cancel');
            yes.type = no.type = 'button';
            no.addEventListener('click', function () { panel.hidden = true; panel.textContent = ''; });
            yes.addEventListener('click', function () {
                Object.keys(res.keys).forEach(function (k) { rawSet.call(localStorage, k, res.keys[k]); });
                Storage.prototype.setItem = function () {};          // the open page must not write its old copy over the import
                panel.textContent = 'Imported. Reloading …';
                location.reload();
            });
            panel.appendChild(yes); panel.appendChild(document.createTextNode(' ')); panel.appendChild(no);
            panel.hidden = false;
        };
        r.readAsText(file);
    }

    function init() {
        var row = document.querySelector('.skillnav-in');
        if (!row || document.getElementById('wfp-msg')) return;
        var st = document.createElement('style');
        st.textContent = '.skillnav-tools{margin-left:auto;display:flex;gap:.4rem;flex:0 0 auto;padding-left:.75rem}' +
            '.wfp-btn{border:1px solid var(--bs-border-color);border-radius:999px;padding:.3rem .85rem;font-size:.9rem;background:var(--bs-body-bg);color:var(--bs-body-color);cursor:pointer;white-space:nowrap}' +
            '.wfp-btn:hover{border-color:var(--bs-primary)}.wfp-go{background:var(--bs-primary);border-color:var(--bs-primary);color:#fff}' +
            '#wfp-msg{max-width:1120px;margin:.5rem auto 0;padding:.6rem 16px;font-size:.9rem;border:1px solid var(--bs-border-color);border-radius:.5rem;background:var(--bs-secondary-bg)}' +
            '#wfp-msg.wfp-err{border-color:var(--bs-danger);color:var(--bs-danger-text-emphasis)}.wfp-list{margin:.4rem 0 .6rem;padding-left:1.2rem}.wfp-small{font-size:.85rem;color:var(--bs-secondary-color)}';
        document.head.appendChild(st);
        var tools = el('span', 'skillnav-tools'), ex = el('button', 'wfp-btn', '⬇ Export'), im = el('button', 'wfp-btn', '⬆ Import');
        ex.type = im.type = 'button';
        ex.title = 'Save your progress (answers, scores, underlines) in one file';
        im.title = 'Read a progress file back into this browser';
        var inp = document.createElement('input');
        inp.type = 'file'; inp.accept = '.json,application/json'; inp.hidden = true; inp.setAttribute('aria-label', 'Progress file');
        var panel = el('div'); panel.id = 'wfp-msg'; panel.setAttribute('role', 'status'); panel.hidden = true;
        function say(t, err) { panel.textContent = t; panel.className = err ? 'wfp-err' : ''; panel.id = 'wfp-msg'; panel.hidden = false; }
        ex.addEventListener('click', function () { exportProgress(say); });
        im.addEventListener('click', function () { inp.value = ''; inp.click(); });
        inp.addEventListener('change', function () { if (inp.files && inp.files[0]) importProgress(inp.files[0], say, panel); });
        tools.appendChild(ex); tools.appendChild(im); tools.appendChild(inp);
        row.appendChild(tools);
        row.parentNode.parentNode.insertBefore(panel, row.parentNode.nextSibling);
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
}());
