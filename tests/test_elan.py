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


def test_cldf(capsys):
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_transcriptions()
    ef.populate_translations()
    ef.populate_glosses()
    x = ef.get_cldfs()
    print("|",repr(x[0:30]),"|")
    assert x.startswith(""""ID","Analyzed_Word","Gloss","Translated_Text"\r\n"a1","to\t/\tkalanga\t/\tmoek'wo\t/\ta""")
    assert x[100:130] == """e-\tn-\td\'e-\tnnoe\t=hoe","okay(H)"""



def test_overview(capsys):
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_transcriptions()
    ef.populate_translations()
    ef.populate_glosses()
    with capsys.disabled():
        out = open("test.csv", "w")
        ef.print_overview(writer=out)
        out.close()

def test_ref_tx_ft_wd_mb(capsys):
    ef = ElanFile("ref_tx_ft_wd_mb.eaf", "www")
    ef.populate_transcriptions()
    ef.populate_translations()
    ef.populate_glosses()
    output = ef.print_overview()
    assert output == "ref_tx_ft_wd_mb.eaf\t00:00:59\tft\t15\t108\t434\t7.2\t4.02\t00:00:50\ttx\t15\t72\t339\t4.8\t4.71\t00:00:50\tword\t30\t199\t63\t3.16"



def test_ref_po_mb_ge_ps_ft_nt(capsys):
    ef = ElanFile("ref_po_mb_ge_ps_ft_nt.eaf", "www")
    ef.populate_transcriptions()
    ef.populate_translations()
    ef.populate_glosses()
    with capsys.disabled():
        output = ef.print_overview()
        assert output == "ref_po_mb_ge_ps_ft_nt.eaf\t00:01:10\tft\t10\t155\t687\t15.5\t4.43\t00:00:59\tpo\t10\t118\t629\t11.8\t5.33\t00:00:59\tge\t10\t313\t59\t5.31"




#
#
def test_fuzz(capsys):
    # eafs = glob.glob('quarantine/*eaf')
    offset = 0
    offset = 11237
    eafs = glob.glob("testeafs/*eaf")[offset:]
    eafs.sort()
    with capsys.disabled():
        print(f"fuzzing {len(eafs)} elan files. This can take several minutes")
    out = open("test.csv", "w")
    for i, eaf in enumerate(eafs):
        # print(eaf)
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
