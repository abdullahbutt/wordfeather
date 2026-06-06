# Schema v2 — Lemma-Centric Lexical Architecture
**Version:** 2.0-draft
**Date:** 2026-06-06
**Status:** Specification for migration from `words_final.json` (v1) to `words_v2.json`
**Backward compatibility:** `build.py` flattens v2 → v1 for HTML generation — zero frontend changes

---

## Design Principles

1. **One row per lemma** — not per level, not per meaning
2. **Senses hold the variation** — different meanings, different levels, different registers live inside `senses[]`
3. **Morphology is separate from semantics** — `article`, `plural`, `pos` are top-level; `en`, `example`, `level` are per-sense
4. **Topics are per-lemma** — a word like `Bank` belongs to topic `finance` AND `daily-life`, regardless of which sense
5. **Frequency is per-lemma** — how common the word is overall, not per-sense
6. **Frontend never sees v2** — `build.py` always flattens v2 → v1 format before generating HTML

---

## Top-Level Entry Structure

```json
{
  "id":         "bank_001",
  "lemma":      "Bank",
  "article":    "die",
  "plural":     "Bänke / Banken",
  "pos":        "noun",
  "frequency":  2,
  "topics":     ["finance", "daily-life"],
  "senses": [
    {
      "sense_id":    "bank_001_s1",
      "en":          "bench",
      "level":       "A1",
      "register":    "everyday",
      "example":     "Sie sitzt auf einer Bank im Park.",
      "example_en":  "She is sitting on a bench in the park.",
      "collocations": []
    },
    {
      "sense_id":    "bank_001_s2",
      "en":          "bank (financial institution)",
      "level":       "A2",
      "register":    "everyday",
      "example":     "Ich habe ein Konto bei der Bank eröffnet.",
      "example_en":  "I opened an account at the bank.",
      "collocations": []
    }
  ]
}
```

---

## Field Reference — Top Level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique identifier: `{lemma_slug}_{sequence}` e.g. `"probezeit_001"` |
| `lemma` | string | ✅ | Dictionary headword without article or plural. Nouns: `"Probezeit"`. Verbs: `"bezahlen"`. Phrases: `"Maßnahmen ergreifen"`. Proverbs: full sentence. |
| `article` | string | ✅ | `"der"` / `"die"` / `"das"` / `""` (empty for verbs, adjectives, adverbs, phrases) |
| `plural` | string | ✅ | Plural form or marker. `"Probezeiten"` or `"-en"` or `""` (empty for uncountable/non-nouns) or `"—"` (no plural exists) |
| `pos` | string | ✅ | Part of speech — see POS taxonomy below |
| `frequency` | integer | ✅ | Usage frequency tier: 1 (core everyday) → 5 (rare/specialised) |
| `topics` | array | ✅ | 1–3 topic tags from controlled vocabulary — see Topic taxonomy below |
| `senses` | array | ✅ | 1+ sense objects — see Sense structure below |

---

## Field Reference — Sense Level

