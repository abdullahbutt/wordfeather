#!/usr/bin/env python3
"""
split_dictionary.py - make WordFeather's dictionary indexable by Google.

Googlebot only processes the first 2 MB of an HTML file. dictionary.html is
~5 MB because all 5,243 word cards are rendered into one page. This script
takes that big *build output* and turns it into:

    dictionary.html            small hub page (A-Z grid + search, ~70 KB)
    dictionary-a.html ...      one static page per initial letter (all words
                               crawlable, each page far below 2 MB)
    dictionary-index.json      slim search index used by the hub's search box
    (sitemap.xml)              the dictionary URLs are kept up to date inside your existing sitemap.xml

words_final.json / person-sentences.json / conjugations.json are NOT touched.

It also fixes a grouping bug: nouns were filed under the letter of their
ARTICLE (3,3xx entries ended up under "D" because of der/die/das). Here nouns
are filed under the noun itself: "der Wasserhahn" -> W.

Usage
-----
build.py (see the updated version) imports split_dictionary() and calls it in memory,
so normally you never run this file by hand:   python3 build.py --all
Manual use, on a file that still contains ALL word cards:
    python split_dictionary.py --src full.html --out ./out

Only the standard library is used. Python 3.8+.
"""
import argparse
import datetime
import html
import json
import re
import sys
import unicodedata
from collections import OrderedDict, defaultdict
from pathlib import Path

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
LEVEL_COLORS = {"A1": "#16a34a", "A2": "#2563eb", "B1": "#7c3aed",
                "B2": "#ea580c", "C1": "#dc2626", "C2": "#0d9488"}
HARD_LIMIT = 1_900_000          # fail the build above this (Google cuts at 2 MB)


# --------------------------------------------------------------------------- helpers
def fold(s):
    """lower-case, ä->a, ö->o, ü->u, ß->ss, strip other accents."""
    s = s.replace("ß", "ss").replace("ẞ", "ss")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.casefold()


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", fold(s)).strip("-")


def sort_key_text(de, pos):
    """The text a dictionary would alphabetise by (article / 'sich' removed)."""
    t = de.strip()
    if pos == "noun":
        rest = re.sub(r"^(der|die|das)(/(der|die|das))*\s+", "", t, flags=re.I)
        # only strip the article when a real word follows; entries like "der (2)" ARE the article itself
        if re.match(r"[^\W\d_]|\d", rest):
            t = rest
    t = re.sub(r"^sich\s+", "", t, flags=re.I)
    t = re.sub(r"^[^\w]+", "", t)
    return t


def letter_of(key_text):
    f = fold(key_text)
    ch = f[:1]
    return ch.upper() if "a" <= ch <= "z" else "#"


def letter_slug(letter):
    return "0-9" if letter == "#" else letter.lower()


def meta_sub(s, attr, name, content):
    """Replace content="" of <meta attr="name" ...>."""
    pat = re.compile(r'(<meta\s+%s="%s"\s+content=")[^"]*(")' % (attr, re.escape(name)))
    if not pat.search(s):
        raise SystemExit("template marker not found: <meta %s=%s>" % (attr, name))
    return pat.sub(lambda m: m.group(1) + html.escape(content, quote=True) + m.group(2), s, count=1)


def set_head(s, title, desc, url):
    s = re.sub(r"<title>.*?</title>", lambda m: "<title>%s</title>" % html.escape(title), s, count=1, flags=re.S)
    s = meta_sub(s, "name", "description", desc)
    s = meta_sub(s, "property", "og:title", title)
    s = meta_sub(s, "property", "og:description", desc)
    s = meta_sub(s, "property", "og:url", url)
    s = meta_sub(s, "name", "twitter:title", title)
    s = meta_sub(s, "name", "twitter:description", desc)
    s, n = re.subn(r'(<link rel="canonical" href=")[^"]*(")', lambda m: m.group(1) + url + m.group(2), s, count=1)
    if not n:
        raise SystemExit("template marker not found: canonical link")
    return s


