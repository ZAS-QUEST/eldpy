import csv
import sys
import re


preamble=r"""\documentclass{scrartcl}
\usepackage{libertine}
\usepackage{langsci-gb4e}
\examplesitalics
\renewcommand{\exfont}{\itshape}
\newcommand{\verntrans}[2]{\parbox[t]{.45\textwidth}{#1}\qquad\parbox[t]{.45\textwidth}{#2}\medskip\par}
%s
\begin{document}
%s
"""

end_document="\\end{document}"

def escape_latex(s, no_spaces=False):
    result =  s.replace("\\", "{\\textbackslash}")\
        .replace("_", "\\_")\
        .replace("&","\\&")\
        .replace("#","\#")\
        .replace("$","\\$")\
        .replace("^","\\^")\
        .replace("~","{\\textasciitilde}")\
        .replace("`", "{\\textasciigrave}")\
        .replace("\t\t","\t{\\relax}\t")
    if no_spaces:
        result = result.replace(" ", "\\_")
    return result

def latex_quotation_marks(s):
    result = re.sub('"(?=\B)', "''", s)
    result = re.sub('(?<=\B)"', '``', result)
    return result

def get_matrix_content_from_csv(filename,provided_title=""):
    matrix = []
    with open(filename, mode='r', encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            ID = row["ID"]
            gloss = row["Gloss"]
            primary_text = row["Primary_Text"]
            analyzed_word = row["Analyzed_Word"]
            translation = row["Translated_Text"]
            comment = row.get("Comment",'')
            matrix.append([ID,primary_text,analyzed_word,gloss,translation,comment])
    return matrix

def get_tex_content_from_csv(filename,provided_title="", output_type="examples", orthographic_line=True,standalone=True):
    matrix = get_matrix_content_from_csv(filename,provided_title="")
    return get_tex_content(matrix,provided_title=provided_title,output_type=output_type,orthographic_line=orthographic_line,standalone=standalone)


def get_tex_content(matrix,provided_title="",output_type="examples",orthographic_line=True,standalone=True):
    title = "\\title{%s}\date{}"%provided_title
    maketitle = "\maketitle"
    if standalone:
        resultstring = preamble % (title,maketitle)
    else:
        resultstring = ""
    vernaculars = []
    translations = []
    comments = []
    for row in matrix:
        if len(row)<6:
            continue #FIXME need better check for matrix integrity
        ID = row[0]
        if orthographic_line:
            primary_text = latex_quotation_marks(escape_latex(row[1]))
        else:
            primary_text = "%"
        vernacular = row[2].strip()
        gloss = row[3]
        translation = row[4]
        comment = latex_quotation_marks(escape_latex(row[5]))
        processed_translation = latex_quotation_marks(escape_latex(translation))
        vernacular_words = vernacular.split("\t")
        recomposed_vernacular_string = "\t".join(["{%s}"%w if " " in w else w for w in vernacular_words])
        recomposed_vernacular_string = escape_latex(recomposed_vernacular_string)
        gloss=escape_latex(gloss, no_spaces=True)
        allcapsglosses = re.findall("([A-Z][A-Z]+)", gloss)
        sorted_glosses = sorted(allcapsglosses,key=len)[::-1]
        for match in  sorted_glosses:
            gloss=gloss.replace(match, "\\textsc{%s}"%match.lower())
        if gloss.startswith("\t"):
            gloss = "{\\relax}"+gloss
        if output_type == "examples":
            resultstring += ('\\ea\\label{ex:%s}\n' % ID)
            resultstring += (primary_text+"\\\\\n")
            resultstring += (f'\\gll {recomposed_vernacular_string}\\\\\n')
            resultstring += (f'     {gloss}\\\\\n')
            footnotestring = ''
            if comment:
                footnotestring = "\\footnote{%s}"%comment
            resultstring += (f"""\\glt `{processed_translation}'{footnotestring}\n""")
            resultstring += ("\\z\n\n")
        if output_type == "lines":
            resultstring += ("\\verntrans{%s}{%s}\n" % (recomposed_vernacular_string,processed_translation))
        if output_type in ["pages","columns", "translation"]:
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
    if output_type == "translation":
        translation_cell = []
        for i,_ in enumerate(translations):
            translation = translations[i]
            translation_cell.append(translation)
        resultstring += ("\n".join(translation_cell))
    if standalone:
        resultstring += (end_document)
    return(resultstring)


if __name__ == "__main__":
    standalone = False #FIXME
    examples = True
    output_type = "examples"
    orthographic_line = True
    try:
        orthographic_line = sys.argv[4] #FIXME do this with proper option parsing
        orthographic_line = False
    except IndexError:
        pass
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
        sys.exit()
    tex_filename = filename[0:-4]+".tex"
    with open(tex_filename, "w", encoding="utf-8") as tex_file:
        tex_file.write(get_tex_content_from_csv(filename,provided_title=provided_title,output_type=output_type,orthographic_line=orthographic_line,standalone=standalone))
