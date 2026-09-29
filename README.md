<div align="center">

[![GitHub Stars](https://img.shields.io/github/stars/abdullahbutt/wordfeather?style=for-the-badge&logo=github&label=Star%20this%20Repo)](https://github.com/abdullahbutt/wordfeather)
&nbsp;&nbsp;
[![View Website](https://img.shields.io/badge/🌐_Use_the_Website-wordfeather.com-blue?style=for-the-badge)](https://wordfeather.com/)

</div>

# 🪶 WordFeather — Deutsch Lernen / Goethe-Zertifikat Vorbereitung
# 🇩🇪 Learn German — Goethe Certificate Preparation

**👉 Most people should just use [wordfeather.com](https://wordfeather.com/) — no need to browse this repo's files.**
*Die meisten sollten einfach [wordfeather.com](https://wordfeather.com/) benutzen — ein Durchstöbern dieses Repos ist nicht nötig.*

This repository is the source material behind [wordfeather.com](https://wordfeather.com/): a free, open-source study platform for all CEFR levels (A1–C2) preparing for the Goethe and telc exams. The website is the finished, interactive product — searchable, with audio, and installable as an app. The files in this repo are the raw content it's built from, useful if you want to read offline, fork it, or contribute.

---

## 🌐 What's on wordfeather.com

| Tool | What it does |
|---|---|
| [📖 Dictionary](https://wordfeather.com/dictionary.html) | 5,243 words and phrases, A1–C2, searchable in German or English, with audio pronunciation, example sentences, collocations and full verb conjugation tables |
| [🎯 Quiz](https://wordfeather.com/quiz.html) | Vocabulary practice with spaced repetition, Hörverstehen (listening) and Leseverstehen (reading) exercises, and a "find my level" placement test |
| [📚 A1–C2 level pages](https://wordfeather.com/) | Every level's vocabulary, grammar, example sentences, reading, listening, speaking, writing, a full sample exam, and the telc exam format — as browsable pages, most with audio pronunciation built in |
| [🇩🇪 leben.wordfeather.com](https://leben.wordfeather.com/) | A companion site for the "Leben in Deutschland" (German citizenship) test |

No login, no ads, works offline as an installable app (PWA).

---

## 📂 What's in this repo

Each level folder (`A1/` … `C2/`) contains the source content for that level's pages on the site:

| File | Content | On the site as |
|---|---|---|
| `01_Wortschatz.md` | Vocabulary, organized by theme | part of the live [Dictionary](https://wordfeather.com/dictionary.html), plus the level's own Wortschatz page |
| `02_Grammatik.md` | Grammar rules, tables, exercises | the level's Grammatik page, and [grammar-quiz.html](https://wordfeather.com/grammar-quiz.html) |
| `03_Saetze.md` | Example sentences, A–Z | the level's Sätze page |
| `04_Lesen.md` | Reading comprehension, Goethe-format | the level's Lesen page, and the Quiz's Leseverstehen mode |
| `05_Hoeren.md` | Listening exercises, transcripts | the level's Hören page, and the Quiz's Hörverstehen mode |
| `06_Sprechen.md` | Speaking prompts and Redemittel | the level's Sprechen page, with audio |
| `07_Schreiben.md` | Writing tasks with model answers | the level's Schreiben page |
| `08_Musterpruefung.md` | A complete sample exam with answer key | the level's Musterprüfung page |
| `09_telc_Pruefungsformat.md` | telc exam format, task types, scoring | the level's own page |

Each `.md` file has a matching `.html` file — that's the actual page the site serves; the Markdown is the plain-text source it's generated from. A few levels also have extra pages not listed above (e.g. course notes, a cheat sheet) — open a level's `index.html` or visit its page on the site to see everything available for it.

**5,243 vocabulary entries · 6 levels · all 4 exam skills, every level**

---

## 🎯 Exam format overview

### Goethe-Zertifikat A1: Start Deutsch 1
- **Lesen** (25 min) · **Hören** (20 min) · **Schreiben** (20 min) · **Sprechen** (15 min)

### Goethe-Zertifikat A2
- **Lesen** (30 min) · **Hören** (30 min) · **Schreiben** (30 min) · **Sprechen** (15 min)

### Goethe-Zertifikat B1
- **Lesen** (65 min) · **Hören** (40 min) · **Schreiben** (60 min) · **Sprechen** (15 min)

### Goethe-Zertifikat B2
- **Lesen** (65 min) · **Hören** (40 min) · **Schreiben** (75 min) · **Sprechen** (15 min)

### Goethe-Zertifikat C1
- **Lesen** (70 min) · **Hören** (40 min) · **Schreiben** (80 min) · **Sprechen** (15 min)

### Goethe-Zertifikat C2: GDS
- **Lesen** (80 min) · **Hören** (35 min) · **Schreiben** (80 min) · **Sprechen** (15 min)

---

## 📖 Vocabulary and grammar by level

### Wortschatz / Vocabulary
| Level | Words | Themes |
|---|---|---|
| A1 | 2,024 | Alphabetisch A–Z: Alltag, Familie, Essen, Körper, Verkehr |
| A2 | 932 | 12 Themen: Wohnen, Gesundheit, Arbeit, Reisen, Einkaufen, Behörden |
| B1 | 1,099 | 10 Themen: Gesellschaft, Medien, Karriere, Umwelt, Bildung, Gefühle |
| B2 | 446 | 10 Themen: Politik, Wissenschaft, Wirtschaft, Kultur, Recht, Psychologie + Kollokationen |
| C1 | 408 | 9 Themen: Akademie, Diplomatie, Philosophie, Biotechnologie + Stilistische Wendungen |
| C2 | 334 + Idiome | Literarisch, Akademisch, Rhetorik + 29 Redewendungen + 16 Sprichwörter |

### Grammatik / Grammar
| Level | Focus Areas |
|---|---|
| A1 | Artikel, Präsens, Perfekt, Modalverben, Satzstruktur, Imperativ, Präpositionen |
| A2 | Präteritum, Nebensätze (weil, dass, wenn, obwohl), Komparativ/Superlativ, Reflexivverben, Dativverben, Konjunktiv II (Höflichkeit) |
| B1 | Konjunktiv II (irreal), Passiv, Relativsätze, Genitiv, Infinitiv mit "zu", Plusquamperfekt, Zweiteilige Konnektoren |
| B2 | Partizipialkonstruktionen, Nominalisierung, Subjektive Modalverben, Passiversatzformen, Erweiterte Konnektoren |
| C1 | Funktionsverbgefüge, Modalpartikeln, Konjunktiv I (indirekte Rede), Textgrammatik, Nominalstil |
| C2 | Komplexe Satzgefüge, Stilregister, Verbalperiphrasen, Spaltsätze, Ausklammerung |

---

## 🌍 Bilingual approach

| Levels | Language | Reason |
|---|---|---|
| **A1, A2, B1** | German + English | Beginners need English to understand explanations and tips |
| **B2, C1, C2** | German only (English only in vocab tables) | Advanced learners benefit from immersion |

---

## 💡 Study tips

1. **Täglich lernen** — Regelmäßigkeit ist wichtiger als Dauer. *Consistency matters more than duration.*
2. **Wortschatz im Kontext** — Lerne Wörter in Sätzen, nicht isoliert. *Learn words in sentences, not in isolation.*
3. **Alle vier Fertigkeiten üben** — Lesen, Hören, Sprechen, Schreiben. *Practice all four skills.*
4. **Prüfungsformat kennen** — Übe mit den Modelltests. *Know the exam format.*
5. **Deutsche Medien nutzen** — Podcasts, Filme, Bücher, Nachrichten. *Use German media.*

---

## 🔗 Useful resources

- [Goethe-Institut Prüfungen](https://www.goethe.de/de/spr/kup/prf.html)
- [Deutsche Welle Deutschkurse](https://www.dw.com/de/deutsch-lernen/s-2055)
- [Hueber Verlag](https://www.hueber.de/)

---

**Viel Erfolg beim Lernen! / Good luck with your studies!** 🍀

## ☕ Support this project
*If these materials helped you, consider buying me a coffee to keep this project free for everyone!*

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?logo=paypal&style=for-the-badge)](https://www.paypal.com/paypalme/abdullahbuttde)

---

## License

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

This project is licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.

**You are free to:** use, share and adapt this content for personal learning, classroom teaching and non-commercial projects — as long as you give credit.

**You may not:** sell this content, include it in a paid product or service, or use it commercially without written permission.

© 2024–2026 [Abdullah Butt](https://github.com/abdullahbutt) · [Full license text](LICENSE) · Commercial enquiries: [open a GitHub Issue](https://github.com/abdullahbutt/wordfeather/issues)