# --------------------------------------------------------------------------- parsing
def parse_source(src_text):
    s = src_text.lstrip("\ufeff").replace("\r\n", "\n")

    wl = '<div id="wordList">\n'
    wl_at = s.find(wl)
    dl_at = s.find('<div class="dict-layout">')
    if wl_at < 0 or dl_at < 0:
        raise SystemExit("Could not find #wordList / .dict-layout - build output changed?")
    region_start = wl_at + len(wl)

    card_re = re.compile(r'<div class="word-card".*?\n</div>\n', re.S)
    cards = list(card_re.finditer(s, region_start))
    if not cards:
        if 'id="hubResults"' in s:
            raise SystemExit("This file is already the split hub page (it has no word cards). "
                             "Feed the script the FULL page (all cards), e.g. build.py's in-memory output "
                             "or templates/dictionary.template.html after build_dictionary().")
        raise SystemExit("No word cards found.")
    region_end = cards[-1].end()

    # everything in the region that is not a card must be the noResults block or letter headers
    leftovers = card_re.sub("", s[region_start:region_end])
    no_results = re.search(r'<div id="noResults".*?\n</div>\n', leftovers, re.S)
    hdr_re = re.compile(r'<div class="letter-header"[^>]*>[^<]*</div>\n')
    header_tpl = hdr_re.search(leftovers)
    rest = hdr_re.sub("", leftovers)
    if no_results:
        rest = rest.replace(no_results.group(0), "")
    if rest.strip():
        raise SystemExit("Unexpected markup between word cards:\n" + rest[:300])
    if not header_tpl:
        raise SystemExit("No letter-header template found.")

    after_cards = s[region_end:]
    if not after_cards.startswith("</div>\n</div>\n"):
        raise SystemExit("Unexpected markup after the last card - build output changed?")

    entries = []
    for m in cards:
        c = m.group(0)
        if c.count("<div") != c.count("</div>"):
            raise SystemExit("Unbalanced card markup near: " + c[:120])
        tag = c[: c.index(">") + 1]
        a = {k: html.unescape(v) for k, v in re.findall(r'data-([a-z]+)="([^"]*)"', tag)}
        disp = re.search(r'<span class="word-de">(.*?)</span>', c, re.S)
        a["disp"] = html.unescape(disp.group(1)).strip() if disp else a["de"]
        a["html"] = c
        a["key"] = sort_key_text(a["disp"], a.get("pos", ""))
        a["letter"] = letter_of(a["key"])
        entries.append(a)

    return {
        "before": s[:dl_at],
        "after": after_cards,
        "no_results": no_results.group(0) if no_results else "",
        "header_tpl": header_tpl.group(0),
        "entries": entries,
        "full": s,
    }


# --------------------------------------------------------------------------- page building
def build_pages(entries, max_bytes, overhead):
    """Group by letter, sort, split a letter into parts if it would exceed max_bytes."""
    by_letter = defaultdict(list)
    for e in entries:
        by_letter[e["letter"]].append(e)
    order = sorted(by_letter, key=lambda L: ("~" if L == "#" else L))
    order = (["#"] if "#" in by_letter else []) + [L for L in order if L != "#"]
    pages = []
    for L in order:
        items = sorted(by_letter[L], key=lambda e: (fold(e["key"]), LEVELS.index(e["level"])))
        parts, cur, size = [], [], overhead
        for e in items:
            b = len(e["html"].encode("utf-8"))
            if cur and size + b > max_bytes:
                parts.append(cur)
                cur, size = [], overhead
            cur.append(e)
            size += b
        parts.append(cur)
        for i, part in enumerate(parts, 1):
            slug = "dictionary-%s%s.html" % (letter_slug(L), "" if i == 1 else "-%d" % i)
            pages.append({"letter": L, "part": i, "parts": len(parts), "file": slug, "items": part})
    return pages


def alpha_nav(pages, current=None):
    firsts = OrderedDict()
    for p in pages:
        firsts.setdefault(p["letter"], p["file"])
    links = []
    for L, f in firsts.items():
        cur = ' aria-current="page"' if current == L else ""
        links.append('<a href="%s"%s>%s</a>' % (f, cur, L))
    return '<nav class="alpha-nav" aria-label="A-Z">\n%s\n</nav>' % "".join(links)


