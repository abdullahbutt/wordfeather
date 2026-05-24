# Vocabulary Schema — words_final.json

This document defines the canonical schema for every entry in `words_final.json`,
the single source of truth for all vocabulary in this project.
To regenerate all pages from this file, run:

```bash
python3 build.py           # rebuild Wortschatz pages + update dictionary counts
python3 build.py --audit   # quality audit only
```

---

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `de` | string | ✅ | German word with article and plural marker, e.g. `"die Probezeit, -en"` |
| `en` | string | ✅ | English translation, e.g. `"probationary period"` |
| `level` | string | ✅ | CEFR level: `A1` `A2` `B1` `B2` `C1` `C2` |
| `example` | string | ✅ | German example sentence demonstrating natural usage |
| `example_en` | string | ⚠️ | English translation of the example sentence (empty for some A1 entries) |
| `register` | string | ✅ | Usage register — see valid values below |
| `collocations` | array | B2–C2 | 2–3 natural German collocations (verb+noun, adj+noun, fixed phrases) |
| `article` | string | ○ | Article if applicable: `"der"` `"die"` `"das"` — usually embedded in `de` |

---

## Field: `de` — Format Conventions

- Nouns include article and plural marker: `"die Probezeit, -en"`, `"das Kind, -er"`, `"der Mann, -̈er"`
- Verbs in infinitive: `"bezahlen"`, `"umsteigen"`
- Fixed phrases / idioms: `"Maßnahmen ergreifen"`, `"in Betracht ziehen"`
- Proverbs: full sentence as-is: `"Übung macht den Meister."`
- Academic templates: `"Im Hinblick auf ..."`, `"Es lässt sich nicht bestreiten, dass ..."`

---

## Field: `level` — Valid Values

| Value | Name | Register focus | Target exam |
|-------|------|----------------|-------------|
| `A1` | Beginner | Everyday, concrete | Goethe A1 / Start Deutsch 1 |
| `A2` | Elementary | Everyday, practical | Goethe A2 / Start Deutsch 2 |
| `B1` | Intermediate | Practical, society, work | Goethe B1 / Einbürgerungstest |
| `B2` | Upper-Intermediate | Journalistic, semi-formal | Goethe B2 / telc B2 |
| `C1` | Advanced | Formal, academic, policy | Goethe C1 / DSH / TestDaF |
| `C2` | Mastery | Nuanced, idiomatic, literary | Goethe C2 |

---

## Field: `register` — Valid Values

| Value | Meaning | Typical levels |
|-------|---------|----------------|
| `everyday` | Natural spoken or written everyday language | A1–B1 |
| `formal` | Professional, official, journalistic | B2–C1 |
| `academic` | Scientific, scholarly, research language | C1 |
| `literary` | Idiomatic, rhetorical, poetic | C2 |

---

## Field: `collocations` — Format

An array of 2–3 strings. Each string is a natural German collocation:
- Verb + noun: `"eine Entscheidung treffen"`, `"Maßnahmen ergreifen"`
- Adjective + noun: `"weitreichende Folgen"`, `"grundlegende Veränderung"`
- Fixed phrase: `"in Betracht ziehen"`, `"zur Verfügung stellen"`
- Noun + verb: `"Kritik üben"`, `"Transparenz herstellen"`

**Collocations are required for all B2, C1, C2 entries.**
A1, A2, B1 entries do not require collocations.

---

## Example Entry — B1

```json
{
  "de": "die Probezeit, -en",
  "en": "probationary period",
  "level": "B1",
  "register": "everyday",
  "example": "Während der Probezeit lernt man die Kolleginnen und Kollegen gut kennen.",
  "example_en": "During the probationary period you get to know your colleagues well.",
  "collocations": [
    "die Probezeit bestehen",
    "sich bewähren",
    "Probezeit verlängern"
  ],
  "article": ""
}
```

## Example Entry — C1

```json
{
  "de": "die Rechtsstaatlichkeit",
  "en": "rule of law",
  "level": "C1",
  "register": "formal",
  "example": "Die Rechtsstaatlichkeit ist die Grundlage jeder stabilen Demokratie.",
  "example_en": "The rule of law is the foundation of every stable democracy.",
  "collocations": [
    "Rechtsstaatlichkeit wahren",
    "demokratische Kontrolle",
    "Gewaltenteilung"
  ],
  "article": ""
}
```

## Example Entry — C2 (proverb)

```json
{
  "de": "Übung macht den Meister.",
  "en": "practice makes perfect",
  "level": "C2",
  "register": "literary",
  "example": "Übung macht den Meister.",
  "example_en": "Practice makes perfect.",
  "collocations": [],
  "article": ""
}
```

---

## Quality Rules

These rules are enforced by `python3 build.py --audit`:

1. **No duplicates** — each `(de.lower(), level)` pair must be unique
2. **No empty `de`, `en`, `level`, `example`** — all required fields must be non-empty
3. **No German characters in `example_en`** — ä ö ü Ä Ö Ü ß must not appear in the EN field
4. **No generic examples** — banned patterns: `"das Thema betrifft"`, `"Wir sprechen über"`, `"ist sehr wichtig"`, `"hat sich verändert"`, `"ich interessiere mich für"`
5. **Collocations coverage** — B2, C1, C2 entries must have collocations (target: ≥ 80%)
6. **Register field** — all entries must have one of the four valid register values

---

## Adding New Entries

1. Add the entry to `words_final.json` following the schema above
2. Run `python3 build.py --audit` to check for issues
3. Run `python3 build.py` to regenerate all Wortschatz pages
4. Commit both `words_final.json` and the regenerated HTML files

---

## Level Counts (current)

| Level | Count |
|-------|-------|
| A1 | 741 |
| A2 | 600 |
| B1 | 500 |
| B2 | 450 |
| C1 | 400 |
| C2 | 350 |
| **Total** | **3,041** |
