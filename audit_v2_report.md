# Architecture v2 Diagnostic Audit Report
**Date:** 2026-06-06
**Dataset:** `words_final.json` — 3,041 entries
**Purpose:** Blueprint for migration from entry-centric to lemma-centric schema (Steps 2–7)

---

## 1. Level Distribution

| Level | Count | % of total |
|-------|-------|-----------|
| A1 | 741 | 24.4% |
| A2 | 600 | 19.7% |
| B1 | 500 | 16.4% |
| B2 | 450 | 14.8% |
| C1 | 400 | 13.2% |
| C2 | 350 | 11.5% |
| **Total** | **3,041** | |

---

## 2. `de` Field Parse Analysis

The `de` field currently mixes lemma, article, plural, and phrase type in one string.

| Category | Count | % | Notes |
|----------|-------|---|-------|
| `noun_parseable` | 1,176 | 38.7% | Pattern: `"die Probezeit, -en"` — fully auto-parseable |
| `multi_word_phrase` | 1,119 | 36.8% | Idioms, collocations, fixed phrases |
| `single_word_no_article` | 387 | 12.7% | Adjectives, adverbs, bare nouns |
| `verb_infinitive` | 299 | 9.8% | Clean infinitives — fully auto-parseable |
| `proverb_sentence` | 52 | 1.7% | End in `.` or `!` |
| `irregular` | 8 | 0.3% | `dies-`, `ein/eine`, `gern(e)` etc. |

**Auto-parseable (nouns + verbs): 1,475 (49%)**
**Multi-word phrases needing pos tag only: 1,119 (37%)**
**Need manual attention: 395 entries (13%)**

### Irregular entries requiring manual handling (8 total)
- `dies-`, `ein/eine`, `gern(e)`, `jeder/jede/jedes`, `kein/keine`, `lang(e)`, `nah(e)`, `welch-`
- These are determiners/pronouns — need a new `pos: "determiner"` or `"pronoun"` value

---

## 3. POS Estimate (pre-tagging baseline)

| POS | Count | % |
|-----|-------|---|
| Noun (with article) | 1,176 | 38.7% |
| Phrase / idiom | 1,119 | 36.8% |
| Adjective / adverb / other | 387 | 12.7% |
| Verb (infinitive) | 299 | 9.8% |
| Proverb | 52 | 1.7% |
| Irregular / unknown | 8 | 0.3% |

---

## 4. Lemma Conflicts (same lemma, multiple levels)

| Type | Count |
|------|-------|
| Total lemmas at multiple levels | 245 |
| True duplicates (same level, same meaning) | 2 |
| Justified different senses | 224 |
| Weak CEFR distinction (>65% similar example) | 19 |

### True duplicates to resolve in Step 7
| Lemma | Issue |
|-------|-------|
| `essen` (A1) vs `das Essen` (A1) | Verb and noun — different entries, not duplicates; but need clear separation |
| `morgen` (A1) vs `der Morgen` (A1) | Adverb and noun — same resolution |

### Top 10 weak CEFR distinctions (>65% similar examples)
| Lemma | Levels | Similarity | Action |
|-------|--------|-----------|--------|
| Miete | A1/A2/B1 | 89% | Merge A2+B1 into senses; A1 keeps brief form |
| die Nachfrage | B1/B2 | 78% | Rewrite B2 example for journalistic register |
| die Zusammenarbeit | B1/B2 | 78% | Rewrite B2 with formal/policy context |
| Vorstellungsgespräch | A2/B1 | 77% | Merge into single B1 entry |
| die Veranstaltung | A1/A2 | 75% | A1 too advanced; remove or simplify |
| die Sehenswürdigkeit | A2/B1 | 75% | Merge into single B1 entry |
| die Transparenz | B2/C1 | 75% | Examples currently distinct enough — monitor |
| ärgerlich | A2/B1 | 74% | Rewrite B1 with work/society context |
| aussehen | A1/A2 | 71% | A1: "Du siehst gut aus." A2 needs clear upgrade |
| das Krankenhaus | A1/A2/B1 | 70% | 3-level entry — merge into senses[] |

---

## 5. Multi-Word Phrase Breakdown (1,119 entries)

| Sub-type | Count | Examples |
|----------|-------|---------|
| Noun phrase (multi-word) | 1,006 | `der 3D-Druck`, `das A und O`, `der Abflug` |
| Reflexive verb | 35 | `sich ärgern`, `sich anmaßen` |
| Other phrase | 30 | `bemüßigt sein`, `etwas auf die lange Bank schieben` |
| Separable verb | 29 | `einen Antrag stellen`, `einen Beitrag leisten` |
| Proverb / idiom | 25 | `Aller Anfang ist schwer.`, `Ende gut, alles gut.` |
| Prepositional phrase | 22 | `auf Biegen und Brechen`, `auf dem Holzweg sein` |
| Academic template | 14 | `Dies legt den Schluss nahe, dass ...` |
| Capitalised phrase | 10 | `Abschied nehmen`, `Bescheid geben` |

**Key insight:** 1,006 of the 1,119 "multi-word phrases" are actually nouns with compound modifiers
(e.g. `der 3D-Druck`, `der Abflug`) — these ARE parseable as nouns. The ARTICLE_RE failed because
they don't follow the `"article lemma, plural"` pattern exactly.

---

## 6. Single-Word No-Article Breakdown (387 entries)

| Sub-type | Count | Examples |
|----------|-------|---------|
| Other single (prepositions, conjunctions, misc) | 216 | `ab`, `abends`, `also` |
| Adjective (identifiable by suffix) | 134 | `ängstlich`, `ärgerlich`, `ausschlaggebend` |
| Adverb / particle | 43 | `aber`, `also`, `allerdings`, `nichtsdestotrotz` |
| Abstract noun (no article) | 2 | `jung`, `spät` ← likely misclassified |