def letter_page(tpl, pages, page, base_url, counts_total):
    n_page = len(page["items"])
    L = page["letter"]
    label = L   # "#" is shown as "#" everywhere, same as in the A-Z nav
    part_txt = "" if page["parts"] == 1 else " (Teil %d/%d)" % (page["part"], page["parts"])
    letter_total = sum(len(p["items"]) for p in pages if p["letter"] == L)
    samples = ", ".join(re.sub(r"[\u2060\u200b]", "", e["disp"].split(",")[0]).strip() for e in page["items"][:3])
    starting = "starting with a number or symbol (#)" if L == "#" else "starting with %s" % label
    title = "German Words %s%s – Deutsch Wörterbuch A1–C2 | WordFeather" % (starting[0].upper() + starting[1:], part_txt)
    desc = ("%d German word%s %s (e.g. %s) with English translations, example sentences and collocations. "
            "Deutsch–Englisch Wörterbuch for Goethe and telc exam preparation, levels A1–C2." %
            (letter_total, "" if letter_total == 1 else "s", starting, samples))
    url = "%s/%s" % (base_url, page["file"])

    s = set_head(tpl["before"], title, desc, url)
    # JSON-LD of the hub describes the whole dataset -> replace with a breadcrumb for letter pages
    crumb = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "WordFeather", "item": base_url + "/"},
            {"@type": "ListItem", "position": 2, "name": "Wörterbuch", "item": base_url + "/dictionary.html"},
            {"@type": "ListItem", "position": 3, "name": "%s%s" % (label, part_txt), "item": url}]},
        ensure_ascii=False)
    s, n = re.subn(r'<script type="application/ld\+json">.*?</script>',
                   lambda m: '<script type="application/ld+json">%s</script>' % crumb, s, count=1, flags=re.S)

    # visible headline + counts
    s = s.replace("📖 Wörterbuch / Dictionary</h1>",
                  "📖 German Words %s%s – Deutsch Wörterbuch</h1>" % (starting[0].upper() + starting[1:], part_txt), 1)
    intro = ('<p class="mb-3">%d German word%s %s, each with its English translation, an example sentence with '
             'translation and common collocations – graded from A1 to C2 for Goethe and telc exam preparation. '
             'Deutsche Wörter mit englischer Übersetzung und Beispielsätzen. '
             '<a href="dictionary.html">Back to the full dictionary</a>.</p>\n' % (letter_total, "" if letter_total == 1 else "s", starting))
    s = s.replace('<p class="info-line mb-3">', intro + '<p class="info-line mb-3">', 1)
    s, k = re.subn(r"\d+ exam-relevant words from A1–C2",
                   "%d word%s beginning with %s · A1–C2" % (letter_total, "" if letter_total == 1 else "s", label), s, count=1)
    s = re.sub(r'(<span class="stats" id="wordCount">)[^<]*(</span>)',
               lambda m: "%s%d words%s" % (m.group(1), n_page, m.group(2)), s, count=1)
    s = s.replace('<li class="breadcrumb-item active" aria-current="page">Wörterbuch / Dictionary</li>',
                  '<li class="breadcrumb-item"><a href="dictionary.html">Wörterbuch / Dictionary</a></li>'
                  '<li class="breadcrumb-item active" aria-current="page">%s%s</li>' % (label, part_txt), 1)

    extra_css = ("<style>.word-card{scroll-margin-top:7rem}.word-card:target{outline:2px solid #1d4ed8;"
                 "outline-offset:2px;border-radius:.5rem}.letter-pager{display:flex;justify-content:space-between;"
                 "gap:1rem;flex-wrap:wrap;padding:1.25rem 0 0;font-weight:600}"
                 ".search-scope{font-size:.8rem;color:var(--muted,#64748b)}</style>\n")
    s = s.replace("</head>", extra_css + "</head>", 1)

    # search box is now per-letter: say so, link to the global search on the hub
    scope = ('<p class="search-scope mb-2">Search and filters apply to this page (%s). '
             '<a href="dictionary.html">Search all %d words →</a></p>\n' % (label, counts_total))
    s = s.replace('<div class="search-wrap mb-2">', scope + '<div class="search-wrap mb-2">', 1)

    # cards
    hdr = tpl["header_tpl"]
    hdr = re.sub(r'id="letter-[^"]*"', 'id="letter-%s"' % letter_slug(L), hdr, count=1)
    hdr = re.sub(r">[^<]*</div>", ">%s</div>" % html.escape(label + part_txt), hdr, count=1)

    used = set()
    body = []
    for e in page["items"]:
        slug = "%s-%s" % (slugify(e["disp"].split(",")[0]) or "w", e["level"].lower())
        base, i = slug, 2
        while slug in used:
            slug, i = "%s-%d" % (base, i), i + 1
        used.add(slug)
        e["slug"] = slug
        body.append(e["html"].replace('<div class="word-card"', '<div class="word-card" id="%s"' % slug, 1))

    idx = pages.index(page)
    prev_p = pages[idx - 1] if idx > 0 else None
    next_p = pages[idx + 1] if idx + 1 < len(pages) else None

    def plabel(p):
        l = p["letter"]
        return l + ("" if p["parts"] == 1 else " (%d)" % p["part"])
    pager = '<nav class="letter-pager" aria-label="Seiten">%s<a href="dictionary.html">↑ A–Z</a>%s</nav>\n' % (
        ('<a href="%s" rel="prev">← %s</a>' % (prev_p["file"], plabel(prev_p))) if prev_p else "<span></span>",
        ('<a href="%s" rel="next">%s →</a>' % (next_p["file"], plabel(next_p))) if next_p else "<span></span>")

    middle = ('<div class="dict-layout">\n%s\n<div id="wordList">\n%s%s%s%s' %
              (alpha_nav(pages, L), tpl["no_results"], hdr, "".join(body), pager))
    return s + middle + tpl["after"]