Each entry in `senses[]`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sense_id` | string | ✅ | Unique: `{parent_id}_s{n}` e.g. `"bank_001_s1"` |
| `en` | string | ✅ | English translation for THIS sense |
| `level` | string | ✅ | CEFR level: `A1` `A2` `B1` `B2` `C1` `C2` |
| `register` | string | ✅ | Register: `everyday` `formal` `academic` `literary` `colloquial` |
| `example` | string | ✅ | German example sentence demonstrating THIS sense |
| `example_en` | string | ⚠️ | English translation of example (empty for some A1 entries) |
| `collocations` | array | B2+ | 2–3 German collocations for this sense |
| `note` | string | ○ | Optional disambiguation: `"financial"`, `"park bench"`, `"legal term"` |

---

## POS Taxonomy

13 values. Every entry MUST have exactly one.

| Value | Description | Count (est.) | Example |
|-------|-------------|-------------|---------|
| `noun` | All nouns — with or without article/plural | ~2,174 | `"Probezeit"`, `"Klimaschutz"` |
| `verb` | Regular infinitives, including separable/reflexive base forms | ~299 | `"bezahlen"`, `"umsteigen"` |
| `adjective` | Attributive or predicative adjectives | ~200 | `"freundlich"`, `"nachhaltig"` |
| `adverb` | True adverbs and sentence modifiers | ~80 | `"immer"`, `"besonders"` |
| `preposition` | Prepositions and postpositions | ~25 | `"über"`, `"mit"`, `"wegen"` |
| `conjunction` | Coordinating and subordinating conjunctions | ~20 | `"weil"`, `"obwohl"`, `"aber"` |
| `particle` | Modal, discourse, and focus particles | ~30 | `"doch"`, `"mal"`, `"allerdings"`, `"zumal"` |
| `pronoun` | Personal, demonstrative, relative pronouns | ~10 | `"ich"`, `"welch-"`, `"dies-"` |
| `determiner` | Articles, possessives, quantifiers | ~8 | `"ein/eine"`, `"jeder/jede/jedes"`, `"kein/keine"` |
| `phrase` | Multi-word fixed expressions and collocations | ~66 | `"Maßnahmen ergreifen"`, `"Abschied nehmen"` |
| `idiom` | Idiomatic expressions with figurative meaning | ~30 | `"den Nagel auf den Kopf treffen"`, `"auf dem Holzweg sein"` |
| `proverb` | Complete proverb sentences | ~52 | `"Übung macht den Meister."`, `"Gut Ding will Weile haben."` |
| `template` | Academic discourse templates | ~14 | `"Im Hinblick auf ..."`, `"Es lässt sich nicht bestreiten, dass ..."` |

### POS assignment rules

| Pattern in v1 `de` field | Assigned POS | Parsing |
|--------------------------|-------------|---------|
| `"der/die/das X, -en"` | `noun` | article → `article`, X → `lemma`, -en → `plural` |
| `"der/die/das X"` (no comma) | `noun` | article → `article`, X → `lemma`, plural → `""` (lookup needed) |
| `"Xen"` (single word ending -en, lowercase) | `verb` | full word → `lemma` |
| `"sich Xen"` | `verb` | `"Xen"` → `lemma`, add `note: "reflexive"` |
| Word ending in -lich/-ig/-isch/-bar/-sam/-haft/-los | `adjective` | full word → `lemma` |
| Known adverb set (immer, oft, hier, ...) | `adverb` | full word → `lemma` |
| Known particle set (allerdings, zumal, doch, ...) | `particle` | full word → `lemma` |
| Known conjunction set (weil, obwohl, aber, ...) | `conjunction` | full word → `lemma` |
| `"dies-"`, `"ein/eine"`, `"welch-"` | `determiner` | normalised form → `lemma` |
| Multi-word with verb + noun (`"Maßnahmen ergreifen"`) | `phrase` | full phrase → `lemma` |
| Multi-word with figurative meaning | `idiom` | full phrase → `lemma` |
| Sentence ending in `.` or `!` | `proverb` | full sentence → `lemma` |
| Contains `...` | `template` | full phrase → `lemma` |

---

## Topic Taxonomy

28 controlled tags. Every entry gets 1–3 tags.

| Tag | Scope | Typical levels |
|-----|-------|----------------|
| `daily-life` | General everyday situations, routines | A1–A2 |
| `family` | Family members, relationships, life events | A1–B1 |
| `home` | Household, furniture, living, repairs | A1–A2 |
| `food` | Eating, drinking, cooking, ingredients | A1–A2 |
| `transport` | Vehicles, public transport, navigation | A1–B1 |
| `shopping` | Purchasing, money, stores, returns | A1–A2 |
| `school` | School, learning, classrooms, grades | A1–B1 |
| `education` | University, training, qualifications, research | B1–C1 |
| `technology` | Computers, internet, apps, AI, digital | A2–C1 |
| `travel` | Tourism, flights, accommodation, abroad | A2–B1 |
| `weather` | Weather, seasons, temperature, climate (simple) | A1–A2 |
| `nature` | Plants, animals, landscapes, geography | A2–B1 |
| `work` | Employment, career, office, colleagues | A2–B2 |
| `health` | Body, illness, doctors, hospitals, wellbeing | A1–B2 |
| `medicine` | Medical science, treatments, research | B2–C1 |
| `society` | Social issues, community, volunteering, equality | B1–C1 |
| `law` | Courts, contracts, rights, criminal justice | B2–C1 |
| `politics` | Government, elections, parties, democracy | B1–C2 |
| `media` | News, journalism, social media, press | B1–B2 |
| `economics` | Markets, trade, inflation, business | B2–C1 |
| `environment` | Pollution, climate change, sustainability, energy | B1–C1 |
| `science` | Biology, physics, chemistry, research methods | C1–C2 |
| `philosophy` | Ethics, epistemology, metaphysics, logic | C1–C2 |
| `linguistics` | Syntax, semantics, pragmatics, discourse | C1–C2 |
| `culture` | Arts, music, theatre, heritage, literature | B2–C2 |
| `rhetoric` | Figures of speech, argumentation, persuasion | C1–C2 |
| `history` | Historical events, epochs, movements | B2–C2 |
| `leisure` | Sports, hobbies, entertainment, parks | A1–B1 |

---

## Frequency Scale

| Value | Label | Description | Approx. German rank |
|-------|-------|-------------|-------------------|
| 1 | Core | Top 1,000 most frequent words; essential for survival | 1–1,000 |
| 2 | Common | Everyday vocabulary; understood by all native speakers | 1,000–3,000 |
| 3 | Intermediate | Used regularly in conversation, news, workplace | 3,000–6,000 |
| 4 | Advanced | Semi-formal, journalistic, professional vocabulary | 6,000–12,000 |
| 5 | Specialised | Academic, literary, technical, rare vocabulary | 12,000+ |

### Default frequency assignment by level

| Level | Default frequency | Override when... |
|-------|------------------|-----------------|
| A1 | 1 | Override to 2 if not in Goethe A1 official list |
| A2 | 2 | Override to 1 if word is in top-1000 frequency |
| B1 | 3 | Override to 2 if word is clearly everyday |
| B2 | 4 | Override to 3 if word appears regularly in news |
| C1 | 5 | Override to 4 if word is common in formal writing |
| C2 | 5 | Override to 4 for common literary/idiomatic terms |

---

## Register Taxonomy

5 values. Applied per-sense, not per-lemma.

| Value | Description | Typical levels |
|-------|-------------|----------------|
| `everyday` | Spoken, informal, daily use | A1–B1 |
| `colloquial` | Slang, regional, informal-only usage | A2–B1 |
| `formal` | Professional, official, journalistic | B2–C1 |
| `academic` | Scientific, scholarly, research language | C1–C2 |
| `literary` | Poetic, rhetorical, idiomatic, archaic | C2 |

---

## Example Entries by POS Type

### Noun (with article + plural)
```json
{
  "id": "probezeit_001",
  "lemma": "Probezeit",
  "article": "die",
  "plural": "Probezeiten",
  "pos": "noun",
  "frequency": 3,
  "topics": ["work"],
  "senses": [{
    "sense_id": "probezeit_001_s1",
    "en": "probationary period",
    "level": "B1",
    "register": "everyday",
    "example": "Während der Probezeit lernt man die Kolleginnen gut kennen.",
    "example_en": "During the probationary period you get to know your colleagues well.",
    "collocations": ["die Probezeit bestehen", "sich bewähren", "Probezeit verlängern"]
  }]
}
```

### Noun (multiple senses across levels)
```json
{
  "id": "krankenhaus_001",
  "lemma": "Krankenhaus",
  "article": "das",
  "plural": "Krankenhäuser",
  "pos": "noun",
  "frequency": 1,
  "topics": ["health"],
  "senses": [
    {
      "sense_id": "krankenhaus_001_s1",
      "en": "hospital",
      "level": "A1",
      "register": "everyday",
      "example": "Er ist im Krankenhaus.",
      "example_en": "He is in hospital.",
      "collocations": []
    },
    {
      "sense_id": "krankenhaus_001_s2",
      "en": "hospital",
      "level": "B1",
      "register": "everyday",
      "example": "Sie wurde nach dem Unfall sofort ins Krankenhaus gebracht.",
      "example_en": "She was taken to hospital immediately after the accident.",
      "collocations": ["ins Krankenhaus eingeliefert werden", "stationär behandeln", "Klinikaufenthalt"],
      "note": "contextual B1 usage with medical/emergency register"
    }
  ]
}
```

### Verb (regular)
```json
{
  "id": "bezahlen_001",
  "lemma": "bezahlen",
  "article": "",
  "plural": "",
  "pos": "verb",
  "frequency": 1,
  "topics": ["shopping", "daily-life"],
  "senses": [{
    "sense_id": "bezahlen_001_s1",
    "en": "to pay",
    "level": "A1",
    "register": "everyday",
    "example": "Ich möchte bitte bezahlen.",
    "example_en": "I would like to pay please.",
    "collocations": []
  }]
}
```

### Verb (reflexive)
```json
{
  "id": "aergern_001",
  "lemma": "ärgern",
  "article": "",
  "plural": "",
  "pos": "verb",
  "frequency": 2,
  "topics": ["daily-life"],
  "senses": [{
    "sense_id": "aergern_001_s1",
    "en": "to be annoyed / to get angry",
    "level": "A2",
    "register": "everyday",
    "example": "Sie ärgert sich, weil ihr Koffer verloren gegangen ist.",
    "example_en": "She is annoyed because her suitcase was lost.",
    "collocations": [],
    "note": "reflexive: sich ärgern (über + acc)"
  }]
}
```

### Adjective
```json
{
  "id": "nachhaltig_001",
  "lemma": "nachhaltig",
  "article": "",
  "plural": "",
  "pos": "adjective",
  "frequency": 4,
  "topics": ["environment", "economics"],
  "senses": [{
    "sense_id": "nachhaltig_001_s1",
    "en": "sustainable",
    "level": "B2",
    "register": "formal",
    "example": "Das Unternehmen setzt auf nachhaltige Produktionsmethoden.",
    "example_en": "The company relies on sustainable production methods.",
    "collocations": ["nachhaltig wirtschaften", "nachhaltige Entwicklung", "langfristig denken"]
  }]
}
```

### Particle / discourse marker
```json
{
  "id": "allerdings_001",
  "lemma": "allerdings",
  "article": "",
  "plural": "",
  "pos": "particle",
  "frequency": 3,
  "topics": ["rhetoric"],
  "senses": [{
    "sense_id": "allerdings_001_s1",
    "en": "however / admittedly",
    "level": "C2",
    "register": "formal",
    "example": "Das Experiment lieferte interessante Ergebnisse; allerdings sind diese noch nicht reproduziert worden.",
    "example_en": "The experiment yielded interesting results; however, these have not yet been reproduced.",
    "collocations": ["Einschränkung einführen", "konzessiv", "differenziert argumentieren"]
  }]
}
```

### Phrase (fixed collocation)
```json
{
  "id": "massnahmen_ergreifen_001",
  "lemma": "Maßnahmen ergreifen",
  "article": "",
  "plural": "",
  "pos": "phrase",
  "frequency": 4,
  "topics": ["politics", "society"],
  "senses": [{
    "sense_id": "massnahmen_ergreifen_001_s1",
    "en": "to take measures",
    "level": "B2",
    "register": "formal",
    "example": "Die Regierung ergreift sofortige Maßnahmen gegen die Ausbreitung der Epidemie.",
    "example_en": "The government is taking immediate measures against the spread of the epidemic.",
    "collocations": ["Maßnahmen ergreifen", "dringende Maßnahmen", "wirksame Gegenmaßnahmen"]
  }]
}
```

### Idiom
```json
{
  "id": "nagel_kopf_001",
  "lemma": "den Nagel auf den Kopf treffen",
  "article": "",
  "plural": "",
  "pos": "idiom",
  "frequency": 5,
  "topics": ["rhetoric"],
  "senses": [{
    "sense_id": "nagel_kopf_001_s1",
    "en": "to hit the nail on the head",
    "level": "C2",
    "register": "everyday",
    "example": "Mit seiner Analyse hat er den Nagel auf den Kopf getroffen.",
    "example_en": "With his analysis he has hit the nail on the head.",
    "collocations": []
  }]
}
```

### Proverb
```json
{
  "id": "uebung_meister_001",
  "lemma": "Übung macht den Meister.",
  "article": "",
  "plural": "",
  "pos": "proverb",
  "frequency": 5,
  "topics": ["daily-life"],
  "senses": [{
    "sense_id": "uebung_meister_001_s1",
    "en": "practice makes perfect",
    "level": "C2",
    "register": "literary",
    "example": "Übung macht den Meister.",
    "example_en": "Practice makes perfect.",
    "collocations": []
  }]
}
```

### Template (academic discourse marker)
```json
{
  "id": "im_hinblick_001",
  "lemma": "Im Hinblick auf ...",
  "article": "",
  "plural": "",
  "pos": "template",
  "frequency": 5,
  "topics": ["rhetoric"],
  "senses": [{
    "sense_id": "im_hinblick_001_s1",
    "en": "with regard to / in view of",
    "level": "C1",
    "register": "academic",
    "example": "Im Hinblick auf die Prüfung sollten wir mehr üben.",
    "example_en": "With regard to the exam, we should practise more.",
    "collocations": []
  }]
}
```

### Determiner
```json
{
  "id": "jeder_001",
  "lemma": "jeder/jede/jedes",
  "article": "",
  "plural": "",
  "pos": "determiner",
  "frequency": 1,
  "topics": ["daily-life"],
  "senses": [{
    "sense_id": "jeder_001_s1",
    "en": "every / each",
    "level": "A1",
    "register": "everyday",
    "example": "Jeder Schüler bekommt ein Heft.",
    "example_en": "Every pupil receives an exercise book.",
    "collocations": []
  }]
}
```

---

## Backward Compatibility — v2 → v1 Flattening

`build.py` converts v2 format back to v1 for HTML generation using `flatten_v2_to_v1()`:

```python
def flatten_v2_to_v1(v2_entries):
    """Convert lemma-centric v2 → entry-centric v1 for frontend."""
    v1 = []
    for entry in v2_entries:
        for sense in entry['senses']:
            # Reconstruct the v1 'de' field
            if entry['article'] and entry['plural']:
                de = f"{entry['article']} {entry['lemma']}, {entry['plural']}"
            elif entry['article']:
                de = f"{entry['article']} {entry['lemma']}"
            else:
                de = entry['lemma']

            v1.append({
                'de':          de,
                'en':          sense['en'],
                'level':       sense['level'],
                'register':    sense['register'],
                'example':     sense['example'],
                'example_en':  sense.get('example_en', ''),
                'collocations': sense.get('collocations', []),
                'article':     entry['article'],
            })
    return v1
