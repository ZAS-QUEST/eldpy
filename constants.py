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
NER_BLACKLIST = [
    "Q7946755", #'wasn', radio station
    "Q3089073", #'happy, happy', norwegian comedy film
    "Q19893364",#'Inside The Tree', music album
    "Q49084,"# ss/ short story
    "Q17646620",# "don't" Ed Sheeran song
    "Q2261572",# "he/she" Gender Bender
    "Q35852",# : "ha" hectare
    "Q119018",#: "Mhm" Mill Hill Missionaries
    "Q932347",# "gave",# generic name referring to torrential rivers, in the west side of the Pyrenees
    "Q16836659", #"held" feudal land tenure in England
    "Q914307",# "ll" Digraph
    "Q3505473",# "stayed" Stay of proceedings
    "Q303",# "him/her" Elvis Presley
    "Q2827398",#: "Aha!" 2007 film by Enamul Karim Nirjhar
    "Q1477068",# "night and day" Cole Porter song
    "Q1124888",# "CEDA" Spanish Confederation of the Autonomous Righ
    ]
