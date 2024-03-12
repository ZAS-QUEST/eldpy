import rdflib

# import lod
import glob
from elanfile import ElanFile
from annotation import Annotation


def test_fingerprint():
    ef = ElanFile("goemai_test.eaf", "www")
    fp = ef.get_fingerprint()
    assert fp == "[R[x[aaas[s[aa]]]x[aaaaasa]]]"


def test_translations():
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_translations()
    t = ef.get_translations()
    assert (
        t[0][6]
        == "Two people would now move around in front of him, who are the people who look after him."
    )
    assert (
        t[0][4]
        != "Two people would now move around in front of him, who are the people who look after him."
    )


def test_transcriptions():
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_transcriptions()
    t = ef.get_transcriptions()
    assert t[0][23] == "To, a bi goegoeme ndoe goeshin mûep pûanang goe yil Dorok."
    assert int(ef.secondstranscribed) == 3836


def test_glosses():
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_glosses()
    assert ef.glossed_sentences["gl"]["gl@A"][23]["a24"][2] == ["ya", "catch"]


#
def test_cldf(capsys):
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate()
    x = ef.get_cldfs()
    # with capsys.disabled():
        # print(ef.comments_with_IDs)
        # print(ef.translations)
        # print(ef.glossed_sentences)
        # print(repr(x[200:250]))
    assert x.startswith(
        """"ID","Primary_Text","Analyzed_Word","Gloss","Translated_Text","Comment","LGRConformance"\r\n"a1","To, kalanga Moek"""
    )
    assert x[200:250] == 'e\t=hoe","okay(H)\t/\tboy\'s_game\t/\t<place.name>\t/\tFOC'


def test_komnzo(capsys):
    ef = ElanFile("komnzo_test.eaf", "www")
    ef.populate(glosscandidates=["gloss"])
    x = ef.get_cldfs()
    assert x[200:230] == 'fé","nä\tzokwasi\twe\tza\\thkäf/é"'


def test_wan(capsys):
    ef = ElanFile("wan_test.eaf", "www")
    ef.populate()
    x = ef.get_cldfs()
    assert x[216:351] == '"è ŋ̄ trɔ̰̀ gbɔ́ ē wàà","è\tŋ̊\ttrɔ̰̀\tgbɔ̊ɔ̊\tē\twà\tX","3sg.subj\tperf\tblessing\tclay_pot\tsee:past\tprt\tprt","She found a pot of luck!"'

def test_saek(capsys):
    ef = ElanFile("saek_test.eaf", "www")
    ef.populate()
    x = ef.get_cldfs()
    assert x[290:546] == '"suan2 man4khoo6 lèè tamo6 man4 kung2 paj nòòm1 bal1 loo5","suan2\tman4khoo6\tlèè\ttamo6\tman4\tkung2\tpaj1\tnòòm1\tbal1\tloo5","garden\tcassava\thest\tstart\t3\ttlnk\tgo\tlook\tmud\tmore","Cassava garden, at the beginning of it (the process), we also go to check the soil."'

def test_yaminawa(capsys):
    ef = ElanFile("yaminawa_test.eaf", "www")
    ef.populate(spanish=True)
    x = ef.get_cldfs()
    assert x[233:453] == '"a4707","Pẽxẽwãkũĩkĩã, pẽxẽwã, datiu pẽxẽwã","pexe\t-wã\t-kũĩ\t=kĩã\tpexe\t-wã\tda\t=tiu\tpexe\t-wã","casa\tAUG\tINTENS\t=EXIST\tcasa\tAUG\tmorir\t=tamaño\tcasa\tAUG","Era una casa grande, una casa grande, una casa grande de este tamaño."'


def test_muyu(capsys):
    ef = ElanFile("muyu_test.eaf", "www")
    ef.populate()
    x = ef.get_cldfs()
    assert x[382:515] == '"a153","Ege olalane keman eyen.","#\t\tege\tolal-an-e\tkem-an\t\teyen","#\t\tDEM\ttalk-IRR-SM\tAUX-1SG\t\tthis.is","This is what I want to tell."'



def test_totoli(capsys):
    ef = ElanFile("totoli_test.eaf", "www")
    ef.populate()
    x = ef.get_cldfs()
    assert x[459:614] == '"ann95","antuknako","antuk\t=na\t=ko\tdei\tsatu\t***\tso-\tlipu\t-an\titu","meaning\t=3s.GEN\t=AND\tLOC\tone\t***\tONE-\tcountry\t-NR\tDIST","in the sense, from our coutnry"'

def test_gorwaa(capsys):
    ef = ElanFile("gorwaa_test.eaf", "www")
    ef.populate(glosscandidates=["morph-item"])
    x = ef.get_cldfs()
    assert x[90:317] == '"ann2_flexid_cf517905-27fc-4f45-a039-924f03d43d8f","desisí ta bay ya Tlaqasí","desi\t-r´\t-sí\tt-\t∅\tbáw\t~$B~\t-a\t~LPA~\tya\tTlaqasí\t-r´","girl:Fr\tL.Fr\tDem2\tMP\tAux\tcall\tM\t-NPst\tSubj\tthus\tTlaqasí\tL.Fr","this girl who is called Tlaqasí"'


