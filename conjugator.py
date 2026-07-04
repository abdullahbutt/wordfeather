"""
conjugator.py — Full German verb conjugation engine
=====================================================
Generates a complete Reverso-style conjugation table (Indikativ,
Konjunktiv I, Konjunktiv II, Imperativ, Passiv) from a compact set
of principal parts per verb. This is rule-based, not a lookup table
of ~27,000 pre-typed forms — accuracy depends on correct input data,
not on this engine guessing irregular forms.

PRINCIPAL PARTS SCHEMA (per verb, stored in words_final.json under
the "conjugation" key):

    {
        "infinitiv":            "schwimmen",   # full infinitive
        "praesens_stamm":       null,           # du/er stem if changed
                                                 # (e.g. "nimm" for nehmen),
                                                 # null if regular
        "praeteritum_stamm":    "schwamm",      # person-invariant middle
                                                 # part; weak verbs end "te"
                                                 # (e.g. "machte")
        "partizip2":            "geschwommen",  # full participle
        "hilfsverb":            "sein",         # "haben" or "sein"
        "trennbares_praefix":   null,           # e.g. "auf" for aufstehen,
                                                 # null if not separable
        "konj2_stamm":          null,           # e.g. "schwömm" for
                                                 # schwimmen; null falls
                                                 # back to würde+Infinitiv
        "transitiv":            false,          # generates Passiv table
        "reflexiv":             false            # adds sich/mich/dich...
    }

Only "infinitiv", "praeteritum_stamm", "partizip2" and "hilfsverb" are
required. Everything else defaults sensibly for regular weak verbs.
"""

import re

PERSONS = ['ich', 'du', 'er/sie/es', 'wir', 'ihr', 'Sie']

REFLEXIVE_PRONOUNS = ['mich', 'dich', 'sich', 'uns', 'euch', 'sich']

# ── Fixed irregular auxiliary paradigms ─────────────────────────────────────
HABEN = {
    'praesens':      ['habe', 'hast', 'hat', 'haben', 'habt', 'haben'],
    'praeteritum':   ['hatte', 'hattest', 'hatte', 'hatten', 'hattet', 'hatten'],
    'konj1_praesens':['habe', 'habest', 'habe', 'haben', 'habet', 'haben'],
    'konj2':         ['hätte', 'hättest', 'hätte', 'hätten', 'hättet', 'hätten'],
}
SEIN = {
    'praesens':      ['bin', 'bist', 'ist', 'sind', 'seid', 'sind'],
    'praeteritum':   ['war', 'warst', 'war', 'waren', 'wart', 'waren'],
    'konj1_praesens':['sei', 'seist', 'sei', 'seien', 'seiet', 'seien'],
    'konj2':         ['wäre', 'wärst', 'wäre', 'wären', 'wärt', 'wären'],
}
WERDEN = {
    'praesens':      ['werde', 'wirst', 'wird', 'werden', 'werdet', 'werden'],
    'praeteritum':   ['wurde', 'wurdest', 'wurde', 'wurden', 'wurdet', 'wurden'],
    'konj1_praesens':['werde', 'werdest', 'werde', 'werden', 'werdet', 'werden'],
    'konj2_wuerde':  ['würde', 'würdest', 'würde', 'würden', 'würdet', 'würden'],
}

AUX = {'haben': HABEN, 'sein': SEIN, 'werden': WERDEN}


def _regular_stem(infinitiv, prefix):
    """Strip trailing -en/-n and any separable prefix to get the bare stem."""
    inf = infinitiv
    if prefix and inf.startswith(prefix):
        inf = inf[len(prefix):]
    if inf.endswith('eln') or inf.endswith('ern'):
        return inf[:-1]          # sammeln -> sammel, wandern -> wander
    if inf.endswith('en'):
        return inf[:-2]
    if inf.endswith('n'):
        return inf[:-1]
    return inf


def _needs_extra_e(stem):
    """Verbs whose stem ends in d/t, or in m/n preceded by a *different*
    non-vowel, non-l/r/h consonant, need an epenthetic -e- before
    consonant-initial endings: arbeitest, atmet, regnest, öffnest.
    Doubled consonants (schwimm-, komm-, renn-) and stems ending in
    m/n after a vowel or a genuine single l/r/h DO NOT need it:
    schwimmst, kommst, lernst, wohnst. But the 'ch' digraph is NOT
    the same as a plain 'h' — it behaves like any other consonant
    cluster and DOES need the epenthetic -e-: rechnen->rechnest,
    zeichnen->zeichnest (not 'rechnst'/'zeichnst')."""
    if not stem:
        return False
    last = stem[-1]
    if last in ('d', 't'):
        return True
    if last in ('m', 'n') and len(stem) >= 2:
        prev = stem[-2]
        is_ch_digraph = prev == 'h' and len(stem) >= 3 and stem[-3] == 'c'
        if is_ch_digraph:
            return True
        if prev in 'aeiouäöüy' or prev in ('l', 'r', 'h') or prev == last:
            return False
        return True
    return False