# --------------------------------------------------------------------------- hub
HUB_CSS = """<style>
.letter-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:.6rem;margin:.25rem 0 1.5rem}
.letter-tile{display:flex;flex-direction:column;align-items:center;gap:.1rem;padding:.7rem .4rem;border:1.5px solid var(--word-border,#e5e7eb);
 border-radius:.75rem;text-decoration:none;background:var(--card-bg,#fff);color:inherit}
.letter-tile:hover{border-color:#1d4ed8;box-shadow:var(--card-shadow,0 .25rem .75rem rgba(0,0,0,.08))}
.letter-tile strong{font-size:1.5rem;line-height:1.1;color:#1d4ed8}
[data-bs-theme="dark"] .letter-tile strong{color:#818cf8}
.letter-tile span{font-size:.75rem;color:var(--muted,#64748b)}
.hub-result{display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap;padding:.55rem .25rem;border-bottom:1px solid var(--word-border,#e5e7eb);text-decoration:none;color:inherit}
.hub-result:hover{background:rgba(29,78,216,.06)}
.hub-result .hub-de{font-weight:700;font-size:1.05rem}
.hub-result .hub-en{color:var(--muted,#64748b)}
.hub-result .hub-ex{flex-basis:100%;font-size:.85rem;color:var(--muted,#64748b)}
.hub-msg{padding:1.5rem .25rem;color:var(--muted,#64748b)}
</style>
"""

