#!/usr/bin/env python3
"""
build.py — Deutsch Lernen Hub build pipeline
============================================
Regenerates all six Wortschatz pages and/or dictionary.html
from the single source of truth: words_final.json

Usage:
    python3 build.py                     # rebuild Wortschatz pages + update dictionary counts
    python3 build.py --all               # rebuild everything: Wortschatz + dictionary (recommended)
    python3 build.py --dictionary        # fully rebuild dictionary.html from JSON only
    python3 build.py --wortschatz-only   # rebuild Wortschatz pages only
    python3 build.py --audit             # run quality audit and exit
    python3 build.py --help              # show this help

Author: Abdullah Butt
"""

import json, html as htmllib, re, sys, os
from collections import defaultdict, Counter
from conjugator import conjugate, _regular_stem
from english_conjugator import build_english_table

REPO    = os.path.dirname(os.path.abspath(__file__))
JSON    = os.path.join(REPO, 'words_final.json')
BASE    = '/deutsch-lernen-goethe-a1-c2'

FAVICON_BLOCK = f'''\
    <link rel="icon" type="image/x-icon" href="{BASE}/icons/favicon.ico">
    <link rel="icon" type="image/png" sizes="16x16" href="{BASE}/icons/16.png">
    <link rel="icon" type="image/png" sizes="32x32" href="{BASE}/icons/32.png">
    <link rel="icon" type="image/png" sizes="96x96" href="{BASE}/icons/96.png">
    <link rel="icon" type="image/png" sizes="192x192" href="{BASE}/icons/192.png">
    <link rel="apple-touch-icon" sizes="180x180" href="{BASE}/icons/180.png">
    <link rel="manifest" href="{BASE}/manifest.json">'''

# ── Level metadata ─────────────────────────────────────────────────────────────
META = {
    'A1': {'color':'#16a34a','desc':'Grundvokabular für absolute Anfänger — Alltag, Familie, Zahlen, Begrüßungen.'},
    'A2': {'color':'#2563eb','desc':'Erweiterter Alltagswortschatz — Einkaufen, Reisen, Körper, Schule, Technologie.'},
    'B1': {'color':'#7c3aed','desc':'Thematischer Wortschatz für das Goethe-Zertifikat B1 und den Einbürgerungstest.'},
    'B2': {'color':'#ea580c','desc':'Journalistischer und halbformeller Wortschatz für Studium und Beruf.'},
    'C1': {'color':'#dc2626','desc':'Formaler, akademischer und fachsprachlicher Wortschatz.'},
    'C2': {'color':'#0d9488','desc':'Nuancierter, idiomatischer und literarischer Wortschatz auf Muttersprachenniveau.'},
}
COLORS = {lv: META[lv]['color'] for lv in META}

# ── Quality audit ──────────────────────────────────────────────────────────────
def audit(words):
    issues = []
    counts = Counter(w['level'] for w in words)

    # Duplicates
    keys = [(w['de'].lower().strip(), w['level']) for w in words]
    dupes = [k for k, v in Counter(keys).items() if v > 1]
    if dupes:
        issues.append(f"DUPLICATES ({len(dupes)}): " + ', '.join(f"{d[0]} [{d[1]}]" for d in dupes[:5]))

    # Missing required fields
    for field in ['de','en','level','example']:
        missing = [w['de'] for w in words if not w.get(field,'').strip()]
        if missing:
            issues.append(f"MISSING '{field}' ({len(missing)}): " + ', '.join(missing[:5]))

    # German chars in English field
    bad = [w['de'] for w in words
           if any(c in w.get('example_en','') for c in 'äöüÄÖÜß')
           and not any(x in w.get('example_en','').lower() for x in ['café','naïve'])]
    if bad:
        issues.append(f"GERMAN IN EN FIELD ({len(bad)}): " + ', '.join(bad[:5]))

    # Generic examples
    BANNED = ["das thema betrifft","wir sprechen über","ist sehr wichtig",
              "hat sich verändert","ich interessiere mich für",
              "ist von großer bedeutung","ist ein ernstes problem",
              "es gibt verschiedene ansichten","der ansatz ist "]
    generic = [w['de'] for w in words
               if any(b in w.get('example','').lower() for b in BANNED)]
    if generic:
        issues.append(f"GENERIC EXAMPLES ({len(generic)}): " + ', '.join(generic[:5]))

    # Collocations coverage B2+
    for lv in ['B2','C1','C2']:
        total = counts[lv]
        has   = sum(1 for w in words if w['level']==lv and w.get('collocations'))
        pct   = has * 100 // total if total else 0
        if pct < 80:
            issues.append(f"LOW COLLOCATIONS {lv}: {has}/{total} ({pct}%)")

    return issues, counts

# ── App Install Banner ────────────────────────────────────────────────────────
# Slim, collapsible, dismissible banner. Collapsed by default; expands on tap.
# Hidden entirely when the PWA is already running in standalone (installed) mode,
# and hidden permanently once the user dismisses it (localStorage flag shared
# across all pages that include this markup).
INSTALL_BANNER_STYLE_SCRIPT = (
    '    <style>\n'
    '        .install-banner-wrap{background:linear-gradient(135deg,#1d4ed8 0%,#7c3aed 100%);color:#fff;}\n'
    '        .install-banner{position:relative;padding:.5rem 2.2rem .5rem .25rem;}\n'
    '        .install-banner-bar{display:flex;align-items:center;gap:.5rem;width:100%;background:none;'
    'border:none;color:#fff;text-align:left;cursor:pointer;padding:.2rem .25rem;font-size:.85rem;}\n'
    '        .install-banner-icon{font-size:1.1rem;line-height:1;}\n'
    '        .install-banner-text{font-weight:600;flex:1;}\n'
    '        .install-banner-chevron{opacity:.8;transition:transform .2s;}\n'
    '        .install-banner-bar[aria-expanded="true"] .install-banner-chevron{transform:rotate(180deg);}\n'
    '        .install-banner-close{position:absolute;top:.35rem;right:.35rem;background:none;border:none;'
    'color:#fff;opacity:.7;font-size:1rem;line-height:1;cursor:pointer;padding:.2rem .4rem;}\n'
    '        .install-banner-close:hover{opacity:1;}\n'
    '        .install-banner-panel{padding-top:.5rem;}\n'
    '        .install-banner-card{background:rgba(255,255,255,.15);border-radius:.6rem;padding:.5rem .7rem;'
    'font-size:.78rem;line-height:1.4;height:100%;}\n'
    '        .install-banner-card-title{font-weight:700;margin-bottom:.15rem;}\n'
    '    </style>\n'
    '    <script>\n'
    '    (function () {\n'
    "        var KEY = 'dlh_install_banner_dismissed';\n"
    "        var banner = document.getElementById('installBanner');\n"
    '        if (!banner) return;\n'
    "        var isStandalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || window.navigator.standalone === true;\n"
    '        var dismissed = false;\n'
    "        try { dismissed = localStorage.getItem(KEY) === '1'; } catch (e) {}\n"
    '        if (isStandalone || dismissed) return;\n'
    "        banner.style.display = 'block';\n"
    "        var toggle = document.getElementById('installBannerToggle');\n"
    "        var panel = document.getElementById('installBannerPanel');\n"
    "        var closeBtn = document.getElementById('installBannerClose');\n"
    "        toggle.addEventListener('click', function () {\n"
    "            var expanded = toggle.getAttribute('aria-expanded') === 'true';\n"
    "            toggle.setAttribute('aria-expanded', String(!expanded));\n"
    '            panel.hidden = expanded;\n'
    '        });\n'
    "        closeBtn.addEventListener('click', function (e) {\n"
    '            e.stopPropagation();\n'
    "            try { localStorage.setItem(KEY, '1'); } catch (e2) {}\n"
    "            banner.style.display = 'none';\n"
    '        });\n'
    '    })();\n'
    '    </script>\n'
)

INSTALL_BANNER_CARDS = (
    '                    <div class="row g-2">\n'
    '                        <div class="col-6 col-md-3">\n'
    '                            <div class="install-banner-card"><div class="install-banner-card-title">🍎 iPhone/iPad</div>'
    '<div>Safari → <strong>Share ⬆</strong> → Add to Home Screen</div></div>\n'
    '                        </div>\n'
    '                        <div class="col-6 col-md-3">\n'
    '                            <div class="install-banner-card"><div class="install-banner-card-title">🤖 Android</div>'
    '<div>Chrome → <strong>⋮ Menu</strong> → Add to Home Screen</div></div>\n'
    '                        </div>\n'
    '                        <div class="col-6 col-md-3">\n'
    '                            <div class="install-banner-card"><div class="install-banner-card-title">🖥️ macOS</div>'
    '<div>Safari → <strong>Share</strong> → Add to Dock</div></div>\n'
    '                        </div>\n'
    '                        <div class="col-6 col-md-3">\n'
    '                            <div class="install-banner-card"><div class="install-banner-card-title">🪟 Windows</div>'
    '<div>Edge → <strong>Apps</strong> → Install this site</div></div>\n'
    '                        </div>\n'
    '                    </div>\n'
)