def _present_forms(stem, changed_stem, is_eln_ern=False):
    """Build the 6-person Präsens indicative forms.
    Stems ending in a sibilant (s, ß, z, x) merge the -st du-ending
    down to just -t: essen (changed stem 'iss') -> du isst, not 'issst'.
    The epenthetic -e- (arbeitest, findest) only applies to the
    REGULAR unchanged stem. A genuine ablaut-changed präsens stem
    (fahren->fährst, laden->lädst, halten->hältst, raten->rätst)
    never takes it, even when it ends in d/t — only the raw stem
    used for ich/wir/ihr/Sie does (arbeiten->arbeitest, bitten->bittest,
    finden->findest, none of which have a präsens vowel change).
    -eln/-ern class verbs (wechseln, wandern) have infinitives ending
    in just -n, not -en — so wir/sie/Sie must match the infinitive
    exactly (wechseln, not 'wechselen') rather than getting the usual
    stem+en ending."""
    s = stem
    s2 = changed_stem or stem
    e = 'e' if (not changed_stem and _needs_extra_e(s2)) else ''
    du_ending = 't' if s2[-1] in ('s', 'ß', 'z', 'x') else e + 'st'
    ich  = s + 'e'
    du   = s2 + du_ending
    er   = s2 if (changed_stem and s2.endswith('t')) else s2 + e + 't'
    wir_sie_ending = 'n' if is_eln_ern else 'en'
    wir  = s + wir_sie_ending
    ihr  = s + (('e' if _needs_extra_e(s) else '')) + 't'
    sie  = s + wir_sie_ending
    return [ich, du, er, wir, ihr, sie]


def _preterite_forms(praeteritum_stamm):
    """Build the 6-person Präteritum indicative forms.
    Stems ending in -e (machte, wurde) use 'weak' endings [-,st,-,n,t,n],
    attaching directly since the stem already supplies a linking vowel.
    Stems ending in a consonant (schwamm, stand, bat) use 'strong'
    endings [-,st,-,en,t,en], with an epenthetic -e- inserted before
    -st/-t when the stem ends in d/t or an awkward m/n cluster
    (stand -> standest, bat -> batest; but schwamm -> schwammst, no e)."""
    stem = praeteritum_stamm
    if stem.endswith('e'):
        return [stem, stem + 'st', stem, stem + 'n', stem + 't', stem + 'n']
    else:
        e = 'e' if _needs_extra_e(stem) else ''
        du_ending = 't' if stem[-1] in ('s', 'ß', 'z', 'x') else e + 'st'
        return [stem, stem + du_ending, stem, stem + 'en', stem + e + 't', stem + 'en']


def _konj1_praesens_forms(stem, is_eln_ern=False):
    """Konjunktiv I endings (-e, -est, -e, -en, -et, -en) always already
    contain the linking vowel, so no epenthetic -e- insertion is needed
    here regardless of the stem's final consonant. wir/sie always
    coincide with the infinitive for every verb type in German, so
    -eln/-ern class verbs need stem+'n' there too (fordern, not
    'forderen'), matching the same fix applied to the indicative."""
    wir_sie_ending = 'n' if is_eln_ern else 'en'
    return [stem + 'e', stem + 'est', stem + 'e',
             stem + wir_sie_ending, stem + 'et', stem + wir_sie_ending]


def _konj2_forms(konj2_stamm):
    """Konjunktiv II endings, same fixed pattern as Konjunktiv I."""
    return [konj2_stamm + 'e', konj2_stamm + 'est', konj2_stamm + 'e',
             konj2_stamm + 'en', konj2_stamm + 'et', konj2_stamm + 'en']


def _attach(forms, suffix_words):
    """Append trailing words (prefix, reflexive pronoun, etc.) to each form."""
    if not suffix_words:
        return forms
    return [f + ' ' + suffix_words for f in forms]


def _attach_per_person(forms, per_person_suffix):
    return [f + ' ' + per_person_suffix[i] for i, f in enumerate(forms)]


