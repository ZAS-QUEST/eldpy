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
    ef.populate_transcriptions()
    # with capsys.disabled():
    #     print(ef.transcriptions.keys())
    ef.populate_translations()
    ef.populate_glosses()
    x = ef.get_cldfs()
    assert x.startswith(
        """"ID","Primary_Text","Analyzed_Word","Gloss","Translated_Text","LGRConformance"\r\n"a1","To, kalanga Moek"""
    )
    assert x[200:230] == """kay(H)\t/\tboy's_game\t/\t<place.n"""


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
    ef.populate_transcriptions()
    transcriptions = ef.get_transcriptions()
    assert ef.transcriptions["po"]["tx@A"] == [
        "oino irore",
        "ire awu boe etore emaragodudö",
    ]
    ef.populate_translations()
    ef.translations["ft"]["ft@A"] == ["Thus I did.", "I made these children work"]
    translations = ef.get_translations()
    assert translations == [["Thus I did.", "I made these children work"]]
    ef.populate_glosses()
    assert ef.glossed_sentences["ge"]["ge@A"][1]["ann25"][2] == ["boe.etore", "son"]
    cldfstring = ef.get_cldfs()
    assert (
        cldfstring.split("\n")[1].strip()
        == '"ann0","oino irore","oino\ti=ro=re","thus\t1.SG=make=IND","Thus I did.","WORD_ALIGNED"'
    )
    assert ef.glossed_sentences["ge"]["ge@A"][1]["ann25"][2] == [
        "boe.etore",
        "son",
    ]  # regression test: make sure that get_cldfs does not affect the data itself.


def test_fuzz(capsys):
    # eafs = glob.glob('quarantine/*eaf')
    offset = 0
    # offset = 19029
    eafs = glob.glob("testeafs/*eaf")[offset:]
    eafs.sort()
    with capsys.disabled():
        print(f"fuzzing {len(eafs)} elan files. This can take several minutes")
    out = open("fuzztest.csv", "w")
    header2 = "filename transcribed tier stc wd char wd/stc ch/wd time tier stc wd ch wd/stc ch/ed time tier stc wd distinct uniformity zipf1 zipf2".replace(
        " ", "\t"
    )
    out.write(header2)
    out.write("\n")
    # print(eaf)
    for i, eaf in enumerate(eafs):
        ef = ElanFile(eaf, "www")
        ef.populate_transcriptions()
        transcriptions = ef.get_transcriptions()
        ef.populate_translations()
        translations = ef.get_translations()
        ef.populate_glosses()
        ef.get_cldfs()
        with capsys.disabled():
            # print(eaf)
            print()
            print(str(offset + i).rjust(5, " "), end=" ")
            ef.print_overview(writer=out)
    out.close()
