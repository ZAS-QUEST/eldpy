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
tiertype
#sentences
#words
#chars
words/stc
chars/word
duration
%sec translated
tiertype
#sentences
#words
#chars
words/stc
chars/words
duration
%sec transcribed
tiertype
#sentences
#items
distinct
repetition
zipf1
zipf2
empty_segments
total_segments
%empty""".split("\n")
    lines = [line1,line2]
    offset = 0
    # offset = 3649
    for i, eaf in enumerate(eafs[offset:]):
        print(i+offset,eaf)
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
    grey_bg = workbook.add_format({'bg_color': "#eeeeee"})
    bold = workbook.add_format({'bold': True})

    worksheet = writer.sheets['Sheet1']
    worksheet.set_row(0, cell_format=bold)
    worksheet.set_row(1, cell_format=bold)
    worksheet.set_column(2,9, cell_format=red_bg)
    worksheet.set_column(10,17, cell_format=green_bg)
    worksheet.set_column(18,24, cell_format=blue_bg)
    worksheet.set_column(25,27, cell_format=grey_bg)
    writer._save()
    print(f"output written to {outfilename}")