# Version for index.html / level index pages — inserted before <main>, wrapped
# in its own full-width container.
INSTALL_BANNER = (
    '\n    <!-- App Install Banner -->\n'
    '    <div id="installBanner" class="install-banner-wrap" style="display:none;">\n'
    '        <div class="container">\n'
    '            <div class="install-banner">\n'
    '                <button type="button" id="installBannerToggle" class="install-banner-bar" '
    'aria-expanded="false" aria-controls="installBannerPanel">\n'
    '                    <span class="install-banner-icon">📱</span>\n'
    '                    <span class="install-banner-text">Install as a free app — works offline, no App Store needed</span>\n'
    '                    <span class="install-banner-chevron">▾</span>\n'
    '                </button>\n'
    '                <button type="button" id="installBannerClose" class="install-banner-close" '
    'aria-label="Dismiss install banner">✕</button>\n'
    '                <div id="installBannerPanel" class="install-banner-panel" hidden>\n'
    + INSTALL_BANNER_CARDS.replace('                    ', '                        ')
    + '                </div>\n'
    '            </div>\n'
    '        </div>\n'
    '    </div>\n'
    + INSTALL_BANNER_STYLE_SCRIPT +
    '    <!-- End App Install Banner -->\n'
)

# Version for dictionary.html — no outer .container (it already sits inside the
# content card), inserted after the search/filter block instead of before <main>
# so the search box stays the first visible element.
INSTALL_BANNER_DICT = (
    '                <!-- App Install Banner -->\n'
    '                <div id="installBanner" class="install-banner-wrap mb-3" style="display:none;">\n'
    '                    <div class="install-banner">\n'
    '                        <button type="button" id="installBannerToggle" class="install-banner-bar" '
    'aria-expanded="false" aria-controls="installBannerPanel">\n'
    '                            <span class="install-banner-icon">📱</span>\n'
    '                            <span class="install-banner-text">Install as a free app — works offline, no App Store needed</span>\n'
    '                            <span class="install-banner-chevron">▾</span>\n'
    '                        </button>\n'
    '                        <button type="button" id="installBannerClose" class="install-banner-close" '
    'aria-label="Dismiss install banner">✕</button>\n'
    '                        <div id="installBannerPanel" class="install-banner-panel" hidden>\n'
    + INSTALL_BANNER_CARDS.replace('                    ', '                            ')
    + '                        </div>\n'
    '                    </div>\n'
    '                </div>\n'
    + INSTALL_BANNER_STYLE_SCRIPT +
    '                <!-- End App Install Banner -->\n'
)

_BANNER_STRIP_RE = re.compile(
    r'\s*<!-- [─\-]*\s*App Install Banner.*?End App Install Banner\s*[─\-]*\s*-->\s*',
    re.DOTALL
)

def inject_install_banner(content):
    """Insert the app install banner before <main>. Idempotent."""
    # Remove any existing banner — handles both old and new comment styles
    content = _BANNER_STRIP_RE.sub('\n', content)
    main_pos = content.find('<main')
    if main_pos == -1:
        return content
    return content[:main_pos] + INSTALL_BANNER + content[main_pos:]


def inject_install_banner_dict(content):
    """Insert the dictionary-page install banner right below the title/subtitle
    block, above the search box (<div class="search-wrap mb-2">), so it's
    immediately visible without pushing the search input down more than one
    slim bar's height. Idempotent."""
    content = _BANNER_STRIP_RE.sub('\n', content)
    anchor = content.find('<div class="search-wrap mb-2">')
    if anchor == -1:
        # Fallback: behave like the standard banner if the anchor is missing
        main_pos = content.find('<main')
        if main_pos == -1:
            return content
        return content[:main_pos] + INSTALL_BANNER + content[main_pos:]
    return content[:anchor] + INSTALL_BANNER_DICT + content[anchor:]


CONJUGATION_WS_SCRIPT = """<script>
// Full verb conjugation table for Wortschatz tables — lazy-loaded, click-to-expand
(function() {
    var conjData = null;
    var conjPromise = null;
    var prefix = '../';

    function loadConjugations() {
        if (conjPromise) return conjPromise;
        conjPromise = fetch(prefix + 'conjugations.json')
            .then(function(r) { return r.ok ? r.json() : {}; })
            .then(function(json) {
                conjData = {};
                Object.keys(json).forEach(function(k) { conjData[k.toLowerCase()] = json[k]; });
                return conjData;
            })
            .catch(function() { conjData = {}; return conjData; });
        return conjPromise;
    }

    var TENSE_LABELS = {
        praesens: 'Präsens', praeteritum: 'Präteritum', perfekt: 'Perfekt',
        plusquamperfekt: 'Plusquamperfekt', futur1: 'Futur I', futur2: 'Futur II'
    };
    var PERSONS = ['ich', 'du', 'er/sie/es', 'wir', 'ihr', 'Sie'];
    var PERSONS_EN = ['I', 'you', 'he/she/it', 'we', 'you', 'they'];
    var EN_ELIGIBLE_TENSES = ['praesens', 'praeteritum', 'perfekt'];

    function renderTenseBlock(tenseKey, forms, englishForms) {
        var rows = '';
        var showEn = englishForms && EN_ELIGIBLE_TENSES.indexOf(tenseKey) > -1;
        for (var i = 0; i < 6; i++) {
            var enLine = showEn
                ? '<div class="conj-en-line-ws">(' + PERSONS_EN[i] + ' ' + englishForms[i] + ')</div>'
                : '';
            rows += '<div class="conj-row-ws"><span class="conj-person-ws">' + PERSONS[i] + '</span>' +
                    forms[i] + enLine + '</div>';
        }
        return '<div class="conj-tense-block-ws">' +
               '<div class="conj-tense-label-ws">' + (TENSE_LABELS[tenseKey] || tenseKey) + '</div>' +
               rows + '</div>';
    }

    function renderMoodGridWs(tenses, source, english) {
        var html = '';
        tenses.forEach(function(t) {
            if (source && source[t]) html += renderTenseBlock(t, source[t], english && english[t]);
        });
        return html ? '<div class="conj-mood-grid-ws">' + html + '</div>' : '';
    }

    function renderTable(table) {
        var html = '<div class="conj-table-wrap-ws">';
        var en = table.english || null;

        html += '<div class="conj-en-toggle-wrap-ws">' +
                '<label class="conj-en-toggle-ws">' +
                '<input type="checkbox" class="conj-en-toggle-input">' +
                '<span class="conj-en-toggle-slider-ws"></span>' +
                '</label>' +
                '<span>Englische Übersetzung anzeigen</span>' +
                '</div>';

        html += '<div class="conj-mood-title-ws">Weitere Formen</div><div class="conj-imperativ-row-ws">' +
                '<span>Infinitiv: ' + table.infinitiv + '</span>' +
                '<span>Partizip Präsens: ' + table.partizip1 + '</span>' +
                '<span>Partizip Perfekt: ' + table.partizip2 + '</span>' +
                '<span>zu + Infinitiv: ' + table.zu_infinitiv + '</span></div>';

        html += '<div class="conj-mood-title-ws">Indikativ</div>';
        html += renderMoodGridWs(['praesens','praeteritum','perfekt','plusquamperfekt','futur1','futur2'], table.indikativ, en);

        html += '<div class="conj-mood-title-ws">Konjunktiv I</div>';
        html += renderMoodGridWs(['praesens','perfekt','futur1','futur2'], table.konjunktiv1);

        html += '<div class="conj-mood-title-ws">Konjunktiv II</div>';
        html += renderMoodGridWs(['praeteritum','plusquamperfekt','futur1','futur2'], table.konjunktiv2);

        if (table.imperativ) {
            html += '<div class="conj-mood-title-ws">Imperativ</div><div class="conj-imperativ-row-ws">';
            ['du','ihr','Sie','wir'].forEach(function(p) {
                if (table.imperativ[p]) html += '<span>' + p + ': ' + table.imperativ[p] + '</span>';
            });
            html += '</div>';
        }
        if (table.passiv) {
            html += '<div class="conj-mood-title-ws">Passiv</div>';
            html += renderMoodGridWs(['praesens','praeteritum','perfekt','plusquamperfekt','futur1'], table.passiv);
        }
        html += '</div>';
        return html;
    }

    // Event delegation instead of per-button listeners: tts.js rebuilds
    // the 'Deutsch' column cells (innerHTML wipe + replace) to inject
    // its own speaker buttons, which destroys any directly-attached
    // listeners on this button. Delegating to document survives that,
    // since it relies on event bubbling + selector matching at click
    // time, not on the specific DOM node still existing.
    document.addEventListener('click', function(e) {
        var btn = e.target.closest('.conj-toggle-ws');
        if (!btn) return;
        e.preventDefault(); e.stopPropagation();

        var row = btn.closest('tr');
        var nextRow = row.nextElementSibling;
        var isOpen = nextRow && nextRow.classList.contains('conj-row-container-ws');
        if (isOpen) {
            nextRow.remove();
            btn.textContent = '📖 Konjugation';
            return;
        }

        var de = btn.getAttribute('data-de-lower');
        loadConjugations().then(function(data) {
            var table = data[de];
            if (!table) {
                btn.textContent = '(noch nicht verfügbar)';
                btn.disabled = true;
                return;
            }
            var colCount = row.children.length;
            var newRow = document.createElement('tr');
            newRow.className = 'conj-row-container-ws';
            var td = document.createElement('td');
            td.colSpan = colCount;
            td.innerHTML = renderTable(table);
            var enToggleInput = td.querySelector('.conj-en-toggle-input');
            if (enToggleInput) {
                enToggleInput.checked = localStorage.getItem('showEnglishConj') === 'true';
            }
            newRow.appendChild(td);
            row.parentNode.insertBefore(newRow, row.nextSibling);
            btn.textContent = '✕ Ausblenden';
        });
    });

    // English translation toggle — same event-delegation pattern as
    // the conjugation button itself, for the same reason: each toggle
    // switch is created fresh whenever a table is rendered.
    if (localStorage.getItem('showEnglishConj') === 'true') {
        document.body.classList.add('show-english');
    }
    document.addEventListener('change', function(e) {
        var toggle = e.target.closest('.conj-en-toggle-input');
        if (!toggle) return;
        document.body.classList.toggle('show-english', toggle.checked);
        localStorage.setItem('showEnglishConj', toggle.checked ? 'true' : 'false');
        document.querySelectorAll('.conj-en-toggle-input').forEach(function(t) {
            t.checked = toggle.checked;
        });
    });
})();
</script>"""