HUB_JS = r"""        // ---- hub search (uses dictionary-index.json, loaded on first use) ----
        var LEVEL_COLORS = __COLORS__;
        var LETTER_FILES = __FILES__;
        var m = location.hash.match(/^#letter-(.+)$/);
        if (m && LETTER_FILES[decodeURIComponent(m[1]).toUpperCase()]) {
            location.replace(LETTER_FILES[decodeURIComponent(m[1]).toUpperCase()]);
            return;
        }
        var input = document.getElementById('searchInput');
        var wordCount = document.getElementById('wordCount');
        var grid = document.getElementById('letterGrid');
        var resultsBox = document.getElementById('hubResults');
        var noResults = document.getElementById('noResults');
        var activeLevel = 'ALL', activePOS = 'ALL', activeCategory = 'ALL';
        var OTHER_POS = ['proverb', 'preposition', 'conjunction', 'pronoun', 'determiner'];
        var TOTAL = __TOTAL__;
        var PAGE = 150, shown = PAGE, lastHits = [];
        var index = null, loading = null;

        function foldGerman(s) {
            return s.replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss');
        }
        function loadIndex() {
            if (index) return Promise.resolve(index);
            if (!loading) {
                loading = fetch(prefix + 'dictionary-index.json')
                    .then(function (r) { if (!r.ok) throw new Error('index'); return r.json(); })
                    .then(function (j) {
                        j.w.forEach(function (r) {
                            r.f = [foldGerman(r[0].toLowerCase()), foldGerman(r[1].toLowerCase()), foldGerman(r[6].toLowerCase())];
                        });
                        index = j;
                        return j;
                    });
            }
            return loading;
        }
        function isFiltering() {
            return input.value.trim() !== '' || activeLevel !== 'ALL' || activePOS !== 'ALL' || activeCategory !== 'ALL';
        }
        function search() {
            if (!isFiltering()) {
                grid.style.display = ''; resultsBox.style.display = 'none'; noResults.style.display = 'none';
                wordCount.textContent = TOTAL + ' words';
                return;
            }
            resultsBox.style.display = ''; grid.style.display = 'none';
            resultsBox.innerHTML = '<p class="hub-msg">⏳ Laden… / Loading…</p>';
            loadIndex().then(function (j) {
                var q = foldGerman(input.value.toLowerCase().trim());
                var cat = activeCategory === 'ALL' ? null : activeCategory;
                lastHits = j.w.filter(function (r) {
                    if (activeLevel !== 'ALL' && r[2] !== activeLevel) return false;
                    if (activePOS !== 'ALL' && !(r[3] === activePOS ||
                        (activePOS === 'irregular' && r[4] === 1) ||
                        (activePOS === 'other' && OTHER_POS.indexOf(r[3]) > -1))) return false;
                    if (cat && j.c[r[5]] !== cat) return false;
                    return !q || r.f[0].indexOf(q) > -1 || r.f[1].indexOf(q) > -1 || r.f[2].indexOf(q) > -1;
                });
                shown = PAGE;
                render(j);
            }).catch(function () {
                resultsBox.innerHTML = '<p class="hub-msg">Suche momentan nicht verfügbar – bitte einen Buchstaben oben wählen. / Search unavailable – please pick a letter.</p>';
            });
        }
        function render(j) {
            var n = lastHits.length;
            wordCount.textContent = n + ' word' + (n !== 1 ? 's' : '');
            resultsBox.innerHTML = '';
            noResults.style.display = n === 0 ? 'block' : 'none';
            lastHits.slice(0, shown).forEach(function (r) {
                var a = document.createElement('a');
                a.className = 'hub-result';
                a.href = j.p[r[7]] + '#' + r[8];
                var de = document.createElement('span'); de.className = 'hub-de'; de.textContent = r[0];
                var lv = document.createElement('span'); lv.className = 'badge rounded-pill'; lv.textContent = r[2];
                lv.style.background = LEVEL_COLORS[r[2]] || '#64748b';
                var en = document.createElement('span'); en.className = 'hub-en'; en.textContent = r[1];
                var ex = document.createElement('span'); ex.className = 'hub-ex'; ex.textContent = r[6];
                a.appendChild(de); a.appendChild(lv); a.appendChild(en); a.appendChild(ex);
                resultsBox.appendChild(a);
            });
            if (n > shown) {
                var more = document.createElement('button');
                more.type = 'button'; more.className = 'btn btn-outline-primary btn-sm my-3';
                more.textContent = 'Mehr anzeigen / Show more (' + (n - shown) + ')';
                more.addEventListener('click', function () { shown += PAGE; render(j); });
                resultsBox.appendChild(more);
            }
        }
        var timer = null;
        input.addEventListener('focus', function () { loadIndex().catch(function () {}); });
        input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(search, 120); });
        document.querySelectorAll('.level-filter button').forEach(function (btn) {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.level-filter button').forEach(function (b) { b.classList.remove('active'); b.setAttribute('aria-pressed', 'false'); });
                btn.classList.add('active'); btn.setAttribute('aria-pressed', 'true');
                activeLevel = btn.getAttribute('data-level'); search();
            });
        });
        document.querySelectorAll('.pos-filter button').forEach(function (btn) {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.pos-filter button').forEach(function (b) { b.classList.remove('active'); b.setAttribute('aria-pressed', 'false'); });
                btn.classList.add('active'); btn.setAttribute('aria-pressed', 'true');
                activePOS = btn.getAttribute('data-pos'); search();
            });
        });
        var categorySelect = document.getElementById('categoryFilter');
        var categoryEnLabel = document.getElementById('categoryEnLabel');
__CATEGORY_EN__
        function updateCategoryEnLabel() {
            if (!categoryEnLabel || !categorySelect) return;
            var val = categorySelect.value;
            if (val === 'ALL' || !CATEGORY_EN[val]) { categoryEnLabel.style.display = 'none'; categoryEnLabel.textContent = ''; }
            else { categoryEnLabel.textContent = '(' + CATEGORY_EN[val] + ')'; categoryEnLabel.style.display = ''; }
        }
        if (categorySelect) {
            categorySelect.addEventListener('change', function () {
                activeCategory = categorySelect.value; updateCategoryEnLabel(); search();
            });
        }

"""


