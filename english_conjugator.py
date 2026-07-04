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
from irregular_english_verbs import IRREGULAR_PAST, BRITISH_SPELLING_BASE, PRESENT_HE_IRREGULAR

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
    ('to drive, to go' -> 'drive'). Slash-separated dual translations
    ('to lend/borrow') are also rejected — picking either half without
    verification would be a guess, not a derivation."""
    if not en_field:
        return None
    first = en_field.split(',')[0].strip()
    if not first.lower().startswith('to '):
        return None
    base = first[3:].strip()
    if '/' in base:
        return None
    return base


def _split_phrasal(base):
    """Split a phrasal-verb base into its conjugatable first word and
    the unchanged remainder ('pick up' -> ('pick', ' up'); 'work' ->
    ('work', '')). Present/past tense rules only ever apply to the
    first word — 'pick up' must become 'picks up'/'picked up', never
    'pick ups'/'pick uped'. Applies the British spelling correction
    (favor->favour, practice(verb)->practise) to the head before any
    further processing, so it propagates through every derived form."""
    parts = base.split(' ', 1)
    head = BRITISH_SPELLING_BASE.get(parts[0], parts[0])
    rest = ' ' + parts[1] if len(parts) > 1 else ''
    return head, rest


def _needs_es(word):
    """Verbs needing -es instead of -s for he/she/it: ends in
    s/x/z/ch/sh, or consonant+o (do->does, go->goes)."""
    if re.search(r'(s|x|z|ch|sh)$', word):
        return True
    if re.search(r'[^aeiou]o$', word):
        return True
    return False


def _present_he_form(base):
    """he/she/it present form: base + s, with spelling rules.
    Only the first word of a phrasal verb is conjugated."""
    head, rest = _split_phrasal(base)
    if head in PRESENT_HE_IRREGULAR:
        return PRESENT_HE_IRREGULAR[head] + rest
    if _needs_es(head):
        return head + 'es' + rest
    if re.search(r'[^aeiou]y$', head):
        return head[:-1] + 'ies' + rest
    return head + 's' + rest


def _regular_past(base):
    """Regular English past tense (also used for the past participle,
    since regular verbs' past and past participle are identical).
    Only the first word of a phrasal verb is conjugated. British
    spelling convention: verbs ending in a vowel+l double the l
    (travel->travelled), unlike American English. Monosyllabic
    consonant-doubling (stop->stopped, shop->shopped) is deliberately
    NOT handled by a generic rule here — a naive length/pattern check
    doubles many polysyllabic verbs that must NOT double (answer->
    answerred is wrong, must stay 'answered'; order->orderred is
    wrong, must stay 'ordered'). Verbs needing genuine monosyllabic
    doubling are handled via explicit 'irregular_past' overrides
    instead, verified individually — safer than a heuristic that gets
    more wrong than right."""
    head, rest = _split_phrasal(base)
    if head.endswith('e'):
        return head + 'd' + rest
    if re.search(r'[^aeiou]y$', head):
        return head[:-1] + 'ied' + rest
    if re.search(r'[aeiou]l$', head):
        return head + 'led' + rest
    return head + 'ed' + rest


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

    head, rest = _split_phrasal(base)
    base = head + rest  # re-join with British-spelling-corrected head

    he_form = _present_he_form(base)
    praesens = [base, base, he_form, base, base, base]

    irregular = IRREGULAR_PAST.get(head)
    if overrides.get('irregular_past'):
        past = overrides['irregular_past']
    elif irregular:
        past = irregular[0] + rest
    else:
        past = _regular_past(base)
    praeteritum = [past] * 6

    if overrides.get('irregular_participle'):
        participle = overrides['irregular_participle']
    elif irregular and irregular[1]:
        participle = irregular[1] + rest
    else:
        participle = past
    aux = ['have', 'have', 'has', 'have', 'have', 'have']
    perfekt = [f'{aux[i]} {participle}' for i in range(6)]

    return {'praesens': praesens, 'praeteritum': praeteritum, 'perfekt': perfekt}
