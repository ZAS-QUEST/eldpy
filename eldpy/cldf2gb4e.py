import csv
import sys
import re


preamble=r"""\documentclass{scrartcl}
\usepackage{libertine}
\usepackage{langsci-gb4e}
\examplesitalics
\newcommand{\verntrans}[2]{\parbox[t]{.45\textwidth}{#1}\qquad\parbox[t]{.45\textwidth}{#2}\medskip\par}
%s
\begin{document}
%s
"""

end_document="\\end{document}"



def get_tex_content_from_csv(filename,provided_title="", output_type="examples"):
    matrix = []
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            ID = row["ID"]
            gloss = row["Gloss"]
            primary_text = row["Primary_Text"]
            analyzed_word = row["Analyzed_Word"]
            translation = row["Translated_Text"]
            matrix.append([ID,primary_text,analyzed_word,gloss,translation])
    return get_tex_content(matrix,provided_title=provided_title,output_type=output_type)


def get_tex_content(matrix,provided_title="",output_type="examples"):
    title = "\\title{%s}\date{}"%provided_title
    maketitle = "\maketitle"
    resultstring = preamble % (title,maketitle)
    vernaculars = []
    translations = []
    for row in matrix:
        ID = row[0]
        primary_text = row[1].strip()
        vernacular = row[2].strip()
        gloss = row[3].strip()
        translation = row[4].strip()
        processed_translation = translation.replace("&","\\&").replace("#","\\#")
        vernacular_words = vernacular.split("\t")
        recomposed_vernacular_string = "\t".join(["{%s}"%w if " " in w else w for w in vernacular_words])
        recomposed_vernacular_string = recomposed_vernacular_string.replace("&","\\&").replace("#","\\#").replace("\t\t","\t{\\relax}\t")
        allcapsglosses = re.findall("([A-Z.]*[A-Z]+)",gloss)
        for match in  sorted(allcapsglosses)[::-1]:
            gloss=gloss.replace(match, "\\textsc{%s}"%match.lower())
        gloss=gloss.replace("_", "\\_").replace(" ", "\\_").replace("&","\\&").replace("#","\#").replace("\t\t","\t{\\relax}\t")
        if gloss.startswith("\t"):
            gloss = "{\\relax}"+gloss
        if output_type == "examples":
            resultstring += ('\\ea\\label{ex:%s}\n' % ID)
            resultstring += (f'\\gll {recomposed_vernacular_string}\\\\\n')
            resultstring += (f'     {gloss}\\\\\n')
            resultstring += (f"""\\glt `{processed_translation}'\n""")
            resultstring += ("\\z\n\n")
        if output_type == "lines":
            resultstring += ("\\verntrans{%s}{%s}\n" % (recomposed_vernacular_string,processed_translation))
        if output_type in ["pages","columns"]:
            vernaculars.append(recomposed_vernacular_string)
            translations.append(processed_translation)
    if output_type == "columns":
        # print(len(vernaculars))
        # print(len(translations))
        max_chars_page=1700
        accumulated_chars_vernacular=0
        accumulated_chars_translation=0
        # print(accumulated_chars_vernacular)
        # print(accumulated_chars_translation)
        resultstring += ("\\begin{tabular}{p{.45\\textwidth}@{\qquad\qquad}p{.45\\textwidth}}\n")
        vernacular_cell = []
        translation_cell = []
        for i,_ in enumerate(vernaculars):
            vernacular = vernaculars[i]
            translation = translations[i]
            accumulated_chars_vernacular += len(vernacular)
            accumulated_chars_translation += len(translation)
            if accumulated_chars_vernacular > max_chars_page or accumulated_chars_translation > max_chars_page:
                resultstring += ("\n".join(vernacular_cell))
                resultstring += ("\n&\n")
                resultstring += ("\n".join(translation_cell))
                resultstring += ("\n\\end{tabular}\medskip\n\n")
                resultstring += ("\\begin{tabular}{p{.45\\textwidth}@{\qquad\qquad}p{.45\\textwidth}}\n")
                accumulated_chars_vernacular=len(vernacular)
                accumulated_chars_translation=len(translation)
                vernacular_cell = [vernacular]
                translation_cell = [translation]
            vernacular_cell.append(vernacular)
            translation_cell.append(translation)
        resultstring += ("\n".join(vernacular_cell))
        resultstring += ("\n&\n")
        resultstring += ("\n".join(translation_cell))
        resultstring += ("\\end{tabular}\medskip\n\n")
    if output_type == "pages":
        # print(len(vernaculars))
        # print(len(translations))
        max_chars_page=3500
        accumulated_chars_vernacular=0
        accumulated_chars_translation=0
        # print(accumulated_chars_vernacular)
        # print(accumulated_chars_translation)
        vernacular_cell = []
        translation_cell = []
        for i,_ in enumerate(vernaculars):
            vernacular = vernaculars[i]
            translation = translations[i]
            accumulated_chars_vernacular += len(vernacular)
            accumulated_chars_translation += len(translation)
            if accumulated_chars_vernacular > max_chars_page or accumulated_chars_translation > max_chars_page:
                resultstring += ("\n".join(vernacular_cell))
                resultstring += ("\\newpage\n")
                resultstring += ("\n".join(translation_cell))
                resultstring += ("\\newpage\n")
                accumulated_chars_vernacular=len(vernacular)
                accumulated_chars_translation=len(translation)
                vernacular_cell = [vernacular]
                translation_cell = [translation]
            vernacular_cell.append(vernacular)
            translation_cell.append(translation)
        resultstring += ("\n".join(vernacular_cell))
        resultstring += ("\\newpage\n")
        resultstring += ("\n".join(translation_cell))
    resultstring += (end_document)
    return(resultstring)


if __name__ == "__main__":
    examples = True
    output_type = "examples"
    try:
        output_type = sys.argv[3]
    except IndexError:
        pass
    try:
        provided_title = sys.argv[2]
    except IndexError:
        provided_title = ""
    filename = sys.argv[1]
    if not filename.endswith("csv"):
        print("please provide a file of type csv")
    else:
        tex_filemame = filename[0:-4]+".tex"
        with open(tex_filemame,"w") as tex_file:
            tex_file.write(get_tex_content_from_csv(filename,provided_title=provided_title,output_type=output_type))