```

This means:
- **dictionary.html** — continues to render word-cards from flat v1 data
- **01_Wortschatz.html** — continues to render tables from flat v1 data
- **tts.js** — no changes needed
- **No frontend file changes at all**

---

## Migration Steps (3–7) — Quick Reference

| Step | Task | Input | Output |
|------|------|-------|--------|
| 3 | Parse `de` → `lemma` / `article` / `plural` | `words_final.json` | `words_parsed.json` |
| 4 | Add `pos` to all entries | `words_parsed.json` | `words_with_pos.json` |
| 5 | Assign `topics[]` from taxonomy | `words_with_pos.json` | `words_with_topics.json` |
| 6 | Add `frequency` + validate CEFR | `words_with_topics.json` | `words_with_freq.json` |
| 7 | Merge duplicates → `senses[]`, build final v2 | `words_with_freq.json` | `words_v2.json` |

After Step 7: update `build.py` with `flatten_v2_to_v1()` and verify all HTML output is identical.

---

## Validation Rules

These checks must pass before v2 is accepted:

1. Every entry has `id`, `lemma`, `pos`, `frequency`, `topics` (≥1), `senses` (≥1)
2. Every sense has `sense_id`, `en`, `level`, `register`, `example`
3. `pos` is one of the 13 valid values
4. `level` is one of: `A1` `A2` `B1` `B2` `C1` `C2`
5. `register` is one of: `everyday` `colloquial` `formal` `academic` `literary`
6. `frequency` is 1–5
7. All `topics` tags are from the 28-tag controlled vocabulary
8. No duplicate `id` values
9. No duplicate `(lemma, pos)` pairs (multi-sense entries use `senses[]` instead)
10. `flatten_v2_to_v1()` output matches v1 entry count ± 5% (merges reduce count)
11. All HTML output identical to pre-migration (regression test)