WORTSCHATZ_SEARCH_SCRIPT = """<script>
// Live search + POS filter for Wortschatz table rows, grouped by topic section
(function() {
    var input = document.getElementById('wsSearchInput');
    var noResults = document.getElementById('wsNoResults');
    var activePOS = 'ALL';
    if (!input) return;

    var wordCountEl = document.getElementById('wsWordCount');
    var filterCountEl = document.getElementById('wsFilterCount');

    // Folds German special characters to ASCII equivalents so search works
    // both ways on a US keyboard: typing "abschliessen" matches "abschließen",
    // "Maerz" matches "März", "ueben" matches "üben" — and typing the accented
    // letters directly still works too, since both sides are folded the same way.
    function foldGerman(s) {
        return s
            .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue')
            .replace(/ß/g, 'ss');
    }

    function filterRows() {
        var q = foldGerman(input.value.toLowerCase().trim());
        var anyVisible = false;
        var visibleCount = 0;
        document.querySelectorAll('.topic-section').forEach(function(section) {
            var sectionHasMatch = false;
            var lastRowVisible = true;
            section.querySelectorAll('tbody tr').forEach(function(row) {
                if (row.classList.contains('conj-row-container-ws')) {
                    // Conjugation panel rows have no data of their own —
                    // always follow the visibility of the verb row above them.
                    row.style.display = lastRowVisible ? '' : 'none';
                    return;
                }
                var blob = foldGerman(row.getAttribute('data-search') || '');
                var pos = row.getAttribute('data-pos') || '';
                var irregular = row.getAttribute('data-irregular') === 'true';
                var reflexive = row.getAttribute('data-reflexive') === 'true';
                var matchesSearch = !q || blob.indexOf(q) > -1;
                var matchesPOS = activePOS === 'ALL' || pos === activePOS ||
                                 (activePOS === 'irregular' && irregular) ||
                                 (activePOS === 'reflexive' && reflexive);
                var show = matchesSearch && matchesPOS;
                row.style.display = show ? '' : 'none';
                lastRowVisible = show;
                if (show) { sectionHasMatch = true; visibleCount++; }
            });
            section.style.display = sectionHasMatch ? '' : 'none';
            if (sectionHasMatch) anyVisible = true;
        });
        if (noResults) noResults.style.display = anyVisible ? 'none' : 'block';
        var label = visibleCount + (visibleCount === 1 ? ' Wort' : ' Wörter');
        if (wordCountEl) wordCountEl.textContent = label;
        if (filterCountEl) filterCountEl.textContent = label;
    }

    input.addEventListener('input', filterRows);

    document.querySelectorAll('.pos-filter-ws button').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.pos-filter-ws button').forEach(function(b) { b.classList.remove('active'); });
            btn.classList.add('active');
            activePOS = btn.getAttribute('data-pos');
            filterRows();
        });
    });
})();
</script>"""


# ── POS detection ─────────────────────────────────────────────────────────────
_VERB_RE      = re.compile(r'^[a-zäöüß]+en$')
_ADJ_SUFFIXES = ('lich','ig','isch','bar','sam','haft','los','ell','iv','al','ös','iert','end','ent')
_KNOWN_ADV = {
    'ab','abends','also','auch','außen','außerdem','bald','bereits','besonders',
    'bisher','da','dabei','daher','damals','danach','dann','deshalb','dort',
    'dorthin','draußen','ebenso','eigentlich','endlich','erst','fast','ganz',
    'gar','genau','gerade','gern','gerne','gestern','heute','hin','hoffentlich',
    'irgendwann','irgendwo','ja','jetzt','kaum','leider','links','mal','manchmal',
    'meistens','morgens','nachmittags','natürlich','nie','noch','normalerweise',
    'nun','nur','oben','oft','rechts','schon','sehr','seitdem','selten','sofort',
    'sonst','trotzdem','überall','überhaupt','übrigens','unbedingt','ungefähr',
    'unten','vielleicht','vorbei','vorher','wahrscheinlich','wieder','wirklich',
    'wo','zuerst','zurzeit','zusammen','zwar','morgen','viel','wenig','mehr',
    'immer','bereits','fast','ganz','kaum','doch','halt','eben','wohl',
    'schließlich','allerdings','freilich','gleichwohl','nichtsdestotrotz',
    'nichtsdestoweniger','somit','demnach','ergo','mithin','zumal','indessen',
    'überdies','hierbei','insofern','ebendies','indes',
}
_KNOWN_CONJ = {
    'aber','als','bevor','denn','dass','damit','ehe','entweder','falls',
    'nachdem','ob','obwohl','oder','seit','seitdem','sobald','sofern',
    'solange','sondern','sowie','und','während','weder','weil','wenn',
    'wie','wenngleich','obgleich','wohingegen',
}
_KNOWN_PREP = {
    'an','auf','aus','außer','bei','bis','durch','für','gegen','hinter',
    'in','mit','nach','neben','ohne','seit','über','um','unter','von','vor',
    'während','wegen','zwischen','zu','gegenüber','statt','trotz','innerhalb',
    'außerhalb','mithilfe','angesichts','aufgrund','infolge','zwecks',
}
_KNOWN_PRON = {
    'ich','du','er','sie','es','wir','ihr','man','sich','dieser','jener',
    'wer','was','jemand','niemand','etwas','nichts','beide',
}
_DETERMINER = {
    'dies-','ein/eine','gern(e)','jeder/jede/jedes','kein/keine',
    'lang(e)','nah(e)','welch-','alle','einige','viele','wenige',
    'mehrere','manche','solche',
}

def is_irregular_verb(pp):
    """A verb is 'irregular' (unregelmäßig) for filtering purposes if it
    is anything other than a pure weak conjugation — matching how German
    textbooks (e.g. Netzwerk's 'Unregelmäßige Verben' appendix) define
    the category: strong verbs (schwimmen->schwamm), mixed verbs
    (bringen->brachte, irregular stem but weak-style endings), and
    modal/suppletive verbs (können, sein) all count as irregular.
    A regular weak verb's präteritum_stamm is always exactly
    reg_stem + 'te' (or + 'ete' for epenthetic-e stems like arbeiten) —
    anything else means the stem itself changed irregularly."""
    if not pp:
        return False
    if pp.get('praesens_voll') or pp.get('praesens_stamm'):
        return True  # ablaut or fully suppletive present tense
    infinitiv = pp.get('infinitiv', '')
    prefix = pp.get('trennbares_praefix')
    reg_stem = _regular_stem(infinitiv, prefix)
    praeteritum_stamm = pp.get('praeteritum_stamm', '')
    if praeteritum_stamm in (reg_stem + 'te', reg_stem + 'ete'):
        return False
    return True


