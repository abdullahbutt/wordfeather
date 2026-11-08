# -*- coding: utf-8 -*-
"""Cache-busting versions of the shared scripts and data files: ?v=0.00.NN

build.py calls update_asset_versions() on every run. asset-versions.json keeps, per file, a hash of its content and its version. When the content of a file
changed since the last run, the last number of its version goes up by one (0.00.07 -> 0.00.08; 0.00.99 -> 0.01.00); otherwise the version stays. The
version is then written into every reference to the file: src="..." / href="..." and the quoted names in inline scripts (fetch(prefix + 'conjugations.json')).

Every file has its own counter. sw.js is not listed: its CACHE_NAME is a timestamp, stamped by build.py (update_service_worker_cache_name).
The order of ASSETS matters: a file that mentions another one (tts.js loads german-voice.js) comes after it, so that its own change is seen in the same run.
"""
import hashlib
import json
import os
import re

ASSETS = [
    'german-voice.js', 'tts.js', 'recorded-audio.js', 'quiz-bar.js', 'wf-a11y.js', 'wf-lang.js',
    'B1/telc-hoeren-data.js', 'B1/telc-lesen-data.js', 'B1/telc-schreiben-data.js', 'B1/telc-sprachbausteine-data.js', 'B1/telc-sprechen-data.js',
    'conjugations.json', 'person-sentences.json', 'dictionary-index.json', 'grammar_sections.json',
]
MANIFEST = 'asset-versions.json'
SKIP_DIRS = {'.git', 'node_modules', 'vendor', 'fonts', 'audio', 'templates', '__pycache__'}
VERSION = re.compile(r'^\d+\.\d\d\.\d\d$')


def file_hash(path):
    data = open(path, 'rb').read().replace(b'\r\n', b'\n')       # the same hash with LF or CRLF checkouts
    return hashlib.sha1(data).hexdigest()


def bump(v):
    x, y, z = (int(p) for p in v.split('.'))
    z += 1
    if z > 99:
        z, y = 0, y + 1
    if y > 99:
        y, x = 0, x + 1
    return '%d.%02d.%02d' % (x, y, z)


def pattern(names):
    alt = '|'.join(re.escape(os.path.basename(n)) for n in sorted(names, key=len, reverse=True))
    return re.compile(r'(?P<pre>["\'/])(?P<name>%s)(?:\?v=[0-9A-Za-z.]*)?(?P<post>["\'])' % alt)


def rewrite(text, versions, pat):
    return pat.sub(lambda m: '%s%s?v=%s%s' % (m.group('pre'), m.group('name'), versions[m.group('name')], m.group('post')), text)


def html_files(repo):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith('.html'):
                yield os.path.join(root, f)


def read(path):
    return open(path, encoding='utf-8', newline='').read()


def write(path, text):
    open(path, 'w', encoding='utf-8', newline='').write(text)


def update_asset_versions(repo):
    mpath = os.path.join(repo, MANIFEST)
    manifest = json.load(open(mpath, encoding='utf-8')) if os.path.exists(mpath) else {}
    names = [a for a in ASSETS if os.path.exists(os.path.join(repo, a))]
    versions, status = {}, {}
    pages = list(html_files(repo))
    pat = pattern(names)
    first_seen = {}
    if any(n not in manifest for n in names):                   # first run: keep the 0.00.NN a page already carries
        for p in pages:
            for m in re.finditer(r'(?P<name>[\w.-]+\.(?:js|json))\?v=(?P<v>\d+\.\d\d\.\d\d)', read(p)):
                if VERSION.match(m.group('v')) and m.group('v') > first_seen.get(m.group('name'), ''):
                    first_seen[m.group('name')] = m.group('v')
    for n in names:
        base = os.path.basename(n)
        path = os.path.join(repo, n)
        h = file_hash(path)
        cur = manifest.get(n)
        if cur is None:
            manifest[n] = {'hash': h, 'v': first_seen.get(base, '0.00.01')}
            status[n] = 'new'
        elif cur['hash'] != h:
            manifest[n] = {'hash': h, 'v': bump(cur['v'])}
            status[n] = 'bumped'
        else:
            status[n] = 'same'
        versions[base] = manifest[n]['v']
        # a script that names this file (tts.js loads german-voice.js) is rewritten at once, so that its own hash below includes the new version
        for other in names:
            if other.endswith('.js') and other != n and ASSETS.index(other) > ASSETS.index(n):
                op = os.path.join(repo, other)
                t = read(op)
                if base in t:
                    t2 = rewrite(t, versions, pattern([n]))
                    if t2 != t:
                        write(op, t2)
    changed = 0
    for p in pages:
        t = read(p)
        t2 = rewrite(t, versions, pat)
        if t2 != t:
            write(p, t2)
            changed += 1
    write(mpath, json.dumps(manifest, indent=1, sort_keys=True) + '\n')
    bumped = ['%s %s' % (os.path.basename(n), manifest[n]['v']) for n in names if status[n] == 'bumped']
    new = [os.path.basename(n) for n in names if status[n] == 'new']
    print('  ✅ asset versions: %d bumped%s, %d new%s, %d unchanged; %d pages rewritten' % (
        len(bumped), ' (' + ', '.join(bumped) + ')' if bumped else '', len(new), ' (' + ', '.join(new) + ')' if new else '',
        sum(1 for n in names if status[n] == 'same'), changed))
