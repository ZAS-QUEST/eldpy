LGRLIST = set(
    [
        "1",
        "2",
        "3",
        "A",
        "ABL",
        "ABS",
        "ACC",
        "ADJ",
        "ADV",
        "AGR",
        "ALL",
        "ANTIP",
        "APPL",
        "ART",
        "AUX",
        "BEN",
        "CAUS",
        "CLF",
        "COM",
        "COMP",
        "COMPL",
        "COND",
        "COP",
        "CVB",
        "DAT",
        "DECL",
        "DEF",
        "DEM",
        "DET",
        "DIST",
        "DISTR",
        "DU",
        "DUR",
        "ERG",
        "EXCL",
        "F",
        "FOC",
        "FUT",
        "GEN",
        "IMP",
        "INCL",
        "IND",
        "INDF",
        "INF",
        "INS",
        "INTR",
        "IPFV",
        "IRR",
        "LOC",
        "M",
        "N",
        "NEG",
        "NMLZ",
        "NOM",
        "OBJ",
        "OBL",
        "P",
        "PASS",
        "PFV",
        "PL",
        "POSS",
        "PRED",
        "PRF",
        "PRS",
        "PROG",
        "PROH",
        "PROX",
        "PST",
        "PTCP",
        "PURP",
        "Q",
        "QUOT",
        "RECP",
        "REFL",
        "REL",
        "RES",
        "S",
        "SBJ",
        "SBJV",
        "SG",
        "TOP",
        "TR",
        "VOC",
    ]
)

# terms which are occasionally recognized, but which are always false positives in the context of ELD
NER_BLACKLIST = [ #check this against more extensive list in the langsci module
    "Q7946755",  #'wasn', radio station
    "Q3089073",  #'happy, happy', norwegian comedy film
    "Q19893364",  #'Inside The Tree', music album
    "Q49084,"  # ss/ short story
    "Q17646620",  # "don't" Ed Sheeran song
    "Q2261572",  # "he/she" Gender Bender
    "Q35852",  # : "ha" hectare
    "Q119018",  #: "Mhm" Mill Hill Missionaries
    "Q932347",  # "gave",# generic name referring to torrential rivers, in the west side of the Pyrenees
    "Q16836659",  # "held" feudal land tenure in England
    "Q914307",  # "ll" Digraph
    "Q3505473",  # "stayed" Stay of proceedings
    "Q303",  # "him/her" Elvis Presley
    "Q2827398",  #: "Aha!" 2007 film by Enamul Karim Nirjhar
    "Q1477068",  # "night and day" Cole Porter song
    "Q1124888",  # "CEDA" Spanish Confederation of the Autonomous Righ
]


ACCEPTABLE_TRANSLATION_TIER_TYPES = (
    "eng",
    "english translation",
    "English translation",
    "English Free Translation",
    "español",
    "fe",
    "fg",
    "fn",
    "fr",
    "free translation",
    "Free Translation",
    "Free translation",
    "Free-translation",
    "Free Translation (English)",
    "FTE",
    "ft",
    "fte",
    "phrase-gls",
    "phrase-item",
    "te",
    "tf (free translation)",
    "Translation",
    "tl",
    "tn",
    "tn (translation in lingua franca)",
    "tf_eng (free english translation)",
    "trad1",
    "Traducción Español",
    "Tradución",
    "Traduccion",
    "Translate",
    "trad",
    "traduccion",
    "traducción",
    "traducción ",
    "Traducción",
    "Traducción español",
    "Traduction",
    "translation",
    "translations",
    "Translation",
    "xe",
    "翻译",
)


ACCEPTABLE_TRANSCRIPTION_TIER_TYPES = (
    "alfabetica",
    "arta",
    "Arta",
    "conversación",
    "default-lt",  # needs qualification
    "default-lt",
    "Dusun",
    "Esenam",
    "Fonética",
    "Frases",
    "Hablado",
    "Hakhun orthography",
    "Hija",
    "hija",
    "ilokano",
    "interlinear-text-item",
    "Intonation_Unit",
    "Ikaan sentences",
    "IPA",
    "Kennedy",
    "Khanty Speech",
    "main-tier",
    "Madre",
    "madre",
    "Matanvat text",
    "Matanvat Text",
    "Nese Utterances",
    "o",
    "or",
    "orth",
    "orthT",
    "orthografia",
    "orthografía",
    "orthography",
    "othography",  # sic
    "po",
    "po (practical orthography)",
    "phrase",
    "phrase-item",
    "phrase-txt",
    "Phrases",
    "Practical Orthography",
    "sentence",
    "sentences",
    "speech",
    "Speech",
    "Standardised-phonology",
    "Sumi",
    "t",  # check this
    "Tamang",
    "texo ",
    "text",
    "Text",
    "Text ",
    "texto",
    "Texto",
    "texto ",
    "Texto principal",
    "Texto Principal",
    "tl",  # check this
    "time aligned",  # check this
    "timed chunk",
    "tl",  # check this
    "trad-gls-spa",
    "Transcribe",
    "Transcrição",
    "TRANSCRIÇÃO",
    "Transcript",
    "Transcripción chol",
    "transcripción chol",
    "Transcripción",
    "Transcripcion",
    "transcripción",
    "Transcripcion chol",
    "transcript",
    "Transcription",
    "transcription",
    "transcription_orthography",
    "trs",
    "trs@",
    "trs1",
    "tx",  # check usages of this
    "tx2",  # check usages of this
    "txt",
    "type_utterance",
    "unit",  # some Dutch texts from TLA
    "ut",
    "utt",
    "Utterance",
    "utterance",
    "uterrances",  # sic
    "utterances",
    "utterrances",  # sic
    "Utterances",
    "utterance transcription",
    "UtteranceType",
    "vernacular",
    "Vernacular",
    "vilela",
    "Vilela",
    "word-txt",
    #'Word', #probably more often used for glossing
    #'word', #probably more often used for glossing
    "word_orthography",
    #'words', #probably more often used for glossing
    #'Words', #more often used for glossing
    "wp",
    "xv",
    "default transcript",
    "句子",
    "句子 ",
    "句子 ",
)

ACCEPTABLE_WORD_TIER_TYPES = (
    "Word",
    "word",
    "Words",
    "words",
    "word-item",
    "morpheme",
    "morphemes",
    "mb",
    "mb (morpheme boundaries)",
    "Morpheme Break",
    "m",
    "morph",
    "mph",
    "wordT",
    "word-txt",
    "morph-txt",
)

ACCEPTABLE_GLOSS_TIER_TYPES = (
    "ge",
    "morph-item",
    "morph-gls",
    "gl",
    "Gloss",
    "gloss",
    "glosses",
    "Glosses",
    "word",
    "word-gls",
    "gl (interlinear gloss)",
)

ACCEPTABLE_COMMENT_TIER_TYPES = (
    "cm",
    "cmt",
    "comment"
)