def detect_pos(w):
    """Detect part of speech from de field and article field."""
    de  = w['de'].strip()
    dl  = de.lower()
    art = w.get('article','')
    if art in ('m.','f.','n.','m./f.','Pl.'): return 'noun'
    if de.endswith('.') or de.endswith('!') or de.endswith('?'): return 'proverb'
    if '...' in de: return 'phrase'
    if dl in _DETERMINER: return 'determiner'
    if dl in _KNOWN_PRON: return 'pronoun'
    if dl in _KNOWN_CONJ and ' ' not in de: return 'conjunction'
    if dl.startswith('sich ') and dl.endswith('en'): return 'verb'
    if w.get('conjugation'): return 'verb'  # authoritative — has principal parts, so it's a verb regardless of -eln/-ern suffix
    if _VERB_RE.match(dl): return 'verb'
    if ' ' in de and not re.match(r'^(der|die|das)\s+', de, re.I):
        if dl.split()[-1].endswith('en'): return 'phrase'
    if re.match(r'^(der|die|das)\s+', de, re.I) and ',' not in de: return 'noun'
    if dl in _KNOWN_ADV: return 'adverb'
    if dl in _KNOWN_PREP and ' ' not in de: return 'preposition'
    if dl.endswith(_ADJ_SUFFIXES) and ' ' not in de: return 'adjective'
    if ' ' in de: return 'phrase'
    if len(de) > 2 and dl[0].islower(): return 'adjective'
    return 'adverb'  # fallback for particles


def first_letter(de):
    """Return alphabet section key for a German de field."""
    c = de.strip()[0].upper()
    return {'Ä':'A', 'Ö':'O', 'Ü':'U'}.get(c, c if c.isalpha() else '#')

def make_word_card(w):
    """Build a single word-card div from a JSON entry."""
    de    = w['de']
    en    = w['en']
    level = w['level']
    ex    = w.get('example','').strip()
    ex_en = w.get('example_en','').strip()
    cols  = w.get('collocations', [])
    conj  = w.get('conjugation')
    color = COLORS[level]
    pos   = detect_pos(w)

    col_html = ''
    if cols:
        pills = ''.join(
            f'<span class="col-item">{htmllib.escape(c)}</span>' for c in cols)
        col_html = f'<div class="word-collocations">{pills}</div>'

    conj_html = ''
    if pos == 'verb' and conj:
        parts = []
        if conj.get('er_sie_es'):
            parts.append(f'<strong>er/sie/es:</strong> {htmllib.escape(conj["er_sie_es"])}')
        if conj.get('praeteritum'):
            parts.append(f'<strong>Präteritum:</strong> {htmllib.escape(conj["praeteritum"])}')
        if conj.get('perfekt'):
            parts.append(f'<strong>Perfekt:</strong> {htmllib.escape(conj["perfekt"])}')
        if conj.get('governs'):
            parts.append(f'<strong>+</strong> {htmllib.escape(conj["governs"])}')
        if parts:
            conj_html = (f'\n        <div class="word-conjugation">'
                         f'{" · ".join(parts)}</div>')

    ex_html = ''
    if ex:
        en_span = (f'<br><span class="ex-en">{htmllib.escape(ex_en)}</span>'
                   if ex_en else '')
        ex_html = (f'\n        <div class="word-example">'
                   f'<span class="ex-de">{htmllib.escape(ex)}</span>'
                   f'{en_span}{col_html}</div>')

    return (
        f'<div class="word-card" '
        f'data-de="{htmllib.escape(de.lower(), quote=True)}" '
        f'data-en="{htmllib.escape(en, quote=True)}" '
        f'data-level="{level}" '
        f'data-pos="{pos}" '
        f'data-irregular="{"true" if (pos == "verb" and is_irregular_verb(conj)) else "false"}" '
        f'data-reflexive="{"true" if (pos == "verb" and bool(conj and conj.get("reflexiv"))) else "false"}" '
        f'data-ex="{htmllib.escape(ex, quote=True)}">\n'
        f'    <div class="word-main">\n'
        f'        <div class="word-de-wrap">\n'
        f'            <span class="word-de">{htmllib.escape(de)}</span>\n'
        f'            <span class="word-art"></span>\n'
        f'            <span class="badge rounded-pill word-level" '
        f'style="background:{color}">{level}</span>\n'
        f'        </div>\n'
        f'        <div class="word-en">{htmllib.escape(en)}</div>'
        f'{conj_html}'
        f'{ex_html}\n'
        f'    </div>\n'
        f'</div>'
    )

def build_jsonld(words):
    """Build the JSON-LD structured data block for dictionary.html."""
    counts = Counter(w['level'] for w in words)
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "DefinedTermSet",
                "@id": "https://abdullahbutt.github.io/deutsch-lernen-goethe-a1-c2/dictionary.html#termset",
                "name": "Deutsch Lernen \u2014 Goethe-Zertifikat A1 to C2 Dictionary",
                "description": (f"Free German\u2013English vocabulary dictionary with {len(words):,} words and "
                                f"phrases covering CEFR levels A1\u2013C2. Includes example sentences, "
                                f"collocations and audio pronunciation. Aligned to Goethe-Zertifikat "
                                f"and telc exam requirements."),
                "url": "https://abdullahbutt.github.io/deutsch-lernen-goethe-a1-c2/dictionary.html",
                "inLanguage": ["de", "en"],
                "numberOfItems": len(words),
                "license": "https://creativecommons.org/licenses/by-nc/4.0/",
                "creator": {
                    "@type": "Person",
                    "name": "Abdullah Butt",
                    "url": "https://github.com/abdullahbutt"
                },
                "about": [
                    {"@type": "Thing", "name": "German language"},
                    {"@type": "Thing", "name": "Goethe-Zertifikat"},
                    {"@type": "Thing", "name": "CEFR"},
                    {"@type": "Thing", "name": "Language learning"}
                ],
                "educationalLevel": "A1, A2, B1, B2, C1, C2",
                "keywords": ("Deutsch lernen, German vocabulary, Goethe-Zertifikat, "
                             "telc, CEFR, A1 Wortschatz, B1 Wortschatz, C1 Wortschatz, learn German")
            },
            {
                "@type": "Dataset",
                "@id": "https://abdullahbutt.github.io/deutsch-lernen-goethe-a1-c2/dictionary.html#dataset",
                "name": "German\u2013English CEFR Vocabulary Dataset (A1\u2013C2)",
                "description": (f"Structured bilingual German\u2013English vocabulary dataset with "
                                f"{len(words):,} entries, CEFR level tags (A1\u2013C2), example sentences, "
                                f"English translations and B2\u2013C2 collocations."),
                "url": "https://abdullahbutt.github.io/deutsch-lernen-goethe-a1-c2/dictionary.html",
                "inLanguage": ["de", "en"],
                "license": "https://creativecommons.org/licenses/by-nc/4.0/",
                "creator": {"@type": "Person", "name": "Abdullah Butt"},
                "distribution": {
                    "@type": "DataDownload",
                    "encodingFormat": "application/json",
                    "contentUrl": "https://raw.githubusercontent.com/abdullahbutt/deutsch-lernen-goethe-a1-c2/main/words_final.json"
                },
                "variableMeasured": [
                    {"@type": "PropertyValue", "name": f"{lv} entries", "value": counts[lv]}
                    for lv in ['A1','A2','B1','B2','C1','C2']
                ]
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home",
                     "item": "https://abdullahbutt.github.io/deutsch-lernen-goethe-a1-c2/"},
                    {"@type": "ListItem", "position": 2, "name": "W\u00f6rterbuch / Dictionary",
                     "item": "https://abdullahbutt.github.io/deutsch-lernen-goethe-a1-c2/dictionary.html"}
                ]
            }
        ]
    }
    return (
        '<script type="application/ld+json">\n'
        + json.dumps(data, ensure_ascii=False, indent=2)
        + '\n</script>'
    )