def hub_page(tpl, pages, base_url, total, counts_by_letter, counts_by_level):
    s = tpl["before"]
    title = "German Dictionary A1–C2: {:,} Words – Deutsch Wörterbuch | WordFeather".format(total)
    desc = ("Free German–English dictionary with {:,} exam-relevant words, graded A1 to C2, with translations, "
            "example sentences and collocations for Goethe and telc. Deutsch–Englisch Wörterbuch: "
            "durchsuchen oder nach Buchstaben blättern.".format(total))
    s = set_head(s, title, desc, base_url + "/dictionary.html")
    s = s.replace("📖 Wörterbuch / Dictionary</h1>", "📖 German Dictionary / Deutsch–Englisch Wörterbuch</h1>", 1)
    levels = " · ".join('<a href="%s/">%s</a>' % (l, l) for l in LEVELS)
    intro = ('<p class="mb-3">A free German–English dictionary with {:,} words from A1 to C2. Every entry has an '
             'English translation, an example sentence with translation, collocations and audio pronunciation, '
             'and is chosen for Goethe and telc exam preparation. Search all words below or browse A–Z. '
             'Ein kostenloses Deutsch–Englisch Wörterbuch mit Beispielsätzen für die Prüfungsvorbereitung. '
             'Vocabulary by level: {}.</p>\n'.format(total, levels))
    s = s.replace('<p class="info-line mb-3">', intro + '<p class="info-line mb-3">', 1)
    s = s.replace("</head>", HUB_CSS + "</head>", 1)

    # letter grid (static, crawlable, works without JS)
    firsts = OrderedDict()
    for p in pages:
        firsts.setdefault(p["letter"], p["file"])
    tiles = "".join(
        '<a class="letter-tile" href="%s"><strong>%s</strong><span>%d Wörter</span></a>' %
        (f, L, counts_by_letter[L]) for L, f in firsts.items())
    lv = " · ".join("%s: %d" % (l, counts_by_level.get(l, 0)) for l in LEVELS)
    grid = ('<div id="letterGrid">\n<h2 class="h5 mb-2">Nach Buchstaben blättern / Browse A–Z</h2>\n'
            '<div class="letter-grid">%s</div>\n<p class="info-line">%s</p>\n</div>\n'
            '<div id="hubResults" style="display:none"></div>\n' % (tiles, lv))
    middle = ('<div class="dict-layout">\n%s\n<div id="wordList">\n%s%s' %
              (alpha_nav(pages), tpl["no_results"], grid))
    tail = tpl["after"][len("</div>\n</div>\n"):]     # the original wordList + dict-layout closers are re-added below
    s = s + middle + "</div>\n</div>\n" + tail

    # scripts: drop the per-card scripts (TTS, person drill, conjugations) - the hub has no cards
    def drop(s, marker):
        pat = re.compile(r"<script>(?:(?!</script>).)*?%s.*?</script>\n?" % re.escape(marker), re.S)
        s2, n = pat.subn("", s, count=1)
        if not n:
            print("  warn: hub script marker not found: %s" % marker, file=sys.stderr)
        return s2
    for marker in ("// TTS\n", "Person-sentence drill", "Full verb conjugation table"):
        s = drop(s, marker)

    # replace the card-based "Search & Filter" section of the main script with the index-based one
    a = s.find("        // Search & Filter")
    b = s.find("        // Remove the loading overlay only once")
    if a < 0 or b < 0:
        raise SystemExit("main script markers not found - build output changed?")
    cat = re.search(r"        var CATEGORY_EN = \{.*?\n        \};", tpl["full"], re.S)
    if not cat:
        raise SystemExit("CATEGORY_EN block not found")
    files = {("#" if L == "#" else L): f for L, f in firsts.items()}
    js = (HUB_JS.replace("__COLORS__", json.dumps(LEVEL_COLORS))
                .replace("__FILES__", json.dumps(files))
                .replace("__TOTAL__", str(total))
                .replace("__CATEGORY_EN__", cat.group(0)))
    s = s[:a] + js + s[b:]
    return s


