import rdflib
import lod
import glob
from elanfile import ElanFile

def test_fingerprint():
    ef = ElanFile("goemai_test.eaf", "www")
    fp = ef.get_fingerprint()
    assert fp == "[R[x[aaas[s[aa]]]x[aaaaasa]]]"

def test_translations():
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_translations()
    t = ef.get_translations()
    assert t[0][6] == "Two people would now move around in front of him, who are the people who look after him."
    assert t[0][4] != "Two people would now move around in front of him, who are the people who look after him."


def test_transcriptions():
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_transcriptions()
    t = ef.get_transcriptions()
    t[0][23] == 'To, a bi goegoeme ndoe goeshin mûep pûanang goe yil Dorok.'

def test_glosses():
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_glosses()
    ef.glossed_sentences['gl']['gl@A'][23]['a24'][2] == ('ya', 'catch')

def test_fuzz(capsys):
    eafs = glob.glob('test_eafs/*eaf')
    with capsys.disabled():
        print(f"fuzzing {len(eafs)} elan files. This can take several minutes")

    for eaf in eafs:
        ElanFile(eaf, "www")