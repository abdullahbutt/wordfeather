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
from conjugator import conjugate

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
INSTALL_BANNER = (
    '\n    <!-- App Install Banner -->\n'
    '    <div style="background:linear-gradient(135deg,#1d4ed8 0%,#7c3aed 100%)'
    ';color:#fff;padding:1rem 0;">\n'
    '        <div class="container">\n'
    '            <div class="d-flex align-items-center gap-2 mb-2 flex-wrap">\n'
    '                <span style="font-size:1.6rem">📱</span>\n'
    '                <div>\n'
    '                    <div style="font-weight:700;font-size:1rem;line-height:1.2">'
    'Install as a free app — no App Store needed</div>\n'
    '                    <div style="font-size:.82rem;opacity:.9;margin-top:.1rem">'
    'Works offline · Installs in seconds · All devices</div>\n'
    '                </div>\n'
    '            </div>\n'
    '            <div class="row g-2">\n'
    '                <div class="col-6 col-md-3">\n'
    '                    <div style="background:rgba(255,255,255,.15);border-radius:.6rem'
    ';padding:.5rem .7rem;font-size:.78rem;line-height:1.4;height:100%">\n'
    '                        <div style="font-weight:700;margin-bottom:.15rem">🍎 iPhone/iPad</div>\n'
    '                        <div>Safari → <strong>Share ⬆</strong> → Add to Home Screen</div>\n'
    '                    </div>\n'
    '                </div>\n'
    '                <div class="col-6 col-md-3">\n'
    '                    <div style="background:rgba(255,255,255,.15);border-radius:.6rem'
    ';padding:.5rem .7rem;font-size:.78rem;line-height:1.4;height:100%">\n'
    '                        <div style="font-weight:700;margin-bottom:.15rem">🤖 Android</div>\n'
    '                        <div>Chrome → <strong>⋮ Menu</strong> → Add to Home Screen</div>\n'
    '                    </div>\n'
    '                </div>\n'
    '                <div class="col-6 col-md-3">\n'
    '                    <div style="background:rgba(255,255,255,.15);border-radius:.6rem'
    ';padding:.5rem .7rem;font-size:.78rem;line-height:1.4;height:100%">\n'
    '                        <div style="font-weight:700;margin-bottom:.15rem">🖥️ macOS</div>\n'
    '                        <div>Safari → <strong>Share</strong> → Add to Dock</div>\n'
    '                    </div>\n'
    '                </div>\n'
    '                <div class="col-6 col-md-3">\n'
    '                    <div style="background:rgba(255,255,255,.15);border-radius:.6rem'
    ';padding:.5rem .7rem;font-size:.78rem;line-height:1.4;height:100%">\n'
    '                        <div style="font-weight:700;margin-bottom:.15rem">🪟 Windows</div>\n'
    '                        <div>Edge → <strong>Apps</strong> → Install this site</div>\n'
    '                    </div>\n'
    '                </div>\n'
    '            </div>\n'
    '        </div>\n'
    '    </div>\n'
    '    <!-- End App Install Banner -->\n'
)