def write_if_changed(path, data):
    """Write bytes only if different; returns True when the file changed (keeps mtimes/git diffs quiet)."""
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def update_sitemap(path, base, urls, changed, verbose=True):
    """Keep the dictionary URLs inside the ONE existing sitemap.xml.

    - the existing dictionary.html entry is kept (its lastmod is bumped only if the page changed)
    - one <url> per dictionary-<letter>.html is (re)generated right after it
    - lastmod = today for pages whose content changed, otherwise the previous lastmod is kept
    Everything else in sitemap.xml is left exactly as it was.
    """
    if not path.exists():
        print("  warn: %s not found - sitemap not updated (add these URLs by hand): %s" % (path, ", ".join(urls)))
        return
    raw = path.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    txt = raw.replace("\r\n", "\n")
    today = datetime.date.today().isoformat()

    entry_re = re.compile(r"[ \t]*<url>\s*<loc>([^<]*)</loc>.*?</url>\n?", re.S)
    old_lastmod = {}
    for m in entry_re.finditer(txt):
        lm = re.search(r"<lastmod>([^<]*)</lastmod>", m.group(0))
        old_lastmod[m.group(1).strip()] = lm.group(1) if lm else None

    # drop old dictionary-<letter> entries
    letter_loc = re.compile(re.escape(base) + r"/dictionary-(0-9|[a-z])(-\d+)?\.html$")
    txt = entry_re.sub(lambda m: "" if letter_loc.match(m.group(1).strip()) else m.group(0), txt)

    def lastmod_for(u):
        loc = "%s/%s" % (base, u)
        return today if (u in changed or not old_lastmod.get(loc)) else old_lastmod[loc]

    hub_loc = "%s/dictionary.html" % base
    hub_m = next((m for m in entry_re.finditer(txt) if m.group(1).strip() == hub_loc), None)
    new_entries = "".join(
        "  <url>\n    <loc>%s/%s</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>monthly</changefreq>\n"
        "    <priority>0.7</priority>\n  </url>\n" % (base, u, lastmod_for(u)) for u in urls[1:])
    if hub_m:
        block = re.sub(r"<lastmod>[^<]*</lastmod>", "<lastmod>%s</lastmod>" % lastmod_for("dictionary.html"),
                       hub_m.group(0), count=1)
        txt = txt[:hub_m.start()] + block + new_entries + txt[hub_m.end():]
    else:
        txt = txt.replace("</urlset>", new_entries + "</urlset>", 1)
    out = txt.replace("\n", nl)
    if out != raw:
        path.write_bytes(out.encode("utf-8"))
    if verbose:
        print("  ✅ sitemap.xml — %d dictionary URLs (single sitemap, no separate sitemap-dictionary.xml)" % len(urls))


