"""
english_conjugator.py — English conjugation engine for the bilingual
verb display feature.
======================================================================
Generates Present, Past, and Perfect forms for the six German persons
(ich/du/er-sie-es/wir/ihr/Sie -> I/you/he-she-it/we/you/they) from the
existing 'en' field already in words_final.json, so no new data entry
is needed for the ~200+ verbs whose English translation is regular.

English present tense has only 2 distinct forms (base, and base+s for
he/she/it). English past tense is IDENTICAL across all six persons.
This means the entire table can be rule-derived for regular verbs —
only genuinely irregular English verbs (go/went/gone, buy/bought/
bought) need an explicit override, verified individually.

PRINCIPAL PARTS SCHEMA (optional 'english' key on conjugation data):
    {
        "irregular_past": "went",        # overrides regular -ed rule
        "irregular_participle": "gone",  # overrides regular -ed rule
        "no_conjugation": false           # true for modals with no
                                           # standard present/past
                                           # (handled via full override)
        "praesens_voll": [...6 forms...]  # full override, for modals
        "praeteritum_voll": [...6 forms...]
        "perfekt_voll": [...6 forms...]
    }
Only needed when the regular rules below would be wrong.
"""

import re

PERSONS_EN = ['I', 'you', 'he/she/it', 'we', 'you', 'they']


def extract_base_verb(en_field):
    """Pull the primary 'to X' infinitive out of the en field.
    Only checks the FIRST comma-separated segment — if it doesn't
    start with 'to ', this is very likely a modal-style gloss
    ('can, to be able to', 'must, to have to') where blindly grabbing
    a later 'to X' segment produces garbage (e.g. conjugating
    'be able to' as a regular verb gives 'be able toes'). Returning
    None here correctly signals 'needs an explicit override' rather
    than a false success. Multi-translation regular verbs still work
    fine since their first segment already starts with 'to '
    ('to drive, to go' -> 'drive')."""
    if not en_field:
        return None
    first = en_field.split(',')[0].strip()
    if first.lower().startswith('to '):
        return first[3:].strip()
    return None


def _needs_es(base):
    """Verbs needing -es instead of -s for he/she/it: ends in
    s/x/z/ch/sh, or consonant+o (do->does, go->goes)."""
    if re.search(r'(s|x|z|ch|sh)$', base):
        return True
    if re.search(r'[^aeiou]o$', base):
        return True
    return False


def _present_he_form(base):
    """he/she/it present form: base + s, with spelling rules."""
    if _needs_es(base):
        return base + 'es'
    if re.search(r'[^aeiou]y$', base):
        return base[:-1] + 'ies'
    return base + 's'


def _regular_past(base):
    """Regular English past tense (also used for the past participle,
    since regular verbs' past and past participle are identical).
    British spelling convention: doubles a final single consonant
    after a single stressed vowel in one-syllable bases (stop->stopped,
    travel->travelled — the British doubling rule is broader than
    American for -l specifically)."""
    if base.endswith('e'):
        return base + 'd'
    if re.search(r'[^aeiou]y$', base):
        return base[:-1] + 'ied'
    # British doubling: single vowel + single consonant, or ends in -l
    # after any vowel (travel->travelled is British-specific)
    if re.search(r'[aeiou]l$', base):
        return base + 'led'
    if re.search(r'[^aeiou][aeiou][^aeiouwxy]$', base) and len(base) <= 6:
        return base + base[-1] + 'ed'
    return base + 'ed'


def build_english_table(en_field, english_overrides=None):
    """
    Generate the English Präsens/Präteritum/Perfekt tables matching
    the German 6-person layout. Returns None if the verb can't be
    meaningfully conjugated as a regular 'to X' verb and no override
    is given (e.g. bare modals without explicit irregular data yet).
    """
    overrides = english_overrides or {}

    if overrides.get('praesens_voll'):
        praesens = list(overrides['praesens_voll'])
        praeteritum = list(overrides.get('praeteritum_voll', []))
        perfekt = list(overrides.get('perfekt_voll', []))
        return {'praesens': praesens, 'praeteritum': praeteritum, 'perfekt': perfekt}

    base = extract_base_verb(en_field)
    if not base:
        return None  # bare modal or unparseable — needs explicit override later

    he_form = _present_he_form(base)
    praesens = [base, base, he_form, base, base, base]

    past = overrides.get('irregular_past') or _regular_past(base)
    praeteritum = [past] * 6

    participle = overrides.get('irregular_participle') or past
    aux = ['have', 'have', 'has', 'have', 'have', 'have']
    perfekt = [f'{aux[i]} {participle}' for i in range(6)]

    return {'praesens': praesens, 'praeteritum': praeteritum, 'perfekt': perfekt}