def inject_install_banner(content):
    """Insert the app install banner before <main>. Idempotent."""
    # Remove any existing banner — handles both old and new comment styles
    content = re.sub(
        r'\s*<!-- [─\-]*\s*App Install Banner.*?End App Install Banner\s*[─\-]*\s*-->\s*',
        '\n', content, flags=re.DOTALL
    )
    main_pos = content.find('<main')
    if main_pos == -1:
        return content
    return content[:main_pos] + INSTALL_BANNER + content[main_pos:]


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

    function renderTenseBlock(tenseKey, forms) {
        var rows = '';
        for (var i = 0; i < 6; i++) {
            rows += '<div class="conj-person-ws">' + PERSONS[i] + '</div>' +
                    '<div>' + forms[i] + '</div>';
        }
        return '<div style="margin-bottom:.4rem">' +
               '<div class="conj-tense-label-ws">' + (TENSE_LABELS[tenseKey] || tenseKey) + '</div>' +
               '<div class="conj-grid-ws">' + rows + '</div></div>';
    }

    function renderTable(table) {
        var html = '<div class="conj-table-wrap-ws">';
        html += '<div class="conj-mood-title-ws">Weitere Formen</div><div class="conj-imperativ-row-ws">' +
                '<span>Infinitiv: ' + table.infinitiv + '</span>' +
                '<span>Partizip Präsens: ' + table.partizip1 + '</span>' +
                '<span>Partizip Perfekt: ' + table.partizip2 + '</span>' +
                '<span>zu + Infinitiv: ' + table.zu_infinitiv + '</span></div>';

        html += '<div class="conj-mood-title-ws">Indikativ</div>';
        ['praesens','praeteritum','perfekt','plusquamperfekt','futur1','futur2'].forEach(function(t) {
            if (table.indikativ && table.indikativ[t]) html += renderTenseBlock(t, table.indikativ[t]);
        });
        html += '<div class="conj-mood-title-ws">Konjunktiv I</div>';
        ['praesens','perfekt','futur1','futur2'].forEach(function(t) {
            if (table.konjunktiv1 && table.konjunktiv1[t]) html += renderTenseBlock(t, table.konjunktiv1[t]);
        });
        html += '<div class="conj-mood-title-ws">Konjunktiv II</div>';
        ['praeteritum','plusquamperfekt','futur1','futur2'].forEach(function(t) {
            if (table.konjunktiv2 && table.konjunktiv2[t]) html += renderTenseBlock(t, table.konjunktiv2[t]);
        });
        if (table.imperativ) {
            html += '<div class="conj-mood-title-ws">Imperativ</div><div class="conj-imperativ-row-ws">';
            ['du','ihr','Sie','wir'].forEach(function(p) {
                if (table.imperativ[p]) html += '<span>' + p + ': ' + table.imperativ[p] + '</span>';
            });
            html += '</div>';
        }
        if (table.passiv) {
            html += '<div class="conj-mood-title-ws">Passiv</div>';
            ['praesens','praeteritum','perfekt','plusquamperfekt','futur1'].forEach(function(t) {
                if (table.passiv[t]) html += renderTenseBlock(t, table.passiv[t]);
            });
        }
        html += '</div>';
        return html;
    }

    document.querySelectorAll('.conj-toggle-ws').forEach(function(btn) {
        var de = btn.getAttribute('data-de-lower');
        var wrap = null;
        var cell = btn.closest('td');
        btn.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            if (wrap) { wrap.remove(); wrap = null; btn.textContent = '📖 Konjugation'; return; }
            loadConjugations().then(function(data) {
                var table = data[de];
                if (!table) {
                    btn.textContent = '(noch nicht verfügbar)';
                    btn.disabled = true;
                    return;
                }
                var div = document.createElement('div');
                div.innerHTML = renderTable(table);
                wrap = div.firstChild;
                cell.appendChild(wrap);
                btn.textContent = '✕ Ausblenden';
            });
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

    # Inject app install banner
    content_new = inject_install_banner(content_new)
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

    # Inject / refresh POS filter buttons if not already present
    if 'class="pos-filter"' not in content_new:
        POS_BUTTONS = '''<div class="pos-filter mt-2">
                        <button data-pos="ALL" class="active">All types</button>
                        <button data-pos="noun">🔵 Nouns</button>
                        <button data-pos="verb">🟢 Verbs</button>
                        <button data-pos="adjective">🟠 Adjectives</button>
                        <button data-pos="adverb">🟣 Adverbs</button>
                        <button data-pos="phrase">⬜ Phrases</button>
                    </div>'''
        INSERT_AFTER = 'data-level="C2">C2</button>\n                    </div>'
        content_new = content_new.replace(
            INSERT_AFTER,
            INSERT_AFTER + '\n                    ' + POS_BUTTONS,
            1
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
            sections += (
                f'<tr data-pos="{pos}">\n'
                f'  <td class="fw-semibold de-word">{de}{conj_btn}</td>\n'
                f'  <td class="text-muted">{en}</td>\n'
                f'  <td><span class="ex-de d-block">{exd}</span>{exe_row}{col_html}</td>\n'
                f'</tr>\n'
            )
        sections += '</tbody>\n</table>\n</div>\n'

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
        .conj-table-wrap-ws{{margin-top:.6rem;font-size:.78rem;border-top:1px dashed #bbf7d0;padding-top:.5rem;}}
        .conj-mood-title-ws{{font-weight:700;color:#0d7d4d;margin:.5rem 0 .2rem;font-size:.8rem;}}
        [data-bs-theme="dark"] .conj-mood-title-ws{{color:#4ade80;}}
        .conj-tense-label-ws{{font-weight:600;color:var(--muted-text);font-size:.72rem;text-transform:uppercase;letter-spacing:.02em;margin-bottom:.15rem;margin-top:.3rem;}}
        .conj-grid-ws{{display:grid;grid-template-columns:5.5rem 1fr;gap:.1rem .5rem;font-size:.78rem;}}
        .conj-person-ws{{color:var(--muted-text);}}
        .conj-imperativ-row-ws{{display:flex;gap:.5rem;flex-wrap:wrap;}}
        .conj-imperativ-row-ws span{{background:var(--table-stripe);border-radius:.3rem;padding:.1rem .5rem;}}
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
            <span class="badge bg-secondary">{count} Wörter</span>
        </div>
    </div>
    <p class="text-muted mb-1">{htmllib.escape(desc)}</p>
    <p class="text-muted small mb-4">
        Klicke auf <strong>🔊</strong> um Aussprache zu hören.
        Jeder Eintrag enthält Beispielsatz und englische Übersetzung.
    </p>

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
<script>if('serviceWorker' in navigator){{navigator.serviceWorker.register('/deutsch-lernen-goethe-a1-c2/sw.js').then(function(r){{r.update();}}).catch(function(){{}});}}</script>
{CONJUGATION_WS_SCRIPT}
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
    for w in words:
        pp = w.get('conjugation')
        if not pp:
            continue
        try:
            table = conjugate(pp)
            result[w['de']] = table
        except Exception as e:
            skipped += 1
            print(f"  ⚠️  conjugation error for '{w['de']}': {e}")
    out_path = os.path.join(REPO, 'conjugations.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"  ✅ conjugations.json — {len(result)} verbs"
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