def build_dictionary(words):
    """
    Fully regenerate dictionary.html word-card section from words_final.json.
    Preserves all HTML outside #wordList (header, search, filters, scripts, footer).
    Inserts letter-header anchor divs at each alphabet boundary.
    Verifies correct DOM order: cards → </main> → footer-placeholder → querySelectorAll.
    """
    dict_path = os.path.join(REPO, 'dictionary.html')
    if not os.path.exists(dict_path):
        print("  ❌ dictionary.html not found — cannot rebuild")
        return False

    with open(dict_path, encoding='utf-8') as f:
        content = f.read()

    # Sort words alphabetically
    sorted_words = sorted(words, key=lambda w: (first_letter(w['de']), w['de'].lower()))

    # Build sections: letter headers + word cards
    sections = []
    current_letter = None
    for w in sorted_words:
        ltr = first_letter(w['de'])
        if ltr != current_letter:
            current_letter = ltr
            sections.append(
                f'<div class="letter-header" id="letter-{ltr}" '
                f'style="font-size:1.5rem;font-weight:700;color:#94a3b8;'
                f'padding:.5rem 0 .25rem;margin-top:.5rem;'
                f'border-bottom:1px solid #e2e8f0">'
                f'{ltr}</div>'
            )
        sections.append(make_word_card(w))

    cards_html = '\n'.join(sections)
    total      = sum(1 for s in sections if 'word-card' in s)
    letters    = sum(1 for s in sections if 'letter-header' in s)

    # Build new #wordList content
    WORDLIST = (
        '<div id="wordList">\n'
        '<div id="noResults" class="text-center py-5" style="display:none">\n'
        '    <p class="fs-5">🔍 No words found</p>\n'
        '    <p>Try a different search term or clear the level filter.</p>\n'
        '</div>\n'
        + cards_html +
        '\n</div>'
    )

    # Find and replace #wordList in the HTML
    wl_open = content.find('<div id="wordList">')
    if wl_open == -1:
        print("  ❌ #wordList div not found in dictionary.html")
        return False

    # Depth-count to find matching closing </div>
    depth, i, wl_close = 0, wl_open, -1
    while i < len(content):
        if content[i:i+5] == '<div ':
            depth += 1
        elif content[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                wl_close = i + 6
                break
        i += 1

    if wl_close == -1:
        print("  ❌ Could not find closing </div> for #wordList")
        return False

    content_new = content[:wl_open] + WORDLIST + content[wl_close:]

    # Inject app install banner (after filters, before word list — not before <main>)
    content_new = inject_install_banner_dict(content_new)
    content_new = re.sub(
        r'id="wordCount">\d+ words',
        f'id="wordCount">{total} words',
        content_new
    )
    content_new = re.sub(
        r'\d[\d\.]+ exam-relevant words from A1',
        f'{total} exam-relevant words from A1',
        content_new
    )

    # Inject / refresh JSON-LD structured data
    jsonld_block = build_jsonld(words)
    content_new = re.sub(
        r'<script type="application/ld\+json">.*?</script>\s*',
        '', content_new, flags=re.DOTALL
    )
    if '</head>' in content_new:
        content_new = content_new.replace('</head>', f'{jsonld_block}\n</head>', 1)

    # Verify DOM order
    qs_pos     = content_new.find('var wordCards = document.querySelectorAll')
    fp_match   = re.search(r'<div\s+id="footer-placeholder"', content_new)
    main_close = content_new.rfind('</main>')
    last_card  = content_new.rfind('class="word-card"')
    last_head  = content_new.rfind('class="letter-header"')

    order_ok = (
        last_card  < qs_pos and
        last_head  < qs_pos and
        main_close < qs_pos and
        (fp_match is None or fp_match.start() < qs_pos)
    )

    with open(dict_path, 'w', encoding='utf-8') as f:
        f.write(content_new)

    print(f"  ✅ dictionary.html — {total} cards, {letters} letter headers, "
          f"order {'✅' if order_ok else '❌'}, "
          f"footer {'✅' if fp_match else '❌'}")
    return True

# ── Wortschatz page builder ────────────────────────────────────────────────────
TOPIC_KEYWORDS = {
    'A1': [
        ('Begrüßung & Alltag',  ['guten','hallo','danke','bitte','auf wiedersehen','tschüss']),
        ('Familie',             ['mutter','vater','kind','mann','frau','bruder','schwester','oma','opa','eltern']),
        ('Zahlen & Zeit',       ['uhr','heute','morgen','woche','monat','jahr','stunde','minute','datum']),
        ('Essen & Trinken',     ['essen','trinken','brot','wasser','kaffee','milch','fleisch','gemüse','obst','ei','suppe','salz','zucker','käse','wurst','butter']),
        ('Wohnen & Haus',       ['haus','wohnung','zimmer','küche','bad','bett','tisch','stuhl','treppe','aufzug','fenster','tür']),
        ('Farben & Eigenschaften',['rot','blau','grün','groß','klein','neu','alt','lang','kurz','warm','kalt']),
        ('Körper & Gesundheit', ['arzt','krank','kopf','hand','auge','ohr','fuß','rücken','bauch','nase','zahn']),
        ('Sonstige A1-Wörter',  []),
    ],
    'A2': [
        ('Zuhause & Wohnen',    ['balkon','aufzug','treppe','vorhang','wand','boden','regal','wecker','seife','klo','mülleimer','briefkasten']),
        ('Essen & Trinken',     ['frühstück','mittagessen','abendessen','kuchen','suppe','butter','käse','wurst','milch','zucker','saft','pizza','erdbeere','joghurt','banane','apfel','brot','salz','mehl']),
        ('Verkehr & Transport', ['fahrrad','u-bahn','bus','taxi','bahnhof','parkplatz','tankstelle','führerschein','flugzeug','straßenbahn','fahrplan','linie','navi']),
        ('Einkaufen & Geld',    ['bargeld','wechselgeld','pfand','tüte','einkauf','preisschild','rückgaberecht','öffnungszeiten','kassierer','warteschlange','gutschein','angebot','einkaufskorb']),
        ('Körper & Gesundheit', ['rücken','zahn','bauch','ohr','nase','kopf','fuß','hand','schulter']),
        ('Wetter & Natur',      ['regen','schnee','wolke','sonne','wind','temperatur','berg','meer','blume','baum']),
        ('Schule & Lernen',     ['lehrer','stift','hausaufgaben','test','schulbus','schüler','wörterbuch','schulferien','aufsatz']),
        ('Familie & Beziehungen',['bruder','schwester','baby','opa','oma','sohn','tochter','eltern','geschwister','cousin']),
        ('Technologie',         ['handy','e-mail','computer','wlan','foto','nachricht','kabel','kopfhörer']),
        ('Freizeit & Stadt',    ['kino','theater','park','schwimmbad','restaurant','café','spaziergang','sport','post','paket','apotheke','uhr','kerze']),
        ('Sonstige A2-Wörter',  []),
    ],
    'B1': [
        ('Arbeit & Beruf',      ['bewerbung','vorstellungsgespräch','arbeitsvertrag','probezeit','gehalt','überstunden','homeoffice','betrieb','fachkraft','weiterbildung','teamleiter','besprechung','protokoll','präsentation']),
        ('Gesundheit',          ['arzttermin','rezept','erkrankung','hausarzt','allergie','erste hilfe','sportverletzung','grippe','fitnessstudio','facharzt','notfall','krankenversicherung','physiotherapie','krankenhaus']),
        ('Gesellschaft',        ['ehrenamt','toleranz','kindergeld','flüchtlingshilfe','inklusion','bürgerbeteiligung','sozialhilfe','gemeinschaft','menschenwürde','wahlrecht','grundsicherung','zivilgesellschaft']),
        ('Medien',              ['podcast','berichterstattung','interview','zeitung','pressefreiheit','streaming','dokumentation','desinformation','falschmeldung','livestream','rundfunk']),
        ('Reisen',              ['unterkunft','sehenswürdigkeit','reiseziel','reiseversicherung','ausflug','hostel','sightseeing','flughafen','übernachtung','wanderung','touristeninformation','fähre']),
        ('Umwelt',              ['klimaschutz','recycling','energieverbrauch','sonnenenergie','elektroauto','abgase','plastiktüte','regenwald','windkraft','trinkwasser','biodiversität','meeresverschmutzung']),
        ('Sonstige B1-Wörter',  []),
    ],
    'B2': [
        ('Politik & Recht',     ['meinungsfreiheit','pressekonferenz','gesetzentwurf','grundgesetz','rechtsstaat','asylrecht','bürgerrechte','bundesrat','koalitionsverhandlung','volksabstimmung','verfassungsschutz']),
        ('Medien & Tech',       ['medienlandschaft','cyberangriff','datenschutz','algorithmus','desinformation','onlineplattform','netzneutralität','whistleblower','medienkompetenz','zensur']),
        ('Umwelt & Wiss.',      ['treibhausgasneutralität','artenschwund','kreislaufwirtschaft','kernenergie','solarzelle','gletscherschmelzen','biodiversitätskrise','elektromobilität','wasseraufbereitung']),
        ('Wirtschaft',          ['lieferkette','mindestlohn','kurzarbeit','tarifverhandlung','fachkräfteproblem','wirtschaftswachstum','kaufkraft','startup','wirtschaftsspionage','konjunkturprogramm']),
        ('Gesellschaft',        ['chancenungleichheit','pflegelücke','wohnungsnot','demografischer wandel','gesundheitsversorgung','bildungsgerechtigkeit','rentenreform','impfpflicht']),
        ('Sonstige B2-Wörter',  []),
    ],
    'C1': [
        ('Recht',               ['rechtsstaatlichkeit','verfassungsgericht','normenhierarchie','gewohnheitsrecht','legalitätsprinzip','vollstreckung','amnestie','strafjustiz','rechtsmittel','staatshaftung']),
        ('Wirtschaft',          ['fiskalunion','geldmenge','rezessionsbekämpfung','kapitalmarktregulierung','negativzinsen','wirtschaftsprognose','oligopol','stagflation','umverteilung']),
        ('Wissenschaft',        ['kognitionswissenschaft','epigenetik','immuntherapie','neuroplastizität','genomsequenzierung','systembiologie','präzisionsmedizin','mikrobiom','pandemievorsorge']),
        ('Philosophie & Ling.', ['phänomenologie','hermeneutik','pragmatik','semantik','syntax','diskursanalyse','positivismus','kognitivismus','erzähltheorie','spracherwerbstheorie']),
        ('Politik',             ['systemtransformation','subsidiaritätsprinzip','kommunitarismus','demokratiedefizit','extremismusprävention','vetomacht','ordnungspolitik']),
        ('Umwelt',              ['klimaanpassung','biodiversitätsstrategie','suffizienz','ökosystemleistung','entwaldung','ressourceneffizienz','klimafinanzierung','co₂-bepreisung']),
        ('Technologie',         ['plattformökonomie','blockchain','internet der dinge','quantencomputing','cybersicherheit','sprachverarbeitung','datenhoheit','deepfake']),
        ('Kultur',              ['kulturerbe','kunstförderung','kulturimperialismus','literarische kanonbildung','filmästhetik','kanonrevision']),
        ('Sonstige C1-Wörter',  []),
    ],
    'C2': [
        ('Konnektoren',         ['allerdings','demgegenüber','gleichsam','mitunter','überdies','zuweilen','wenngleich','hierbei','indessen','insofern','ebendies']),
        ('Rhetorik',            ['antilogie','aporie','ellipse','oxymoron','syllogismus','tautologie','antithese','apostrophe','ethos','topos','prolepsis','paraphrase']),
        ('Literaturgeschichte', ['bildungsroman','verfremdung','weimarer klassik','zwischenkriegszeit','groteske','leitmotiv','intertextualität','rezeptionsästhetik','dekonstruktion','modernismus']),
        ('Philosophie',         ['ding an sich','intersubjektivität','teleologie','weltanschauung','apriori','verdingligung','sein-zum-tode','kontingenzphilosophie']),
        ('Politische Sprache',  ['deutungsmonopol','populismus','postdemokratie','framing','pfadabhängigkeit','technokratie','staatsversagen']),
        ('Sprichwörter',        ['hochmut kommt','lügen haben','übung macht','ausnahmen bestätigen','kleider machen','gut ding will','geteiltes leid','viele köche','aller anfang']),
        ('Sonstige C2-Wörter',  []),
    ],
}

def get_topic(w, level):
    de_lower = w['de'].lower()
    for topic, kws in TOPIC_KEYWORDS.get(level, []):
        if not kws:
            continue
        if any(kw in de_lower for kw in kws):
            return topic
    return TOPIC_KEYWORDS[level][-1][0]

def build_wortschatz_page(level, level_words):
    color  = META[level]['color']
    desc   = META[level]['desc']
    count  = len(level_words)
    prev   = {'A1':None,'A2':'A1','B1':'A2','B2':'B1','C1':'B2','C2':'C1'}[level]
    nxt    = {'A1':'A2','A2':'B1','B1':'B2','B2':'C1','C1':'C2','C2':None}[level]

    by_topic = defaultdict(list)
    for w in sorted(level_words, key=lambda x: x['de'].lower()):
        by_topic[get_topic(w, level)].append(w)

    ordered = [t[0] for t in TOPIC_KEYWORDS.get(level, [])]
    for t in by_topic:
        if t not in ordered:
            ordered.append(t)

    topic_nav = []
    for topic in ordered:
        ws = by_topic.get(topic, [])
        if not ws:
            continue
        slug = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')
        topic_nav.append((topic, slug, len(ws)))

    jump_html = '\n'.join(
        f'<a href="#{sl}" class="btn btn-sm btn-outline-secondary mb-1 w-100 text-start">'
        f'{tp[:22]}{"…" if len(tp)>22 else ""} '
        f'<span class="badge ms-1" style="background:{color};font-size:.65rem">{n}</span></a>'
        for tp, sl, n in topic_nav
    )

    sections = ''
    for topic in ordered:
        ws = by_topic.get(topic, [])
        if not ws:
            continue
        slug = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')
        sections += f'<div class="topic-section" data-topic-section="{slug}">\n'
        sections += (f'<h2 id="{slug}" class="mt-4 mb-3" style="color:{color}">'
                     f'{htmllib.escape(topic)} '
                     f'<small class="text-muted fs-6">({len(ws)} Wörter)</small></h2>\n')
        sections += '<div class="table-responsive">\n'
        sections += ('<table class="table table-bordered table-hover vocab-table mb-4">\n'
                     '<thead class="table-dark"><tr>'
                     '<th style="width:22%">Deutsch</th>'
                     '<th style="width:15%">Englisch</th>'
                     '<th>Beispielsatz</th>'
                     '</tr></thead>\n<tbody>\n')
        for w in ws:
            de  = htmllib.escape(w['de'])
            en  = htmllib.escape(w['en'])
            exd = htmllib.escape(w.get('example', ''))
            exe = htmllib.escape(w.get('example_en', ''))
            cols = w.get('collocations', [])
            pos = detect_pos(w)
            col_html = ''
            if cols:
                pills = ' '.join(
                    f'<span class="badge rounded-pill text-bg-light border me-1" '
                    f'style="font-size:.7rem;font-weight:400">{htmllib.escape(c)}</span>'
                    for c in cols[:3])
                col_html = f'<div class="mt-1">{pills}</div>'
            exe_row = (f'<span class="ex-en d-block text-muted small">{exe}</span>' if exe else '')
            conj_btn = (f'<br><button type="button" class="conj-toggle-ws" '
                        f'data-de-lower="{htmllib.escape(w["de"].lower())}">'
                        f'📖 Konjugation</button>' if pos == 'verb' else '')
            search_blob = htmllib.escape(
                f"{w['de']} {w['en']} {w.get('example','')} {w.get('example_en','')}".lower(),
                quote=True)
            is_irregular = pos == 'verb' and is_irregular_verb(w.get('conjugation'))
            is_reflexive = pos == 'verb' and bool(w.get('conjugation', {}).get('reflexiv'))
            sections += (
                f'<tr data-pos="{pos}" data-irregular="{"true" if is_irregular else "false"}" '
                f'data-reflexive="{"true" if is_reflexive else "false"}" data-search="{search_blob}">\n'
                f'  <td class="fw-semibold de-word">{de}{conj_btn}</td>\n'
                f'  <td class="text-muted">{en}</td>\n'
                f'  <td><span class="ex-de d-block">{exd}</span>{exe_row}{col_html}</td>\n'
                f'</tr>\n'
            )
        sections += '</tbody>\n</table>\n</div>\n</div>\n'



    prev_btn = (f'<a href="../{prev}/01_Wortschatz.html" class="btn btn-sm btn-outline-secondary">'
                f'← {prev} Wortschatz</a>' if prev else '')
    nxt_btn  = (f'<a href="../{nxt}/01_Wortschatz.html" class="btn btn-sm text-white" '
                f'style="background:{META[nxt]["color"]}">{nxt} Wortschatz →</a>' if nxt else '')

    return f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="description" content="Komplette {level}-Vokabelliste: {count} Wörter mit Beispielsätzen, englischen Übersetzungen und Aussprache-Funktion für Goethe- und telc-Prüfungen.">
    <meta name="keywords" content="Deutsch lernen, {level} Wortschatz, Goethe, telc, Vokabeln {level}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
{FAVICON_BLOCK}
    <meta name="theme-color" content="#1d4ed8">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Deutsch Lernen">
    <title>01 Wortschatz – {level} | {count} Vokabeln</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root{{--page-bg:#f5f7fb;--page-text:#1f2937;--muted-text:#334155;--card-bg:#fff;--card-shadow:0 .5rem 1.25rem rgba(0,0,0,.08);--alpha-bg:rgba(245,247,251,.95);--alpha-border:#e5e7eb;--table-bg:#fff;--table-stripe:#f8fafc;--table-hover:#eaf3ff;}}
        [data-bs-theme="dark"]{{--page-bg:#0f172a;--page-text:#e2e8f0;--muted-text:#cbd5e1;--card-bg:#111827;--card-shadow:0 .5rem 1.25rem rgba(0,0,0,.35);--alpha-bg:rgba(17,24,39,.95);--alpha-border:#374151;--table-bg:#111827;--table-stripe:#172033;--table-hover:#1f2a44;}}
        html{{scroll-behavior:smooth;}}
        body{{background:var(--page-bg);font-size:1.05rem;line-height:1.7;color:var(--page-text);}}
        .content-card{{border:0;border-radius:1rem;box-shadow:var(--card-shadow);background:var(--card-bg);}}
        .page-header{{border-bottom:2px solid #e9ecef;padding-bottom:1rem;margin-bottom:1.5rem;}}
        .breadcrumb a{{text-decoration:none;}} .breadcrumb a:hover{{text-decoration:underline;}}
        .jump-bar{{position:sticky;top:5rem;z-index:1020;background:var(--alpha-bg);border:1px solid var(--alpha-border);border-radius:.75rem;padding:.75rem;backdrop-filter:blur(4px);max-height:80vh;overflow-y:auto;}}
        .jump-layout{{display:block;}}
        @media(min-width:992px){{.jump-layout{{display:grid;grid-template-columns:15rem minmax(0,1fr);gap:1.5rem;align-items:start;}}.jump-bar{{top:6rem;}}}}
        h2[id]{{scroll-margin-top:6rem;}}
        .ws-search-shade{{background:var(--page-bg);border-radius:.9rem;padding:.6rem;}}
        .ws-search-wrap{{position:relative;}}
        .ws-search-wrap input{{background:var(--card-bg);border:2px solid var(--alpha-border);border-radius:.75rem;padding:.7rem 1rem .7rem 2.75rem;font-size:1rem;color:var(--page-text);width:100%;transition:border-color .2s;}}
        .ws-search-wrap input:focus{{outline:none;border-color:#1d4ed8;box-shadow:0 0 0 3px rgba(29,78,216,.15);}}
        .ws-search-wrap input::placeholder{{color:var(--muted-text);}}
        .ws-search-icon{{position:absolute;left:1rem;top:50%;transform:translateY(-50%);opacity:.4;pointer-events:none;color:var(--page-text);}}
        .filter-label-ws{{font-size:.8rem;color:var(--muted-text);font-weight:600;white-space:nowrap;min-width:4.5rem;}}
        .pos-filter-ws{{display:flex;flex-wrap:wrap;gap:.4rem;}}
        .pos-filter-ws button{{padding:.25rem .75rem;border-radius:999px;border:1px solid var(--alpha-border);background:var(--card-bg);color:var(--page-text);cursor:pointer;font-size:.85rem;transition:all .15s;}}
        .pos-filter-ws button:hover{{background:var(--table-stripe);}}
        .pos-filter-ws button.active{{background:#7c3aed;border-color:#7c3aed;color:#fff;}}
        .vocab-table th,.vocab-table td{{vertical-align:top;padding:.5rem .65rem;}}
        .de-word{{font-size:1rem;}} .ex-de{{font-size:.92rem;}} .ex-en{{font-size:.82rem;}}
        .back-to-top{{position:fixed;right:1rem;bottom:1rem;z-index:1030;display:none;width:2.8rem;height:2.8rem;align-items:center;justify-content:center;box-shadow:0 .5rem 1rem rgba(13,110,253,.3);}}
        .theme-toggle{{min-width:5.8rem;height:2.2rem;display:inline-flex;align-items:center;justify-content:center;padding:0 .65rem;}}
        .site-footer{{background:var(--page-bg);color:var(--page-text);font-size:.9rem;}}
        [data-bs-theme="dark"] .site-footer{{background:#1e293b!important;color:#e2e8f0;border-color:#374151!important;}}
        [data-bs-theme="dark"] .table{{--bs-table-bg:var(--table-bg);--bs-table-striped-bg:var(--table-stripe);}}
        [data-bs-theme="dark"] .table-bordered td,[data-bs-theme="dark"] .table-bordered th{{border-color:#374151;}}
        [data-bs-theme="dark"] .badge.text-bg-light{{background:#1e293b!important;color:#cbd5e1!important;border-color:#374151!important;}}
        .conj-toggle-ws{{display:inline-flex;align-items:center;gap:.25rem;margin-top:.3rem;font-size:.72rem;font-weight:700;color:#fff;cursor:pointer;user-select:none;border:none;background:#7c3aed;border-radius:999px;padding:.2rem .6rem;box-shadow:0 1px 3px rgba(124,58,237,.35);transition:background .15s,transform .1s;}}
        .conj-toggle-ws:hover{{background:#6d28d9;transform:translateY(-1px);}}
        .conj-toggle-ws:disabled{{background:#94a3b8;box-shadow:none;cursor:default;transform:none;}}
        [data-bs-theme="dark"] .conj-toggle-ws{{background:#8b5cf6;}}
        [data-bs-theme="dark"] .conj-toggle-ws:hover{{background:#7c3aed;}}
        .conj-row-container-ws td{{background:var(--table-stripe);padding:1rem 1.25rem;}}
        .conj-table-wrap-ws{{width:100%;margin-top:0;font-size:.82rem;border-top:none;padding-top:0;}}
        .conj-mood-title-ws{{font-weight:700;color:#0d7d4d;margin:.9rem 0 .5rem;font-size:.85rem;text-transform:uppercase;letter-spacing:.03em;}}
        [data-bs-theme="dark"] .conj-mood-title-ws{{color:#4ade80;}}
        .conj-mood-title-ws:first-child{{margin-top:0;}}
        .conj-mood-grid-ws{{display:grid;grid-template-columns:repeat(auto-fill,minmax(12rem,1fr));gap:.6rem;}}
        .conj-tense-block-ws{{background:var(--table-stripe);border:1px solid var(--alpha-border);border-radius:.5rem;padding:.55rem .7rem;}}
        .conj-tense-label-ws{{font-weight:700;text-align:center;margin-bottom:.4rem;padding-bottom:.35rem;font-size:.76rem;color:var(--page-text);border-bottom:1px solid var(--alpha-border);}}
        .conj-row-ws{{padding:.1rem 0;font-size:.78rem;line-height:1.3;}}
        .conj-en-line-ws{{display:none;color:var(--muted-text);font-style:italic;font-size:.72rem;line-height:1.2;padding-left:.1rem;}}
        body.show-english .conj-en-line-ws{{display:block;}}
        .conj-en-toggle-wrap-ws{{display:flex;align-items:center;gap:.5rem;margin-bottom:.6rem;font-size:.8rem;color:var(--muted-text);}}
        .conj-en-toggle-ws{{position:relative;display:inline-block;width:2.4rem;height:1.3rem;flex-shrink:0;}}
        .conj-en-toggle-ws input{{opacity:0;width:0;height:0;}}
        .conj-en-toggle-slider-ws{{position:absolute;cursor:pointer;inset:0;background:#cbd5e1;border-radius:999px;transition:.2s;}}
        .conj-en-toggle-slider-ws:before{{content:"";position:absolute;height:1rem;width:1rem;left:.15rem;bottom:.15rem;background:#fff;border-radius:50%;transition:.2s;}}
        .conj-en-toggle-ws input:checked + .conj-en-toggle-slider-ws{{background:#7c3aed;}}
        .conj-en-toggle-ws input:checked + .conj-en-toggle-slider-ws:before{{transform:translateX(1.1rem);}}
        .conj-person-ws{{color:var(--muted-text);margin-right:.25rem;}}
        .conj-imperativ-row-ws{{display:grid;grid-template-columns:repeat(auto-fill,minmax(12rem,1fr));gap:.6rem;}}
        .conj-imperativ-row-ws span{{background:var(--table-stripe);border:1px solid var(--alpha-border);border-radius:.5rem;padding:.5rem .7rem;text-align:center;font-size:.78rem;display:block;}}
    </style>
</head>
<body id="top">
<div id="header-placeholder"></div>
<script>
(function(){{var s=localStorage.getItem('theme')||(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.setAttribute('data-bs-theme',s);var path=window.location.pathname.replace(/\\\\/g,'/');var lm=path.match(/\\/(A1|A2|B1|B2|C1|C2)\\//);var prefix=lm?'../':'';var cl=lm?lm[1]:null;var modules={{A1:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html'],A2:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html'],B1:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html'],B2:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html'],C1:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html'],C2:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html']}};var labels=['01 Wortschatz','02 Grammatik','03 Sätze','04 Lesen','05 Hören','06 Sprechen','07 Schreiben','08 Musterprüfung'];var hFb='<nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm sticky-top"><div class="container"><a class="navbar-brand" href="BASE/index.html">Deutsch Lernen</a></div></nav>';function renderHeader(html){{html=html.replace(/BASE\\//g,prefix);document.getElementById('header-placeholder').innerHTML=html;if(cl){{document.querySelectorAll('.dropdown-item[data-level]').forEach(function(el){{if(el.getAttribute('data-level')===cl){{el.classList.add('active');el.setAttribute('aria-current','page');}}}}); var mf=modules[cl];var ul='<ul class="dropdown-menu dropdown-menu-end dropdown-menu-lg-start"><li><a class="dropdown-item" href="README.html">📖 Overview</a></li><li><hr class="dropdown-divider"></li>';mf.forEach(function(f,i){{ul+='<li><a class="dropdown-item" href="'+f+'">'+labels[i]+'</a></li>';}}); ul+='</ul>';var li=document.createElement('li');li.className='nav-item dropdown';li.innerHTML='<a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">'+cl+' Modules</a>'+ul;var nav=document.getElementById('nav-main-links');if(nav)nav.appendChild(li);}}var btn=document.getElementById('themeToggle');if(btn){{function sync(){{var d=document.documentElement.getAttribute('data-bs-theme')==='dark';btn.textContent=d?'☀️ Light':'🌙 Dark';}}sync();btn.addEventListener('click',function(){{var n=document.documentElement.getAttribute('data-bs-theme')==='dark'?'light':'dark';document.documentElement.setAttribute('data-bs-theme',n);localStorage.setItem('theme',n);sync();}});}}}}
fetch(prefix+'header.html').then(function(r){{return r.ok?r.text():Promise.reject();}}).then(renderHeader).catch(function(){{renderHeader(hFb);}});
}})();
</script>

<main class="container py-4 py-lg-5">
<div class="card content-card">
<div class="card-body p-4 p-lg-5">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb small mb-3">
            <li class="breadcrumb-item"><a href="../index.html">Home</a></li>
            <li class="breadcrumb-item"><a href="index.html">{level}</a></li>
            <li class="breadcrumb-item active">01 Wortschatz</li>
        </ol>
    </nav>
    <div class="page-header d-flex flex-wrap justify-content-between align-items-center gap-3">
        <h1 class="h2 mb-0">01 Wortschatz</h1>
        <div class="d-flex gap-2 align-items-center flex-wrap">
            <span class="badge fs-6 px-3 py-2" style="background:{color}">{level}</span>
            <span class="badge bg-secondary" id="wsWordCount">{count} Wörter</span>
        </div>
    </div>
    <p class="text-muted mb-1">{htmllib.escape(desc)}</p>
    <p class="text-muted small mb-3">
        Klicke auf <strong>🔊</strong> um Aussprache zu hören.
        Jeder Eintrag enthält Beispielsatz und englische Übersetzung.
    </p>

    <div class="mb-4">
        <div class="ws-search-shade">
        <div class="ws-search-wrap">
            <svg class="ws-search-icon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
            <input type="text" id="wsSearchInput"
                   placeholder="Suche (ä = ae, ö = oe, ü = ue, ß = ss)..." autocomplete="off">
        </div>
        </div>
        <div class="d-flex align-items-center gap-2 flex-wrap mt-2">
            <span class="filter-label-ws">Wortart:</span>
            <div class="pos-filter-ws">
                <button type="button" data-pos="ALL" class="active">Alle</button>
                <button type="button" data-pos="noun">🔵 Nomen</button>
                <button type="button" data-pos="verb">🟢 Verben</button>
                <button type="button" data-pos="adjective">🟠 Adjektive</button>
                <button type="button" data-pos="adverb">🟣 Adverbien</button>
                <button type="button" data-pos="phrase">⬜ Wendungen</button>
                <button type="button" data-pos="irregular">🔄 Unregelmäßige Verben</button>
                <button type="button" data-pos="reflexive">🔁 Reflexive Verben</button>
            </div>
            <span class="badge bg-secondary" id="wsFilterCount">{count} Wörter</span>
        </div>
        <div id="wsNoResults" class="text-center text-muted py-4" style="display:none">
            Keine Wörter gefunden. Versuche einen anderen Suchbegriff.
        </div>
    </div>

    <div class="jump-layout">
    <div><div class="jump-bar">
        <div class="fw-semibold small mb-2" style="color:{color}">📚 Themen</div>
        {jump_html}
        <hr class="my-2">
        <a href="index.html" class="btn btn-sm btn-outline-secondary w-100 mt-1">← {level} Übersicht</a>
        {f'<a href="../{nxt}/01_Wortschatz.html" class="btn btn-sm w-100 mt-1 text-white" style="background:{META[nxt]["color"]}">{nxt} Wortschatz →</a>' if nxt else ''}
    </div></div>
    <div>
        {sections}
        <div class="d-flex justify-content-between mt-4 flex-wrap gap-2">
            {prev_btn}
            <a href="#top" class="btn btn-sm btn-outline-secondary">↑ Nach oben</a>
            {nxt_btn}
        </div>
    </div>
    </div>
</div>
</div>
</main>

<a href="#top" id="backToTop" class="btn btn-primary rounded-circle back-to-top" aria-label="Back to top">↑</a>
<div id="footer-placeholder"></div>
<script>
(function(){{
    var prefix=window.location.pathname.replace(/\\\\/g,'/').match(/\\/(A1|A2|B1|B2|C1|C2)\\//) ? '../':'';
    window.addEventListener('scroll',function(){{var b=document.getElementById('backToTop');if(b)b.style.display=window.scrollY>300?'inline-flex':'none';}});
    var fFb='<footer class="site-footer border-top mt-5 py-4"><div class="container text-center"><p class="mb-0">🇩🇪 Deutsch Lernen · <a href="BASE/privacy.html">Datenschutz</a></p></div></footer>';
    fetch(prefix+'footer.html').then(function(r){{return r.ok?r.text():Promise.reject();}}).then(function(html){{html=html.replace(/BASE\\//g,prefix);document.getElementById('footer-placeholder').innerHTML=html;}}).catch(function(){{document.getElementById('footer-placeholder').innerHTML=fFb.replace(/BASE\\//g,prefix);}});
}})();
</script>
<script src="../tts.js?v=7"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>if('serviceWorker' in navigator){{navigator.serviceWorker.register('/deutsch-lernen-goethe-a1-c2/sw.js').then(function(r){{r.update();}}).catch(function(){{}});}}</script>
{CONJUGATION_WS_SCRIPT}
{WORTSCHATZ_SEARCH_SCRIPT}
<!-- Cloudflare Web Analytics --><script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "d435b2572b82459cb083e37f7c734b75"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>'''


def build_conjugations(words):
    """
    Generate conjugations.json — full Reverso-style conjugation tables
    for every verb entry that has a 'conjugation' principal-parts block.
    Verbs without this data are simply skipped (no error) — this lets
    the dataset be populated incrementally across sessions.
    Keyed by the verb's exact 'de' field so the front-end can look it
    up directly from data-de on click.
    """
    result = {}
    skipped = 0
    en_covered = 0
    for w in words:
        pp = w.get('conjugation')
        if not pp:
            continue
        try:
            table = conjugate(pp)
            english_overrides = pp.get('english')
            english_table = build_english_table(w.get('en', ''), english_overrides)
            if english_table:
                table['english'] = english_table
                en_covered += 1
            result[w['de']] = table
        except Exception as e:
            skipped += 1
            print(f"  ⚠️  conjugation error for '{w['de']}': {e}")
    out_path = os.path.join(REPO, 'conjugations.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"  ✅ conjugations.json — {len(result)} verbs, {en_covered} with English"
          f"{f', {skipped} errors' if skipped else ''}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]

    if '--help' in args:
        print(__doc__)
        return

    print(f"Loading {JSON} …")
    with open(JSON, encoding='utf-8') as f:
        words = json.load(f)

    if '--audit' in args:
        issues, counts = audit(words)
        print("\n── Level distribution ──")
        for lv in ['A1','A2','B1','B2','C1','C2']:
            print(f"  {lv}: {counts[lv]}")
        print(f"  TOTAL: {sum(counts.values())}")
        print("\n── Issues ──")
        if issues:
            for issue in issues:
                print(f"  ⚠️  {issue}")
        else:
            print("  ✅ No issues found")
        return

    # --all: rebuild everything (Windows-friendly alternative to && chaining)
    if '--all' in args:
        for level in ['A1','A2','B1','B2','C1','C2']:
            level_words = [w for w in words if w['level'] == level]
            page = build_wortschatz_page(level, level_words)
            out  = os.path.join(REPO, level, '01_Wortschatz.html')
            with open(out, 'w', encoding='utf-8') as f:
                f.write(page)
            print(f"  ✅ {level}/01_Wortschatz.html — {len(level_words)} words")
        build_dictionary(words)
        build_conjugations(words)
        # Inject banner into index.html and all level index pages
        for page_path in (
            [os.path.join(REPO, 'index.html')] +
            [os.path.join(REPO, lv, 'index.html') for lv in ['A1','A2','B1','B2','C1','C2']]
        ):
            if os.path.exists(page_path):
                with open(page_path, encoding='utf-8') as f:
                    pg = f.read()
                pg = inject_install_banner(pg)
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(pg)
                print(f"  ✅ banner → {os.path.relpath(page_path, REPO)}")
        print("\nBuild complete.")
        return

    # Rebuild Wortschatz pages (always, unless --dictionary only)
    if '--dictionary' not in args or '--wortschatz-only' in args or len(args) == 0:
        for level in ['A1','A2','B1','B2','C1','C2']:
            level_words = [w for w in words if w['level'] == level]
            page = build_wortschatz_page(level, level_words)
            out  = os.path.join(REPO, level, '01_Wortschatz.html')
            with open(out, 'w', encoding='utf-8') as f:
                f.write(page)
            print(f"  ✅ {level}/01_Wortschatz.html — {len(level_words)} words")

    # Rebuild dictionary.html
    if '--dictionary' in args:
        build_dictionary(words)
    elif '--wortschatz-only' not in args:
        # Default: just update word count in existing dictionary.html
        dict_path = os.path.join(REPO, 'dictionary.html')
        if os.path.exists(dict_path):
            with open(dict_path, encoding='utf-8') as f:
                content = f.read()
            total = len(re.findall(r'<div class="word-card"', content))
            content = re.sub(r'\d[\d\.]+ exam-relevant words from A1',
                             f'{total} exam-relevant words from A1', content)
            content = re.sub(r'id="wordCount">\d+ words',
                             f'id="wordCount">{total} words', content)
            with open(dict_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ dictionary.html — word count updated to {total}")

    print("\nBuild complete.")


if __name__ == '__main__':
    main()
