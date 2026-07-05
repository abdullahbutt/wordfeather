"""
Master list of genuine English irregular verbs found among the 292
German verbs' translations, plus monosyllabic-doubling cases (BrEng)
and British-spelling corrections. Built by reviewing all 242 distinct
first-word bases extracted from the dataset.

Format: {base_word: (irregular_past, irregular_participle_or_None)}
If participle is None, it's identical to the past tense (most regular
irregulars: bring/brought/brought).
"""

IRREGULAR_PAST = {
    # 'be' as the first word of a phrasal modal-style construction
    # ('be allowed to', 'be missing', 'be called', 'be happy'...) —
    # sein itself gets its own full override since 'to be' varies by
    # ALL persons in present tense (am/is/are), not just he/she/it;
    # this entry covers every OTHER verb whose English gloss happens
    # to start with 'be' as an auxiliary-style construction.
    'be':         ('was', 'been'),

    # True irregulars (past != base+ed)
    'become':     ('became', 'become'),
    'begin':      ('began', 'begun'),
    'break':      ('broke', 'broken'),
    'bring':      ('brought', None),
    'broadcast':  ('broadcast', None),
    'buy':        ('bought', None),
    'choose':     ('chose', 'chosen'),
    'come':       ('came', 'come'),
    'cost':       ('cost', None),
    'cut':        ('cut', None),
    'deal':       ('dealt', None),
    'do':         ('did', 'done'),
    'drink':      ('drank', 'drunk'),
    'drive':      ('drove', 'driven'),
    'eat':        ('ate', 'eaten'),
    'fall':       ('fell', 'fallen'),
    'feel':       ('felt', None),
    'find':       ('found', None),
    'fly':        ('flew', 'flown'),
    'forbid':     ('forbade', 'forbidden'),
    'forget':     ('forgot', 'forgotten'),
    'get':        ('got', None),
    'give':       ('gave', 'given'),
    'go':         ('went', 'gone'),
    'grow':       ('grew', 'grown'),
    'hang':       ('hung', None),          # physical-object sense; 'hanged' is only for the execution sense
    'have':       ('had', None),
    'hold':       ('held', None),
    'hurt':       ('hurt', None),
    'keep':       ('kept', None),
    'know':       ('knew', 'known'),
    'leave':      ('left', None),
    'let':        ('let', None),
    'lie':        ('lay', 'lain'),          # liegen = to lie/be situated
    'lose':       ('lost', None),
    'make':       ('made', None),
    'mean':       ('meant', None),
    'meet':       ('met', None),
    'overcome':   ('overcame', 'overcome'),
    'pay':        ('paid', None),
    'put':        ('put', None),
    'read':       ('read', None),           # spelling unchanged, pronunciation differs
    'ride':       ('rode', 'ridden'),
    'run':        ('ran', 'run'),
    'say':        ('said', None),
    'see':        ('saw', 'seen'),
    'sell':       ('sold', None),
    'send':       ('sent', None),
    'show':       ('showed', 'shown'),
    'sing':       ('sang', 'sung'),
    'sit':        ('sat', None),
    'sleep':      ('slept', None),
    'speak':      ('spoke', 'spoken'),
    'spend':      ('spent', None),
    'stand':      ('stood', None),
    'swim':       ('swam', 'swum'),
    'take':       ('took', 'taken'),
    'teach':      ('taught', None),
    'tell':       ('told', None),
    'think':      ('thought', None),
    'throw':      ('threw', 'thrown'),
    'understand': ('understood', None),
    'win':        ('won', None),
    'write':      ('wrote', 'written'),
    'withdraw':   ('withdrew', 'withdrawn'),
    'ring':       ('rang', 'rung'),
    'stink':      ('stank', 'stunk'),

    # Monosyllabic (or final-syllable-stressed) consonant doubling,
    # BrEng — 'stop' -> 'stopped', not the plain -ed rule's 'stoped'
    'stop':       ('stopped', None),
    'shop':       ('shopped', None),
    'jog':        ('jogged', None),
    'fit':        ('fitted', None),
    'transfer':   ('transferred', None),
    'plan':       ('planned', None),

    # Explicit exceptions to the general vowel+l doubling rule below:
    # 'fail'/'prevail' end in a diphthong (ai) + l, which looks
    # identical at the letter level to genuine schwa+l doubling verbs
    # (cancel, travel, equal, refuel) but must NOT double — English
    # doesn't reliably distinguish these by spelling pattern alone, so
    # these are corrected here as known exceptions rather than via a
    # regex refinement that would risk breaking the correct cases.
    'fail':       ('failed', None),
    'prevail':    ('prevailed', None),
}

# British spelling corrections (regular grammar, American -ize/-or
# spelling swapped to -ise/-our per this project's existing convention)
BRITISH_SPELLING_BASE = {
    'apologize':  'apologise',
    'favor':      'favour',
    'legitimize': 'legitimise',
    'practice':   'practise',   # verb spelling; noun stays 'practice'
    'recognize':  'recognise',
    'summarize':  'summarise',
}

# Irregular he/she/it present forms beyond the standard -s/-es rule
# ('do'->'does' and 'go'->'goes' are already correctly handled by the
# existing consonant+o -> -es rule, so aren't needed here).
PRESENT_HE_IRREGULAR = {
    'have': 'has',
    'be':   'is',
}
