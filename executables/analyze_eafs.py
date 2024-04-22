import glob
from elanfile import ElanFile
import pandas as pd
import sys
# from collections import OrderedDict

if __name__ == "__main__":
    try:
        workingdir = sys.argv[1]
    except IndexError:
        workingdir = "."
    eafs = glob.glob(f"{workingdir}/*eaf")
    eafs.sort()
    # out = open("eaf_overview.csv", "w")
    line1= """

translation






transcription






gloss





""".split("\n")
    line2 = """filename
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
repetition
zipf1
zipf2
empty_segments
total_segments
ratio_empty""".split("\n")
    # out.write("\t".join(line1)+"\n"+"\t".join(line2)+"\n")
    lines = [line2]
    for i, eaf in enumerate(eafs):
        # print(i)
        ef = ElanFile(eaf, "www")
        ef.populate_transcriptions()
        transcriptions = ef.get_transcriptions()
        ef.populate_translations()
        translations = ef.get_translations()
        ef.populate_glosses()
        line = ef.print_overview()
        lines.append(line)
    # out.close()
    data = lines
    df = pd.DataFrame(data, columns=line2)

    outfilename = "eaf_overview.xls"
    writer = pd.ExcelWriter('eaf_overview.xls', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False,header=False,startrow=0)

    workbook = writer.book
    red_bg = workbook.add_format({'bg_color': "#ffddee"})
    green_bg = workbook.add_format({'bg_color': "#eeffdd"})
    blue_bg = workbook.add_format({'bg_color': "#ddeeff"})
    bold = workbook.add_format({'bold': True})

    worksheet = writer.sheets['Sheet1']
    worksheet.set_row(0, cell_format=bold)
    worksheet.set_column(2,8, cell_format=red_bg)
    worksheet.set_column(9,15, cell_format=green_bg)
    worksheet.set_column(16,22, cell_format=blue_bg)
    writer._save()
    print(f"output written to {outfilename}")


