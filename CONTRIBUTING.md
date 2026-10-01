# Contributing

Thank you for helping improve these German learning materials! Contributions of all kinds are welcome — from fixing a typo to adding new practice exercises.

## Ways to contribute

- **Fix errors** — grammar mistakes, incorrect translations, or wrong exam format details
- **Improve explanations** — clearer wording, better examples, additional context
- **Add exercises** — new vocabulary, grammar drills, or sample exam questions
- **Report issues** — something confusing or missing? Open an issue and describe it

## How to contribute

1. **Fork** this repository
2. **Make your changes** in your forked copy
3. **Submit a Pull Request** with a clear description of what you changed and why

For small fixes (typos, broken links), a Pull Request is enough. For larger changes (new files, restructuring), please open an **Issue** first to discuss the idea before investing time in it.

## Where things live

- **Vocabulary** is stored in `words_final.json` (structure: [SCHEMA.md](SCHEMA.md)). The dictionary and the Wortschatz pages are generated from it, so fix a word or a translation there rather than in the generated HTML. After editing, run `python3 build.py --audit` to check the data, then `python3 build.py --all` to regenerate the pages.
- **Other level content** (Grammatik, Sätze, Lesen, Hören, Sprechen, Schreiben, Musterprüfung, telc format) is plain HTML in the level folders (`A1/` … `C2/`) and can be edited directly.
- The original Markdown versions of the level materials are no longer maintained; they are kept in the `v1.0.0` tag for reference only.

## Guidelines

- Keep the bilingual approach consistent — A1, A2, B1 pages should include English alongside German; B2, C1, C2 pages should be German only (with English only in vocabulary tables)
- Match the existing file naming convention (`01_Wortschatz.html`, `02_Grammatik.html` etc.)
- Stick to the Goethe-Zertifikat exam format — content should align with official exam standards
- Use clear, learner-friendly language appropriate to the level
- Contributions are published under the project's license (CC BY-NC 4.0)

## Reporting mistakes

If you spot an error but don't want to submit a Pull Request, simply open an **Issue** and describe the problem. Every correction helps future learners.

---

Danke für deine Hilfe! 🇩🇪
