import rdflib
# import lod
import glob
from elanfile import ElanFile


# def test_fingerprint():
#     ef = ElanFile("goemai_test.eaf", "www")
#     fp = ef.get_fingerprint()
#     assert fp == "[R[x[aaas[s[aa]]]x[aaaaasa]]]"
#
#
# def test_translations():
#     ef = ElanFile("goemai_test.eaf", "www")
#     ef.populate_translations()
#     t = ef.get_translations()
#     assert (
#         t[0][6]
#         == "Two people would now move around in front of him, who are the people who look after him."
#     )
#     assert (
#         t[0][4]
#         != "Two people would now move around in front of him, who are the people who look after him."
#     )
#
#
# def test_transcriptions():
#     ef = ElanFile("goemai_test.eaf", "www")
#     ef.populate_transcriptions()
#     t = ef.get_transcriptions()
#     assert t[0][23] == "To, a bi goegoeme ndoe goeshin mûep pûanang goe yil Dorok."
#     assert int(ef.secondstranscribed) == 3836
#
#
# def test_glosses():
#     ef = ElanFile("goemai_test.eaf", "www")
#     ef.populate_glosses()
#     assert ef.glossed_sentences["gl"]["gl@A"][23]["a24"][2] == ("ya", "catch")
#
#
# def test_cldf(capsys):
#     ef = ElanFile("goemai_test.eaf", "www")
#     ef.populate_transcriptions()
#     ef.populate_translations()
#     ef.populate_glosses()
#     x = ef.get_cldfs()
#     assert x.startswith(""""to\t/\tkalanga\t/\tmoek'wo\t/\ta""")
#     assert x[108:135] == """FOC\t/\tNOMZ.3Sg.Poss\t/\tas_if"""
#
#

def test_overview(capsys):
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_transcriptions()
    ef.populate_translations()
    ef.populate_glosses()
    with capsys.disabled():
        out = open("test.csv", "w")
        ef.print_overview(writer=out)
        out.close()




def test_fuzz(capsys):
    # eafs = glob.glob('quarantine/*eaf')
    offset = 0
    offset = 5512
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
