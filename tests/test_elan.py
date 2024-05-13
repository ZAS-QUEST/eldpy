# import rdflib

# import lod
import glob
from elanfile import ElanFile
from annotation import Annotation
import pprint
import pytest


def test_fuzz(capsys):
    # eafs = glob.glob('quarantine/*eaf')
    offset = 12900
    # offset = 13000
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
        ef.populate()
        ef.get_cldfs()
        with capsys.disabled():
            # print(eaf)
            print()
            print(str(offset + i).rjust(5, " "), end=" ")
            ef.print_overview()
    out.close()


def test_overview(capsys):
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_transcriptions()
    ef.populate_translations()
    ef.populate_glosses()
    with capsys.disabled():
        out = open("test.csv", "w")
        output = ef.print_overview(
            # writer=out
        )
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
        "100.0",
        "or,trs",
        "598",
        "1067",
        "3784",
        "1.78",
        "3.55",
        "00:04:31",
        "197.97",
        "gl",
        "29",
        "372",
        "171",
        "2.18",
        "1.07",
        "1.27",
        "357",
        "2572",
        "13.88",
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
        "83.79",
        "tx",
        "15",
        "72",
        "339",
        "4.8",
        "4.71",
        "00:00:50",
        "83.79",
        "word",
        "15",
        "87",
        "63",
        "1.38",
        "1.0",
        "1.5",
        "13",
        "296",
        "4.39",
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
            "85.63",
            "po",
            "10",
            "118",
            "629",
            "11.8",
            "5.33",
            "00:00:59",
            "85.63",
            "ge",
            "10",
            "143",
            "59",
            "2.42",
            "1.09",
            "1.1",
            "2",
            "550",
            "0.36",
        ]


def test_minimal(capsys):
    eaf = "test_minimal.eaf"
    ef = ElanFile(eaf, "www")
    ef.populate()
    # with capsys.disabled():
    #     print(123)
    #     print(ef.translations)
    assert ef.transcriptions["po"]["tx@A"] == [
        "oino irore",
        "ire awu boe etore emaragodudö",
    ]
    ef.translations["ft"]["ft@A"] == ["Thus I did.", "I made these children work"]
    translations = ef.get_translations()
    assert translations == [["Thus I did.", "I made these children work"]]
    assert ef.glossed_sentences["ge"]["ge@A"][1]["ann25"][2] == ["boe.etore", "son"]
    cldfstring = ef.get_cldfs()
    # with capsys.disabled():
    #     print(cldfstring)
    assert (
        cldfstring.split("\n")[1].strip()
        == '"ann0","oino irore","oino\ti=ro=re","thus\t1.SG=make=IND","Thus I did.","","MORPHEME_ALIGNED"'
    )
    assert ef.glossed_sentences["ge"]["ge@A"][1]["ann25"][2] == [
        "boe.etore",
        "son",
    ]  # regression test: make sure that get_cldfs does not affect the data itself.


# def test_duration(capsys):
#     eaf = "0685IPF0405-MJ-EN3_20240305_mod.eaf"
#     ef = ElanFile(eaf, "www")
#     ef.populate_transcriptions()
#     assert ef.secondstranscribed == 487.613
#     ef.populate_translations(candidates=["Translation"], french=True)
#     translations = ef.get_translations()
#     assert(translations[0][13] == 'Ce père')
#     assert ef.secondstranslated  == 621.371


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
    assert int(ef.secondstranscribed) == 271


def test_glosses():
    ef = ElanFile("goemai_test.eaf", "www")
    ef.populate_glosses()
    assert ef.glossed_sentences["gl"]["gl@A"][23]["a24"][2] == ["ya", "catch"]


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
    assert x[204:234] == 'fé","nä\tzokwasi\twe\tza\\thkäf/é"'


def test_wan(capsys):
    ef = ElanFile("wan_test.eaf", "www")
    ef.populate()
    x = ef.get_cldfs()
    # with capsys.disabled():
    #     print(repr(x[504:676]))
    assert (
        x[512:688]
        == '"a3","nàà gà lé éé klā tàlí yá̰","nàà\tgà\tlé\téé\tklā\ttàlí\tyá̰","1sg+cop\tgo\tprog\t3sg:indep\tbehind\tnow\tthere","I will [explain] that now.","","MORPHEME_ALIGNED"'
    )


def test_saek(capsys):
    ef = ElanFile("saek_test.eaf", "www")
    ef.populate()
    x = ef.get_cldfs()
    assert (
        x[294:550]
        == '"suan2 man4khoo6 lèè tamo6 man4 kung2 paj nòòm1 bal1 loo5","suan2\tman4khoo6\tlèè\ttamo6\tman4\tkung2\tpaj1\tnòòm1\tbal1\tloo5","garden\tcassava\thest\tstart\t3\ttlnk\tgo\tlook\tmud\tmore","Cassava garden, at the beginning of it (the process), we also go to check the soil."'
    )


def test_yaminawa(capsys):
    ef = ElanFile("yaminawa_test.eaf", "www")
    ef.populate(major_languages=["en", "es"])
    x = ef.get_cldfs()
    assert (
        x[233:453]
        == '"a4707","Pẽxẽwãkũĩkĩã, pẽxẽwã, datiu pẽxẽwã","pexe\t-wã\t-kũĩ\t=kĩã\tpexe\t-wã\tda\t=tiu\tpexe\t-wã","casa\tAUG\tINTENS\t=EXIST\tcasa\tAUG\tmorir\t=tamaño\tcasa\tAUG","Era una casa grande, una casa grande, una casa grande de este tamaño."'
    )


