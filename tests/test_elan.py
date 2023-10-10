import rdflib
import lod
from elanfile import ElanFile

def test_fingerprint():
    ef = ElanFile("goemai_test.eaf", "www")
    fp = ef.fingerprint()
    assert fp == "[R[x[aaas[s[aa]]]x[aaaaasa]]]"

def test_translations():
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_translations()
    t = ef.get_translations()
    assert t[0][6] == "Two people would now move around in front of him, who are the people who look after him."
    assert t[0][4] != "Two people would now move around in front of him, who are the people who look after him."