# def test_gorwaa_full(capsys):
#     ef = ElanFile("gorwaa_test_all_tiers.eaf", "www")
#     ef.populate(transcriptioncandidates=["morph"],glosscandidates=["morph-item"])
#     x = ef.get_cldfs()
#     with capsys.disabled():
#         print(repr(x[90:274]))
#     assert x[90:274] == '"ann2_flexid_cf517905-27fc-4f45-a039-924f03d43d8f","desisí ta bay ya Tlaqasí","desi\t-r´\t-sí\tt-\t∅\tbáw\t~$B~\t-a\t~LPA~\tya\tTlaqasí\t-r´","girl:Fr\tL.Fr\tDem2\tMP\tAux\tcall\tM\t-NPst\tSubj\tthus\tTlaqasí\tL.Fr","this girl who is called Tlaqasí"'







def test_overview(capsys):
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_transcriptions()
    ef.populate_translations()
    ef.populate_glosses()
    with capsys.disabled():
        out = open("test.csv", "w")
        output = ef.print_overview(writer=out)
        out.close()
    assert output == [
        "goemai_test.eaf",
        "00:02:17",
        "ft",
        "29",
        "668",
        "2863",
        "23.03",
        "4.29",
        "00:02:17",
        "or",
        "27",
        "454",
        "1743",
        "16.81",
        "3.84",
        "01:03:56",
        "gl",
        "29",
        "999",
        "171",
        "5.84",
        "1.07",
        "1.27",
    ]


def test_ref_tx_ft_wd_mb(capsys):
    ef = ElanFile("ref_tx_ft_wd_mb.eaf", "www")
    ef.populate_transcriptions()
    ef.populate_translations()
    ef.populate_glosses()
    output = ef.print_overview()
    assert output == [
        "ref_tx_ft_wd_mb.eaf",
        "00:00:59",
        "ft",
        "15",
        "108",
        "434",
        "7.2",
        "4.02",
        "00:00:50",
        "tx",
        "15",
        "72",
        "339",
        "4.8",
        "4.71",
        "00:00:50",
        "word",
        "30",
        "199",
        "63",
        "3.16",
        "1.0",
        "1.5",
    ]


def test_ref_po_mb_ge_ps_ft_nt(capsys):
    ef = ElanFile("ref_po_mb_ge_ps_ft_nt.eaf", "www")
    ef.populate_transcriptions()
    ef.populate_translations()
    ef.populate_glosses()
    with capsys.disabled():
        output = ef.print_overview()
        assert output == [
            "ref_po_mb_ge_ps_ft_nt.eaf",
            "00:01:10",
            "ft",
            "10",
            "155",
            "687",
            "15.5",
            "4.43",
            "00:00:59",
            "po",
            "10",
            "118",
            "629",
            "11.8",
            "5.33",
            "00:00:59",
            "ge",
            "10",
            "313",
            "59",
            "5.31",
            "1.09",
            "1.1",
        ]


def test_minimal(capsys):
    eaf = "test_minimal.eaf"
    ef = ElanFile(eaf, "www")
    ef.populate()
    transcriptions = ef.get_transcriptions()
    assert ef.transcriptions["po"]["tx@A"] == [
        "oino irore",
        "ire awu boe etore emaragodudö",
    ]
    ef.translations["ft"]["ft@A"] == ["Thus I did.", "I made these children work"]
    translations = ef.get_translations()
    assert translations == [["Thus I did.", "I made these children work"]]
    assert ef.glossed_sentences["ge"]["ge@A"][1]["ann25"][2] == ["boe.etore", "son"]
    cldfstring = ef.get_cldfs()
    print(cldfstring)
    assert (
        cldfstring.split("\n")[1].strip()
        == '"ann0","oino irore","oino\ti=ro=re","thus\t1.SG=make=IND","Thus I did.","","WORD_ALIGNED"'
    )
    assert ef.glossed_sentences["ge"]["ge@A"][1]["ann25"][2] == [
        "boe.etore",
        "son",
    ]  # regression test: make sure that get_cldfs does not affect the data itself.


# def test_fuzz(capsys):
#     # eafs = glob.glob('quarantine/*eaf')
#     offset = 0
#     # offset = 19029
#     eafs = glob.glob("testeafs/*eaf")[offset:]
#     eafs.sort()
#     with capsys.disabled():
#         print(f"fuzzing {len(eafs)} elan files. This can take several minutes")
#     out = open("fuzztest.csv", "w")
#     header2 = "filename transcribed tier stc wd char wd/stc ch/wd time tier stc wd ch wd/stc ch/ed time tier stc wd distinct uniformity zipf1 zipf2".replace(
#         " ", "\t"
#     )
#     out.write(header2)
#     out.write("\n")
#     # print(eaf)
#     for i, eaf in enumerate(eafs):
#         ef = ElanFile(eaf, "www")
#         ef.populate_transcriptions()
#         transcriptions = ef.get_transcriptions()
#         ef.populate_translations()
#         translations = ef.get_translations()
#         ef.populate_glosses()
#         ef.get_cldfs()
#         with capsys.disabled():
#             # print(eaf)
#             print()
#             print(str(offset + i).rjust(5, " "), end=" ")
#             ef.print_overview(writer=out)
#     out.close()