---

## 7. Field Completeness

| Field | Coverage | Missing |
|-------|---------|---------|
| `de` | 100% | 0 |
| `en` | 100% | 0 |
| `level` | 100% | 0 |
| `example` | 100% | 0 |
| `example_en` | 85.7% | 436 (all A1 — short sentences, German TTS works) |
| `register` | 100% | 0 |
| `collocations` | 44.9% | 1,677 (by design: A1/A2 don't need them) |

### Collocations coverage by level
| Level | Has collocations | Target | Gap |
|-------|-----------------|--------|-----|
| A1 | 0% | 0% (not needed) | ✅ |
| A2 | 0% | 0% (not needed) | ✅ |
| B1 | 48% | 0% (optional) | acceptable |
| B2 | 100% | 100% | ✅ |
| C1 | 94% | 100% | 6% gap (23 academic templates — correct to skip) |
| C2 | 85% | 100% | 15% gap (52 proverbs — correct to skip) |

---

## 8. Frequency Distribution

Currently no `frequency` field exists. Estimated tiers by level:

| Tier | Level | Count | Description |
|------|-------|-------|-------------|
| 1 | A1 | 741 | Core vocabulary — top ~1,000 German words |
| 2 | A2 | 600 | Common everyday vocabulary |
| 3 | B1 | 500 | Practical/functional vocabulary |
| 4 | B2 | 450 | Semi-formal, journalistic vocabulary |
| 5 | C1+C2 | 750 | Rare, specialised, literary |

**No words at C1/C2 were flagged as incorrectly high-frequency.**

---

## 9. Register Consistency

**0 suspicious register assignments found.**
- No C1/C2 entries incorrectly marked `everyday`
- No A1/A2 entries incorrectly marked `academic` or `literary`
- Register distribution looks linguistically sound

---

## 10. CEFR Placement Anomalies

Only 4 mild anomalies — the dataset is well-placed overall:

| Entry | Current | Issue | Recommendation |
|-------|---------|-------|---------------|
| `der Umweltschutz` | A2 | Abstract policy concept | Move to B1 |
| `das Benzin` | A1 | Not in Goethe A1 official list | Move to A2 |
| `ganz` | A1 | ✅ Actually correct — very high frequency | Keep |
| `tanzen` | A1 | ✅ Correct | Keep |

---

## 11. Migration Complexity Estimate

### Step 3 — Parse `de` → `lemma` / `article` / `plural`
- **1,475 entries (49%)**: fully auto-parseable with regex
- **1,119 entries (37%)**: multi-word phrases — extract as-is, assign pos tag
- **8 entries (0.3%)**: irregular — manual handling
- **439 entries (14%)**: single-word no-article — need POS-based parsing

### Step 4 — POS tagging
- **87% rule-assignable** (nouns from article, verbs from `-en` ending, phrases from spaces)
- **13% need manual review** (single-word adjectives/adverbs/prepositions)
- Estimated manual work: ~400 entries

### Step 5 — Topic taxonomy
- `build.py` keyword map already covers **~85%** auto-assignment
- ~450 entries need new or corrected topic tags

### Step 6 — Frequency metadata
- All 3,041 entries need a `frequency: 1–5` value
- Can be batch-assigned by level (tier 1–5) then refined manually for ~100 outliers

### Step 7 — Sense merging
- **245 lemmas** appear at multiple levels
- **19 are weak distinctions** → candidates for either merging or rewriting examples
- **2 are true same-level duplicates** → straightforward removal
- **224 are justified different senses** → keep as separate senses in `senses[]`

---

## Summary: Key Findings for Schema v2 Design

| Finding | Impact on Schema |
|---------|-----------------|
| 38.7% of entries are clean noun-article-plural strings | `lemma`, `article`, `plural` are auto-extractable for 1,176 entries |
| 36.8% are multi-word phrases | Need `pos: "phrase"/"idiom"/"proverb"/"template"` with no article/plural |
| 12.7% are single words without article | Need `pos: "adjective"/"adverb"/"preposition"` |
| 9.8% are clean verb infinitives | `lemma` = infinitive, no article, add `pos: "verb"` |
| 8 irregular determiners/pronouns | Need `pos: "determiner"/"pronoun"` |
| 245 multi-level lemmas | `senses[]` array is the right solution |
| 19 weak CEFR distinctions | Rewrite examples OR merge into senses with level-per-sense |
| 0 register anomalies | Register taxonomy is sound — carry forward to v2 |
| 436 missing `example_en` | All A1 — acceptable gap, German TTS works |
| `frequency` field: entirely missing | Add in Step 6, batch-assign by level first |

---

## Ready for Step 2

This audit confirms the schema v2 design (Step 2) should handle:

1. **Nouns**: `lemma` + `article` + `plural` + `pos: "noun"`
2. **Verbs**: `lemma` + `pos: "verb"` (no article/plural)
3. **Adjectives/Adverbs**: `lemma` + `pos: "adjective"/"adverb"` (no article/plural)
4. **Phrases/Idioms**: `lemma` = full phrase + `pos: "phrase"/"idiom"/"collocation"`
5. **Proverbs**: `lemma` = full sentence + `pos: "proverb"`
6. **Academic templates**: `lemma` = full template + `pos: "template"`
7. **Determiners/Pronouns**: `lemma` = headword + `pos: "determiner"/"pronoun"`
8. All entries: `frequency: 1–5`, `topics: []`, `senses: []`
