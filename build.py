#!/usr/bin/env python3
"""
build.py — Deutsch Lernen Hub build pipeline
============================================
Regenerates all six Wortschatz pages and updates dictionary.html
from the single source of truth: words_final.json

Usage:
    python3 build.py                     # rebuild Wortschatz pages + update dictionary counts
    python3 build.py --wortschatz-only   # rebuild Wortschatz pages only
    python3 build.py --audit             # run quality audit and exit
    python3 build.py --help              # show this help

Author: Abdullah Butt
"""

import json, html as htmllib, re, sys, os
from collections import defaultdict, Counter

REPO    = os.path.dirname(os.path.abspath(__file__))
JSON    = os.path.join(REPO, 'words_final.json')

# ── Level metadata ────────────────────────────────────────────────────────────
META = {
    'A1': {'color':'#16a34a','desc':'Grundvokabular für absolute Anfänger — Alltag, Familie, Zahlen, Begrüßungen.'},
    'A2': {'color':'#2563eb','desc':'Erweiterter Alltagswortschatz — Einkaufen, Reisen, Körper, Schule, Technologie.'},
    'B1': {'color':'#7c3aed','desc':'Thematischer Wortschatz für das Goethe-Zertifikat B1 und den Einbürgerungstest.'},
    'B2': {'color':'#ea580c','desc':'Journalistischer und halbformeller Wortschatz für Studium und Beruf.'},
    'C1': {'color':'#dc2626','desc':'Formaler, akademischer und fachsprachlicher Wortschatz.'},
    'C2': {'color':'#0d9488','desc':'Nuancierter, idiomatischer und literarischer Wortschatz auf Muttersprachenniveau.'},
}

# ── Quality audit ─────────────────────────────────────────────────────────────
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
              "hat sich verändert","ich interessiere mich für"]
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

# ── Wortschatz page builder ───────────────────────────────────────────────────
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

    # Jump bar
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

    # Sections
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
            col_html = ''
            if cols:
                pills = ' '.join(
                    f'<span class="badge rounded-pill text-bg-light border me-1" '
                    f'style="font-size:.7rem;font-weight:400">{htmllib.escape(c)}</span>'
                    for c in cols[:3])
                col_html = f'<div class="mt-1">{pills}</div>'
            exe_row = (f'<span class="ex-en d-block text-muted small">{exe}</span>' if exe else '')
            sections += (
                f'<tr>\n'
                f'  <td class="fw-semibold de-word">{de}</td>\n'
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
    <link rel="manifest" href="/deutsch-lernen-goethe-a1-c2/manifest.json">
    <meta name="theme-color" content="#1d4ed8">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Deutsch Lernen">
    <link rel="apple-touch-icon" href="/deutsch-lernen-goethe-a1-c2/icon-192x192.png">
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
    </style>
</head>
<body id="top">
<div id="header-placeholder"></div>
<script>
(function(){{var s=localStorage.getItem('theme')||(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.setAttribute('data-bs-theme',s);var path=window.location.pathname.replace(/\\\\/g,'/');var lm=path.match(/\\/(A1|A2|B1|B2|C1|C2)\\//);var prefix=lm?'../':'';var cl=lm?lm[1]:null;var modules={{A1:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html'],A2:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html'],B1:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html'],B2:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html'],C1:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html'],C2:['01_Wortschatz.html','02_Grammatik.html','03_Saetze.html','04_Lesen.html','05_Hoeren.html','06_Sprechen.html','07_Schreiben.html','08_Musterpruefung.html']}};var labels=['01 Wortschatz','02 Grammatik','03 Sätze','04 Lesen','05 Hören','06 Sprechen','07 Schreiben','08 Musterprüfung'];var hFb='<nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm sticky-top"><div class="container"><a class="navbar-brand" href="BASE/index.html">🇩🇪 Deutsch Lernen</a></div></nav>';function renderHeader(html){{html=html.replace(/BASE\\//g,prefix);document.getElementById('header-placeholder').innerHTML=html;if(cl){{document.querySelectorAll('.dropdown-item[data-level]').forEach(function(el){{if(el.getAttribute('data-level')===cl){{el.classList.add('active');el.setAttribute('aria-current','page');}}}}); var mf=modules[cl];var ul='<ul class="dropdown-menu dropdown-menu-end dropdown-menu-lg-start"><li><a class="dropdown-item" href="README.html">📖 Overview</a></li><li><hr class="dropdown-divider"></li>';mf.forEach(function(f,i){{ul+='<li><a class="dropdown-item" href="'+f+'">'+labels[i]+'</a></li>';}}); ul+='</ul>';var li=document.createElement('li');li.className='nav-item dropdown';li.innerHTML='<a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">'+cl+' Modules</a>'+ul;var nav=document.getElementById('nav-main-links');if(nav)nav.appendChild(li);}}var btn=document.getElementById('themeToggle');if(btn){{function sync(){{var d=document.documentElement.getAttribute('data-bs-theme')==='dark';btn.textContent=d?'☀️ Light':'🌙 Dark';}}sync();btn.addEventListener('click',function(){{var n=document.documentElement.getAttribute('data-bs-theme')==='dark'?'light':'dark';document.documentElement.setAttribute('data-bs-theme',n);localStorage.setItem('theme',n);sync();}});}}}}
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
<!-- Cloudflare Web Analytics --><script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "d435b2572b82459cb083e37f7c734b75"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>'''


# ── Main ──────────────────────────────────────────────────────────────────────
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

    # Rebuild Wortschatz pages
    for level in ['A1','A2','B1','B2','C1','C2']:
        level_words = [w for w in words if w['level'] == level]
        page = build_wortschatz_page(level, level_words)
        out  = os.path.join(REPO, level, '01_Wortschatz.html')
        with open(out, 'w', encoding='utf-8') as f:
            f.write(page)
        print(f"  ✅ {level}/01_Wortschatz.html — {len(level_words)} words")

    if '--wortschatz-only' not in args:
        # Update word count in dictionary.html
        dict_path = os.path.join(REPO, 'dictionary.html')
        if os.path.exists(dict_path):
            import re as _re
            with open(dict_path, encoding='utf-8') as f:
                content = f.read()
            total = len(re.findall(r'<div class="word-card"', content))
            content = _re.sub(r'\d[\d\.]+ exam-relevant words from A1',
                              f'{total} exam-relevant words from A1', content)
            content = _re.sub(r'id="wordCount">\d+ words',
                              f'id="wordCount">{total} words', content)
            with open(dict_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ dictionary.html — word count updated to {total}")

    print("\nBuild complete.")


if __name__ == '__main__':
    main()