def test_yaminawa_p(capsys):
    ef = ElanFile("Pashpiexample01.eaf", "www")
    ef.populate(major_languages=["en", "es"])
    x = ef.get_cldfs()
    # with capsys.disabled():
    #     print(repr(x[204:527]))
    assert (
        x[208:531]
        == '"ann11_flexid_7a42f816-ed01-4f28-9608-e83491ddf21b","Pashpiki askadikia, askapaudikia","pashpi\t=ki\taska\t-di\t=kia\taska\t-pau\t-di\t=kia","masculine.name\t=LAT\tdo.like.this.DIST\tREM.PST\t=EVID.REP\tdo.like.this.DIST\tIMPRF.PST.REM\tREM.PST\t=EVID.REP","They say Pashpi was like this, this is what they say happened.","","WORD_ALIGNED"'
    )


def test_muyu(capsys):
    ef = ElanFile("muyu_test.eaf", "www")
    ef.populate()
    x = ef.get_cldfs(provided_gloss_tier_name="mb@S1")
    assert (
        x[386:537]
        == '"a153","Ege olalane keman eyen.","#\tege\tolal-an-e\tkem-an\teyen","#\tDEM\ttalk-IRR-SM\tAUX-1SG\tthis.is","This is what I want to tell.","","MORPHEME_ALIGNED"'
    )


def test_mbat(capsys):
    ef = ElanFile("mbat_test.eaf", "www")
    ef.populate_transcriptions(candidates=["phrase"])
    ef.populate_translations(candidates=["phrase-item"])
    ef.populate_glosses(candidates=["morph-item"])
    ef.populate_comments()
    x = ef.get_cldfs()
    # with capsys.disabled():
    #     print(repr(x[636:841]))
    assert (
        x[640:845]
        == '"ann112_flexid_889cddd3-69e6-4585-88a6-5dfd0330530c","yan ɓɪlɪm munɓalya.","ya\t=n\tɓɪl\t-ɪm\tmʊn\tɓal\t=ya","3PL\t=FOC\tgive birth\tPFT\tchild\tkind\t=3PL","they have given birth to their children.","","WORD_ALIGNED"'
    )


def test_totoli(capsys):
    ef = ElanFile("totoli_test_mod.eaf", "www")  # totoli_test.eaf has two speakers
    ef.populate()
    x = ef.get_cldfs()
    # with capsys.disabled():
    #     print(x)
    assert (
        x[475:652]
        == '"ann95","antuknako","antuk\t=na\t=ko\tdei\tsatu\t***\tso-\tlipu\t-an\titu","meaning\t=3s.GEN\t=AND\tLOC\tone\t***\tONE-\tcountry\t-NR\tDIST","in the sense, from our coutnry","","MORPHEME_ALIGNED"'
    )


def test_windhoek(capsys):
    ef = ElanFile(
        "KK-Windhoek-20230722-5a-C_mod.eaf", "www"
    )  # totoli_test.eaf has two speakers
    ef.populate(translationcandidates=["fte"])
    x = ef.get_cldfs()
    # with capsys.disabled():
    #     print(repr(x[498:645]))
    assert (
        x[510:661]
        == '"a3938","Ashais ai ta gege ǃnae","Ashai\t-s\tai\t=ta\tge\tge\tǃnae","Ashais\t-3F.SG\ton\t=1SG.SBJ\tDECL\tPST\tbe_born","I was born in Ashais","","MORPHEME_ALIGNED"'
    )


def test_gorwaa(capsys):
    ef = ElanFile("gorwaa_test.eaf", "www")
    ef.populate(glosscandidates=["morph-item"])
    x = ef.get_cldfs()
    assert (
        x[90:317]
        == '"ann2_flexid_cf517905-27fc-4f45-a039-924f03d43d8f","desisí ta bay ya Tlaqasí","desi\t-r´\t-sí\tt-\t∅\tbáw\t~$B~\t-a\t~LPA~\tya\tTlaqasí\t-r´","girl:Fr\tL.Fr\tDem2\tMP\tAux\tcall\tM\t-NPst\tSubj\tthus\tTlaqasí\tL.Fr","this girl who is called Tlaqasí"'
    )


# def test_gorwaa_full(capsys):
#     ef = ElanFile("gorwaa_test_all_tiers.eaf", "www")
#     ef.populate(transcriptioncandidates=["morph"],glosscandidates=["morph-item"])
#     x = ef.get_cldfs()
#     with capsys.disabled():
#         print(repr(x[90:274]))
#     assert x[90:274] == '"ann2_flexid_cf517905-27fc-4f45-a039-924f03d43d8f","desisí ta bay ya Tlaqasí","desi\t-r´\t-sí\tt-\t∅\tbáw\t~$B~\t-a\t~LPA~\tya\tTlaqasí\t-r´","girl:Fr\tL.Fr\tDem2\tMP\tAux\tcall\tM\t-NPst\tSubj\tthus\tTlaqasí\tL.Fr","this girl who is called Tlaqasí"'


def test_errors():
    with pytest.raises(Exception) as exc_info:
        ef = ElanFile("empty.eaf", "www")
    assert exc_info.value.args[0] == "the file empty.eaf is not valid XML"
    # test_non_xml
    with pytest.raises(Exception) as exc_info:
        ef = ElanFile("test.png", "www")
    assert exc_info.value.args[0] == "the file test.png is not valid XML"
    # test_other_xml
    ef = ElanFile("test.pfsx", "www")
    ef.populate()
    assert ef.translations == {}
    assert ef.transcriptions == {}
    assert ef.glossed_sentences == {}
    assert ef.comments == {}
