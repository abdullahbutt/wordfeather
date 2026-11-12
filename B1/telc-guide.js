/* "How does this page work?" for the five telc B1 practice pages (14 to 18).
   Adds a button above the page tabs. It opens a small panel at the bottom of the screen that walks through the steps one by one and,
   where the control exists on the page, scrolls to it and outlines it. English only. Nothing is stored. */
(function () {
    'use strict';

    function byText(sel, text) {
        return function () {
            var list = document.querySelectorAll(sel);
            for (var i = 0; i < list.length; i++) {
                if (list[i].offsetParent !== null && list[i].textContent.indexOf(text) !== -1) return list[i];
            }
            return null;
        };
    }
    function one(sel) { return function () { return document.querySelector(sel); }; }

    var TABS = '.rf-switch, .rf-tabs';
    var OPEN_FIRST = 'Open an exam first (Start), then this control appears inside the exam.';

    var GUIDES = {
        '14_telc_hoeren.html': [
            { t: 'Choose what you want', x: 'The three tabs at the top: Exams (take an exam), Solutions (every statement with the answer and the English), Tips & tricks. Start with Exams.', sel: one(TABS) },
            { t: 'Pick an exam', x: 'There are 17 listening exams, named by the first name on the recording. Press Start on a new one, Continue if you stopped, or Open again to repeat a finished one.', sel: byText('#tx-root a, #tx-root button', 'Start') },
            { t: 'Load the recording', x: 'Each exam has one YouTube video with all three Teile. Press “Load the YouTube video”, then play. Listen as in the real exam: the audio is played once. The answers are shown at the very end of the video, so do not skip to the end before you submit.', sel: one('.tx-audio'), n: OPEN_FIRST },
            { t: 'Start the clock', x: 'Press “▶ Start clock” when you press play. The clock also starts with your first answer.', sel: byText('button', 'Start clock'), n: OPEN_FIRST },
            { t: 'Mark the statements', x: 'On the answer sheet mark every statement + (richtig) or − (falsch). Each Teil has 20 statements. The 👁 eye shows the English of a statement, “Underline” lets you mark key words.', sel: byText('button', 'Underline'), n: OPEN_FIRST },
            { t: 'Submit a Teil', x: 'Press “✔ Submit Teil”. That Teil is marked at once with the correct answers and quotes from the recording. You can do the three Teile on different days. “Reset this Teil” clears it for another try.', sel: byText('button', 'Submit Teil'), n: OPEN_FIRST },
            { t: 'Submit the exam', x: '“Submit exam” gives the total. Your answers and results stay in this browser, so you can close the page and come back with Continue.', sel: byText('button', 'Submit exam'), n: OPEN_FIRST }
        ],
        '15_telc_lesen.html': [
            { t: 'Choose what you want', x: 'The three tabs at the top: Exams (take an exam), Solutions (every answer with a short explanation), Tips & tricks. Start with Exams.', sel: one(TABS) },
            { t: 'Pick an exam', x: 'There are 18 reading exams. Press Start on a new one, Continue if you stopped, or Open again to repeat a finished one.', sel: byText('#tx-root a, #tx-root button', 'Start') },
            { t: 'Three Teile, three clocks', x: 'Each exam has Teil 1, 2 and 3 with their own clocks of 15, 15 and 25 minutes. Press “▶ Start Teil” for the Teil you are on. The total clock of the exam starts with your first answer, or with “Start exam”. A + on a clock means you are over time.', sel: byText('button', 'Start Teil'), n: OPEN_FIRST },
            { t: 'Read and answer', x: 'Read the texts and choose your answers. The 👁 eye shows the English of a text, heading or question, and “Underline” lets you mark key words. The tricks for each Teil are above its questions.', sel: byText('button', 'Underline'), n: OPEN_FIRST },
            { t: 'Submit a Teil', x: 'Press “✔ Submit Teil”: the Teil is marked at once and locked. You see the correct answers and points, and “Why?” under an item explains it. “Try Teil again” clears it. You can do the Teile in any order and leave some for later.', sel: byText('button', 'Submit Teil'), n: OPEN_FIRST },
            { t: 'Submit the exam', x: '“Submit exam” stops the total time and gives the total. Your answers and results stay in this browser, so you can come back with Continue.', sel: byText('button', 'Submit exam'), n: OPEN_FIRST }
        ],
        '18_telc_sprachbausteine.html': [
            { t: 'Choose what you want', x: 'Two tabs: “Sprachbausteine exams” (practice exams) and “Grammar refresher”. For the exam, stay on Sprachbausteine exams.', sel: one(TABS) },
            { t: 'What the exam looks like', x: 'Teil 1: a text with 10 gaps, you choose a, b or c. Teil 2: a text with 10 gaps, you choose from a list of 15 words, each word only once.', sel: one('#t-sbexam') },
            { t: 'Read the cheat sheet first', x: 'Open “Cheat sheet: how to find the right word”. It gives four steps for every gap and the word types of the Teil 2 list.', sel: byText('summary', 'Cheat sheet') },
            { t: 'Start the clock', x: 'Press “▶ Start” on the Teil you work on and fill every gap. Teil 2: do the sure gaps first (verbs, articles) and the connector words last.', sel: byText('button', 'Start') },
            { t: 'Submit a Teil', x: 'Press Submit. The Teil is marked, and the box on the page shows what to work on first, which exams to redo and which part of the cheat sheet to read. Nothing leaves your device.', sel: byText('button', 'Submit') },
            { t: 'Meanings and English', x: '“Show meanings and word types” and “Show the English” help you after your own try. Use Reset to clear the clock and your answers for a Teil.', sel: byText('button', 'Show') }
        ],
        '16_telc_schreiben.html': [
            { t: 'Choose what you want', x: 'Four tabs: Exam & clock (practise the task), Worked examples, Week 1 to memorise, Templates. Start with Exam & clock.', sel: one(TABS) },
            { t: 'What the exam looks like', x: 'You get a letter or e-mail with 4 points you must answer. You have 30 minutes: 5 to plan, 18 to write, 7 to check. Write 2–3 sentences for each of the 4 points, about 120–160 words. No dictionary.', sel: one('#t-exam') },
            { t: 'Start the clock', x: 'Press “▶ Start”. The clock runs 30 minutes and shows the phase you should be in: Planen, Schreiben, Kontrollieren.', sel: byText('button', '▶ Start') },
            { t: 'Write your answer', x: 'Type in the practice area. The text stays in this browser. Use the checklist under it (Anrede, all 4 points, Schluss, verb at the end after dass/weil). “Copy text” copies your answer, “Clear” empties the box.', sel: one('#sc-copy') },
            { t: 'Learn the phrases', x: 'The Templates tab has openers and closings for letters. Worked examples show finished answers. Week 1 to memorise is a short list to learn by heart before the exam. In the real exam you write by hand.', sel: one(TABS) }
        ],
        '17_telc_sprechen.html': [
            { t: 'Choose what you want', x: 'Five tabs: Exam & clock, Teil 2 topic cards, Worked examples, Week 1 to memorise, Templates. Start with Exam & clock.', sel: one(TABS) },
            { t: 'What the exam looks like', x: 'You take it with a partner and it lasts about 15 minutes. Before it you have 20 minutes to prepare. Teil 1: get to know each other. Teil 2: present a card with one person’s opinion. Teil 3: plan something together.', sel: one('#t-exam') },
            { t: 'Prepare, then speak', x: 'Press “▶ Start” on the Preparation clock (20 minutes), then on the Speaking clock (about 15 minutes). At the end of each Teil press “Teil … done”: the page shows how long each Teil took.', sel: one('#pr-go') },
            { t: 'Practise Teil 2 with cards', x: 'The “Teil 2 topic cards” tab has 55 topics. Pick one or press “🎲 Random card”, read the two opinion cards and present one with the 6 openers from the Templates tab. Practise out loud or with a partner.', sel: one(TABS) },
            { t: 'Use the templates', x: 'The Templates tab has sentences for Teil 1, 2 and 3. Worked examples show a full conversation. Week 1 to memorise is a short list to learn by heart.', sel: one(TABS) }
        ]
    };

    var file = location.pathname.split('/').pop();
    var steps = GUIDES[file];
    if (!steps) return;

    var css = document.createElement('style');
    css.textContent =
        '.tg-open{margin:.25rem 0 .75rem}' +
        '.tg-panel{position:fixed;left:50%;transform:translateX(-50%);bottom:.75rem;z-index:1060;width:min(34rem,calc(100% - 1.5rem));max-height:46vh;overflow:auto;' +
        'background:var(--bs-body-bg,#fff);color:var(--bs-body-color,#212529);border:2px solid var(--bs-primary,#1d4ed8);border-radius:.8rem;padding:.8rem 1rem;box-shadow:0 8px 28px rgba(0,0,0,.3)}' +
        '.tg-panel[hidden]{display:none}' +
        '.tg-step{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--bs-secondary-color,#6c757d)}' +
        '.tg-title{font-size:1.05rem;font-weight:700;margin:.1rem 0 .3rem}' +
        '.tg-text{margin:0 0 .4rem;line-height:1.45}' +
        '.tg-note{margin:0 0 .4rem;font-size:.85rem;color:var(--bs-secondary-color,#6c757d)}' +
        '.tg-row{display:flex;gap:.4rem;justify-content:space-between;margin-top:.5rem}' +
        '.tg-hl{outline:3px solid #f59e0b !important;outline-offset:3px;border-radius:.4rem;box-shadow:0 0 0 6px rgba(245,158,11,.25) !important}' +
        '@media print{.tg-open,.tg-panel{display:none !important}}';
    document.head.appendChild(css);

    var panel = document.createElement('div');
    panel.className = 'tg-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'How this page works');
    panel.setAttribute('lang', 'en');
    panel.hidden = true;
    panel.innerHTML =
        '<div class="tg-step"></div><div class="tg-title" tabindex="-1"></div><p class="tg-text"></p><p class="tg-note" hidden></p>' +
        '<div class="tg-row"><button type="button" class="btn btn-sm btn-outline-secondary tg-prev">← Back</button>' +
        '<button type="button" class="btn btn-sm btn-outline-secondary tg-close">Close</button>' +
        '<button type="button" class="btn btn-sm btn-primary tg-next">Next →</button></div>';
    document.body.appendChild(panel);

    var q = function (s) { return panel.querySelector(s); };
    var idx = 0, marked = null;

    function unmark() { if (marked) { marked.classList.remove('tg-hl'); marked = null; } }

    function show(i) {
        idx = Math.max(0, Math.min(steps.length - 1, i));
        var s = steps[idx];
        unmark();
        q('.tg-step').textContent = 'Step ' + (idx + 1) + ' of ' + steps.length;
        q('.tg-title').textContent = s.t;
        q('.tg-text').textContent = s.x;
        var el = s.sel ? s.sel() : null;
        var note = q('.tg-note');
        note.hidden = !(s.n && !el);
        note.textContent = s.n || '';
        if (el) {
            marked = el;
            el.classList.add('tg-hl');
            el.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }
        q('.tg-prev').disabled = idx === 0;
        var last = idx === steps.length - 1;
        q('.tg-next').textContent = last ? 'Done' : 'Next →';
    }

    function open() { panel.hidden = false; show(0); q('.tg-title').focus({ preventScroll: true }); }
    function close() { panel.hidden = true; unmark(); if (opener) opener.focus(); }

    q('.tg-prev').addEventListener('click', function () { show(idx - 1); });
    q('.tg-next').addEventListener('click', function () { if (idx === steps.length - 1) close(); else show(idx + 1); });
    q('.tg-close').addEventListener('click', close);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !panel.hidden) close(); });

    var opener = null;
    var tries = 0;
    var timer = setInterval(function () {
        var anchor = document.querySelector(TABS);
        if (anchor || ++tries > 50) {
            clearInterval(timer);
            opener = document.createElement('button');
            opener.type = 'button';
            opener.className = 'btn btn-sm btn-primary tg-open';
            opener.setAttribute('lang', 'en');
            opener.textContent = '▶ How does this page work? Step-by-step demo';
            opener.addEventListener('click', open);
            if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(opener, anchor);
            else { var h = document.querySelector('h1'); (h ? h.parentNode : document.body).insertBefore(opener, h ? h.nextSibling : document.body.firstChild); }
        }
    }, 200);
})();