def _partizip1(infinitiv, override=None):
    """Partizip Präsens (present participle): normally infinitive + 'd'
    (machen -> machend, schwimmen -> schwimmend, gehen -> gehend).
    A handful of short/irregular infinitives (sein -> seiend, tun ->
    tuend) need an inserted -e- and must be given via override."""
    if override:
        return override
    return infinitiv + 'd'


def _zu_infinitiv(infinitiv, reg_stem, prefix, reflexiv=False, is_eln_ern=False):
    """zu + Infinitiv: for separable verbs 'zu' is inserted as one word
    between prefix and stem (aufstehen -> aufzustehen); for everything
    else it's a separate word before the infinitive (sein -> zu sein).
    Reflexive verbs prepend 'sich' (sich freuen -> sich zu freuen).
    -eln/-ern class verbs need reg_stem+'n' not reg_stem+'en' here too
    (aufzufordern, not 'aufzuforderen')."""
    if prefix:
        ending = 'n' if is_eln_ern else 'en'
        result = prefix + 'zu' + reg_stem + ending
    else:
        result = 'zu ' + infinitiv
    if reflexiv:
        result = 'sich ' + result
    return result


def conjugate(principal_parts):
    """
    Generate the complete conjugation table for one verb.
    Returns a nested dict matching the Reverso-style structure:
        {
          "indikativ": {"praesens": [...6], "praeteritum": [...6],
                        "perfekt": [...6], "plusquamperfekt": [...6],
                        "futur1": [...6], "futur2": [...6]},
          "konjunktiv1": {"praesens": [...], "perfekt": [...],
                          "futur1": [...], "futur2": [...]},
          "konjunktiv2": {"praeteritum": [...], "plusquamperfekt": [...],
                          "futur1": [...], "futur2": [...]},
          "imperativ": {"du": "...", "ihr": "...", "Sie": "...", "wir": "..."},
          "passiv": {...} or None if intransitive
        }
    """
    p = principal_parts
    infinitiv          = p['infinitiv']
    praesens_stamm_in   = p.get('praesens_stamm')
    praeteritum_stamm  = p['praeteritum_stamm']
    partizip2          = p['partizip2']
    hilfsverb          = p.get('hilfsverb', 'haben')
    prefix             = p.get('trennbares_praefix')
    konj2_stamm        = p.get('konj2_stamm')
    transitiv          = p.get('transitiv', False)
    reflexiv           = p.get('reflexiv', False)

    reg_stem = _regular_stem(infinitiv, prefix)
    changed_stem = praesens_stamm_in  # already prefix-stripped if separable

    # -eln/-ern class verbs (wechseln, wandern) need special present-tense
    # handling: their infinitive ends in just -n (not -en), so wir/sie/Sie
    # must match the infinitive exactly rather than getting stem+en.
    # -eln verbs specifically ALSO drop the stem-internal -e- for ich only
    # (ich wechsle, not wechsele) — -ern verbs keep it (ich fordere).
    bare_infinitiv = infinitiv[len(prefix):] if (prefix and infinitiv.startswith(prefix)) else infinitiv
    is_eln_ern = bare_infinitiv.endswith('eln') or bare_infinitiv.endswith('ern')
    is_eln = bare_infinitiv.endswith('eln')

    # ── Base conjugated forms (verb only, no prefix/reflexive yet) ─────────
    praesens_voll_override = p.get('praesens_voll')  # for sein/werden etc.
    konj1_voll_override    = p.get('konj1_praesens_voll')

    praesens_base = list(praesens_voll_override) if praesens_voll_override \
        else _present_forms(reg_stem, changed_stem, is_eln_ern)
    if is_eln and not praesens_voll_override and not changed_stem:
        # ich wechsle, not wechsele — drop the stem-internal -e- before -l-
        praesens_base[0] = reg_stem[:-2] + 'le'
    praeteritum_base = _preterite_forms(praeteritum_stamm)
    konj1_base = list(konj1_voll_override) if konj1_voll_override \
        else _konj1_praesens_forms(reg_stem, is_eln_ern)
    if konj2_stamm:
        konj2_voll_override = p.get('konj2_voll')
        konj2_base = list(konj2_voll_override) if konj2_voll_override \
            else _konj2_forms(konj2_stamm)
        konj2_is_wuerde = False
    else:
        konj2_base = list(WERDEN['konj2_wuerde'])
        konj2_is_wuerde = True

    def add_reflexive_and_prefix(forms, add_infinitiv_tail=None):
        """Attach reflexive pronoun then separable prefix (finite forms),
        or attach reflexive + full infinitive tail (non-finite constructs)."""
        out = list(forms)
        if reflexiv:
            out = _attach_per_person(out, REFLEXIVE_PRONOUNS)
        if add_infinitiv_tail:
            out = _attach(out, add_infinitiv_tail)
        elif prefix:
            out = _attach(out, prefix)
        return out

    # ── INDIKATIV ────────────────────────────────────────────────────────
    ind_praesens    = add_reflexive_and_prefix(praesens_base)
    ind_praeteritum = add_reflexive_and_prefix(praeteritum_base)

    aux = AUX[hilfsverb]
    # Perfekt: aux(präsens) + [reflexive] + partizip2
    ind_perfekt = []
    for i in range(6):
        parts = [aux['praesens'][i]]
        if reflexiv:
            parts.append(REFLEXIVE_PRONOUNS[i])
        parts.append(partizip2)
        ind_perfekt.append(' '.join(parts))

    ind_plusquamperfekt = []
    for i in range(6):
        parts = [aux['praeteritum'][i]]
        if reflexiv:
            parts.append(REFLEXIVE_PRONOUNS[i])
        parts.append(partizip2)
        ind_plusquamperfekt.append(' '.join(parts))

    # Futur I: werden(präsens) + [reflexive] + full infinitiv (at end)
    ind_futur1 = []
    for i in range(6):
        parts = [WERDEN['praesens'][i]]
        if reflexiv:
            parts.append(REFLEXIVE_PRONOUNS[i])
        parts.append(infinitiv)
        ind_futur1.append(' '.join(parts))

    # Futur II: werden(präsens) + [reflexive] + partizip2 + hilfsverb(infinitiv)
    ind_futur2 = []
    for i in range(6):
        parts = [WERDEN['praesens'][i]]
        if reflexiv:
            parts.append(REFLEXIVE_PRONOUNS[i])
        parts.append(partizip2)
        parts.append(hilfsverb)
        ind_futur2.append(' '.join(parts))

    # ── KONJUNKTIV I ─────────────────────────────────────────────────────
    k1_praesens = add_reflexive_and_prefix(konj1_base)

    k1_perfekt = []
    for i in range(6):
        parts = [aux['konj1_praesens'][i]]
        if reflexiv:
            parts.append(REFLEXIVE_PRONOUNS[i])
        parts.append(partizip2)
        k1_perfekt.append(' '.join(parts))

    k1_futur1 = []
    for i in range(6):
        parts = [WERDEN['konj1_praesens'][i]]
        if reflexiv:
            parts.append(REFLEXIVE_PRONOUNS[i])
        parts.append(infinitiv)
        k1_futur1.append(' '.join(parts))

    k1_futur2 = []
    for i in range(6):
        parts = [WERDEN['konj1_praesens'][i]]
        if reflexiv:
            parts.append(REFLEXIVE_PRONOUNS[i])
        parts.append(partizip2)
        parts.append(hilfsverb)
        k1_futur2.append(' '.join(parts))

    # ── KONJUNKTIV II ────────────────────────────────────────────────────
    if konj2_is_wuerde:
        # würde + [reflexive] + full infinitiv
        k2_praeteritum = []
        for i in range(6):
            parts = [konj2_base[i]]
            if reflexiv:
                parts.append(REFLEXIVE_PRONOUNS[i])
            parts.append(infinitiv)
            k2_praeteritum.append(' '.join(parts))
    else:
        k2_praeteritum = add_reflexive_and_prefix(konj2_base)

    aux2 = AUX[hilfsverb]
    k2_plusquamperfekt = []
    for i in range(6):
        parts = [aux2['konj2'][i]]
        if reflexiv:
            parts.append(REFLEXIVE_PRONOUNS[i])
        parts.append(partizip2)
        k2_plusquamperfekt.append(' '.join(parts))

    k2_futur1 = []
    for i in range(6):
        parts = [WERDEN['konj2_wuerde'][i]]
        if reflexiv:
            parts.append(REFLEXIVE_PRONOUNS[i])
        parts.append(infinitiv)
        k2_futur1.append(' '.join(parts))

    k2_futur2 = []
    for i in range(6):
        parts = [WERDEN['konj2_wuerde'][i]]
        if reflexiv:
            parts.append(REFLEXIVE_PRONOUNS[i])
        parts.append(partizip2)
        parts.append(hilfsverb)
        k2_futur2.append(' '.join(parts))

    # ── IMPERATIV ────────────────────────────────────────────────────────
    # Modal verbs (dürfen, können, müssen, sollen, wollen, mögen) have no
    # true imperative in standard German — set 'kein_imperativ': True to
    # suppress it entirely (the UI hides the section when imperativ is None).
    imperativ_override = p.get('imperativ_voll')
    if p.get('kein_imperativ'):
        imperativ = None
    elif imperativ_override:
        imperativ = dict(imperativ_override)
    else:
        # German imperative uses e->i/ie present-tense stem changes
        # (nehmen->Nimm!, sehen->Sieh!) but NOT a->ä/au->äu umlaut
        # changes (fahren->Fahr! not *Fähr!, halten->Halt! not *Hält!,
        # laden->Lad! not *Läd!, braten->Brat! not *Brät!).
        # Verbs with ANY präsens ablaut (even umlaut-excluded ones)
        # also skip the epenthetic -e- even on the regular fallback
        # stem (halten->Halt! not *Halte!, laden->Lad! not *Lade!) —
        # only verbs with NO präsens vowel change at all keep it
        # (arbeiten->Arbeite!, bitten->Bitte!).
        has_umlaut = changed_stem and any(c in changed_stem for c in 'äöü')
        du_stem = reg_stem if (not changed_stem or has_umlaut) else changed_stem
        e = 'e' if (not changed_stem and _needs_extra_e(du_stem)) else ''
        base_infinitiv = (reg_stem + ('n' if is_eln_ern else 'en')) if prefix else infinitiv
        imp_du   = (du_stem + e).capitalize()
        imp_ihr  = (reg_stem + ('e' if _needs_extra_e(reg_stem) else '') + 't').capitalize()
        imp_sie  = base_infinitiv.capitalize() + ' Sie'
        imp_wir  = base_infinitiv.capitalize() + ' wir'
        if reflexiv:
            imp_du  += ' dich'
            imp_ihr += ' euch'
            imp_sie += ' sich'
            imp_wir += ' uns'
        if prefix:
            imp_du  += ' ' + prefix
            imp_ihr += ' ' + prefix
            imp_sie += ' ' + prefix
            imp_wir += ' ' + prefix
        imperativ = {'du': imp_du + '!', 'ihr': imp_ihr + '!',
                     'Sie': imp_sie + '!', 'wir': imp_wir + '!'}

    # ── PASSIV (only for transitive verbs) ──────────────────────────────
    passiv = None
    if transitiv:
        pv_praesens = [f'{WERDEN["praesens"][i]} {partizip2}' for i in range(6)]
        pv_praeteritum = [f'{WERDEN["praeteritum"][i]} {partizip2}' for i in range(6)]
        pv_perfekt = [f'{SEIN["praesens"][i]} {partizip2} worden' for i in range(6)]
        pv_plusquamperfekt = [f'{SEIN["praeteritum"][i]} {partizip2} worden' for i in range(6)]
        pv_futur1 = [f'{WERDEN["praesens"][i]} {partizip2} werden' for i in range(6)]
        passiv = {
            'praesens': pv_praesens,
            'praeteritum': pv_praeteritum,
            'perfekt': pv_perfekt,
            'plusquamperfekt': pv_plusquamperfekt,
            'futur1': pv_futur1,
        }

    partizip1 = _partizip1(infinitiv, p.get('partizip1_voll'))
    zu_infinitiv = _zu_infinitiv(infinitiv, reg_stem, prefix, reflexiv, is_eln_ern)

    return {
        'infinitiv': infinitiv,
        'partizip1': partizip1,
        'partizip2': partizip2,
        'zu_infinitiv': zu_infinitiv,
        'hilfsverb': hilfsverb,
        'indikativ': {
            'praesens': ind_praesens,
            'praeteritum': ind_praeteritum,
            'perfekt': ind_perfekt,
            'plusquamperfekt': ind_plusquamperfekt,
            'futur1': ind_futur1,
            'futur2': ind_futur2,
        },
        'konjunktiv1': {
            'praesens': k1_praesens,
            'perfekt': k1_perfekt,
            'futur1': k1_futur1,
            'futur2': k1_futur2,
        },
        'konjunktiv2': {
            'praeteritum': k2_praeteritum,
            'plusquamperfekt': k2_plusquamperfekt,
            'futur1': k2_futur1,
            'futur2': k2_futur2,
        },
        'imperativ': imperativ,
        'passiv': passiv,
    }
