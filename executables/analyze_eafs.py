import glob
from elanfile import ElanFile

if __name__ == "__main__":
    eafs = glob.glob("*eaf")
    eafs.sort()
    out = open("eaf_overview.csv", "w")
    out.write("""

translation






transcription






gloss



""".replace("\n","\t"))
    out.write("\n")
    out.write("""name
duration_timeslots
tiername
#sentences
#words
#chars
words/stc
chars/word
duration
tiername
#sentences
#words
#chars
words/stc
chars/words
duration
tiername
#sentences
#items
distinct
repetition""".replace("\n","\t"))
    out.write("\n")

    for i, eaf in enumerate(eafs):
        ef = ElanFile(eaf, "www")
        ef.populate_transcriptions()
        transcriptions = ef.get_transcriptions()
        ef.populate_translations()
        translations = ef.get_translations()
        ef.populate_glosses()
        ef.print_overview(writer=out)
    out.close()