# --------------------------------------------------------------------------- main
def split_dictionary(src_text, out_dir=".", base="https://wordfeather.com", max_bytes=1_200_000, verbose=True):
    """Split the full dictionary HTML (a string) into hub + letter pages.

    Importable: build.py calls this straight after it has generated the full page in memory.
    """
    base = base.rstrip("/")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    tpl = parse_source(src_text)
    entries = tpl["entries"]
    total = len(entries)
    overhead = len(tpl["before"].encode("utf-8")) + len(tpl["after"].encode("utf-8")) + 12_000
    pages = build_pages(entries, max_bytes, overhead)

    counts_by_letter = defaultdict(int)
    counts_by_level = defaultdict(int)
    for e in entries:
        counts_by_letter[e["letter"]] += 1
        counts_by_level[e["level"]] += 1

    # remove stale letter pages from a previous run (e.g. a part that no longer exists)
    keep = {p["file"] for p in pages}
    for old in out.glob("dictionary-*.html"):
        if re.fullmatch(r"dictionary-(0-9|[a-z])(-\d+)?\.html", old.name) and old.name not in keep:
            old.unlink()

    written, worst, changed = [], 0, set()
    for p in pages:
        text = letter_page(tpl, pages, p, base, total)
        b = text.encode("utf-8")
        if len(b) > HARD_LIMIT:
            raise SystemExit("%s is %d bytes - over the safe limit; lower max_bytes" % (p["file"], len(b)))
        if write_if_changed(out / p["file"], b):
            changed.add(p["file"])
        written.append((p["file"], len(p["items"]), len(b)))
        worst = max(worst, len(b))

    hub = hub_page(tpl, pages, base, total, counts_by_letter, counts_by_level).encode("utf-8")
    if write_if_changed(out / "dictionary.html", hub):
        changed.add("dictionary.html")
    written.insert(0, ("dictionary.html", 0, len(hub)))

    # slim search index (built from the cards, so it can never drift from the pages)
    page_names = [p["file"] for p in pages]
    cats = sorted({e.get("category", "") for e in entries})
    rows = []
    for p in pages:
        pi = page_names.index(p["file"])
        for e in p["items"]:
            rows.append([e["disp"], e.get("en", ""), e["level"], e.get("pos", ""),
                         1 if e.get("irregular") == "true" else 0, cats.index(e.get("category", "")),
                         e.get("ex", ""), pi, e["slug"]])
    (out / "dictionary-index.json").write_text(
        json.dumps({"p": page_names, "c": cats, "w": rows}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")

    update_sitemap(out / "sitemap.xml", base, ["dictionary.html"] + page_names, changed, verbose)

    idx_b = (out / "dictionary-index.json").stat().st_size
    if verbose:
        print("  ✅ dictionary split: %d words -> hub (%s bytes) + %d letter pages; largest page %s bytes "
              "(Google limit 2,097,152); search index %s bytes" %
              (total, format(len(hub), ","), len(pages), format(worst, ","), format(idx_b, ",")))
    return {"words": total, "pages": len(pages), "largest": worst, "files": written}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="full (5 MB) dictionary HTML that still contains all word cards")
    ap.add_argument("--out", default=".", help="site root to write into (default: .)")
    ap.add_argument("--base", default="https://wordfeather.com", help="site origin, no trailing slash")
    ap.add_argument("--max-bytes", type=int, default=1_200_000,
                    help="target max size of one letter page; bigger letters are split into parts")
    args = ap.parse_args()
    res = split_dictionary(Path(args.src).read_text(encoding="utf-8"), args.out, args.base, args.max_bytes, verbose=False)
    print("%-26s %6s %12s" % ("file", "words", "bytes"))
    for name, n, b in res["files"]:
        print("%-26s %6s %12s" % (name, n or "", format(b, ",")))
    print("\n%d words on %d letter pages. Largest page: %s bytes." % (res["words"], res["pages"], format(res["largest"], ",")))


if __name__ == "__main__":
    main()
