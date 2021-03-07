import sys
import re
import sre_constants
import pprint
import json
import os

#GLL = re.compile(
    #r"\\gll[ \t]*(.*?) *?\\\\\\\\\n[ \t]*(.*?) *?\\\\\\\\\n+[ \t]*\\\\glt[ \t\n]*(.*?)\n"
#)
SOURCELINE = r"\\gll[ \t]*(.*?) *?\\\\\n"
IMTLINE = r"[ \t]*(.*?) *?\\\\\n+" #some authors add multiple newlines before the translation
TRSLINE = r"\\glt[ \t\n]*(.*?)\n"

#GLL = re.compile(
    #r"\\gll[ \t]*(.*?) *?\\\\\n[ \t]*(.*?) *?\\\\\n+[ \t]*\\glt[ \t\n]*(.*?)\n"
#)
GLL = re.compile(SOURCELINE+IMTLINE+TRSLINE)
TEXTEXT = re.compile("\\\\text(.*?)\{(.*?)\}")
STARTINGQUOTE = "`‘"
ENDINGQUOTE = "'’"
TEXREPLACEMENTS = [
    (r"\_", "_"),
    (r"\textquotedbl", '"'),
    (r"\textprimstress", "ˈ"),
    (r"\textbackslash", r"\\"),
    (r"\textbar", "|"),
    (r"\textasciitilde", "~"),
    (r"\textless", "<"),
    (r"\textgreater", ">"),
    (r"\textrightarrow", "→"),
    (r"\textalpha", "α"),
    (r"\textbeta", "β"),
    (r"\textgamma", "γ"),
    (r"\textdelta", "δ"),
    (r"\textepsilon", "ε"),
    (r"\textphi", "φ"),
    (r"\textupsilon", "υ"),
    (r"\newline", " "),
    (r"{\ꞌ}", "ꞌ"),
    (r"{\ob}", "["),
    (r"{\cb}", "]"),
    (r"{\db}", " "),
    (r"\nobreakdash", ""),
]


class gll:
    def __init__(self, src, imt, trs, filename=None, language=None):
        self.filename = filename
        self.src = src
        self.imt = imt
        self.language = language
        self.trs = trs.strip()
        if self.trs[0] in STARTINGQUOTE:
            self.trs = self.trs[1:]
        if self.trs[-1] in ENDINGQUOTE:
            self.trs = self.trs[:-1]
        self.srcwordstex = self.src.split()
        self.imtwordstex = self.imt.split()
        assert len(self.srcwordstex) == len(self.imtwordstex)
        self.categories = self.tex2categories(imt)
        self.srcwordshtml = [self.tex2html(w) for w in self.srcwordstex]
        self.imtwordshtml = [self.tex2html(w) for w in self.imtwordstex]
        self.srcwordsbare = [self.striptex(w) for w in self.srcwordstex]
        self.imtwordsbare = [self.striptex(w, sc2upper=True) for w in self.imtwordstex]
        self.clength = len(self.src)
        self.wlength = len(self.srcwordsbare)
        self.ID = "%s-%s" % (
            self.filename.replace(".tex", "").split("/")[-1],
            str(hash(self.src))[:6],
        )
        self.analyze()

    def tex2html(self, s):
        result = re.sub(TEXTEXT, '<span class="\\1">\\2</span>', s)
        for r in TEXREPLACEMENTS:
            result = result.replace(*r)
        return result

    def striptex(self, s, sc2upper=False):
        if sc2upper:
            for c in self.categories:
                s = re.sub("\\\\textsc{%s}" % c, c.upper(), s)
        result = re.sub(TEXTEXT, "\\2", s)

        for r in TEXREPLACEMENTS:
            result = result.replace(*r)
        return result

    def tex2categories(self, s):
        d = {}
        scs = re.findall("\\\\textsc\{(.*?)\}", s)
        for sc in scs:
            cats = re.split("[-=.:]", sc)
            for cat in cats:
                d[cat] = True
        return sorted(list(d.keys()))

    def json(self):
        print(json.dumps(self.__dict__, sort_keys=True, indent=4))

    def __str__(self):
        return "%s\n%s\n%s\n" % (self.srcwordshtml, self.imtwordshtml, self.trs)

    def analyze(self):
        if " and " in self.trs:
            self.coordination = "and"
        if " or " in self.trs:
            self.coordination = "or"
        if " yesterday " in self.trs.lower():
            self.time = "past"
        if " tomorrow " in self.trs.lower():
            self.time = "future"
        if " now " in self.trs.lower():
            self.time = "present"
        if " want" in self.trs.lower():
            self.modality = "volitive"
        if " not " in self.trs.lower():
            self.polarity = "negative"


if __name__ == "__main__":
    filename = sys.argv[1]
    language = sys.argv[2]
    #try:
    s = open(filename).read()
    #except IndexError:
        #s = ""
    print(len(s))
    examples = []
    glls = GLL.findall(s)
    print(filename, end=": ")
    print(len(glls))
    for g in glls:
        try:
            examples.append(gll(*g, filename=filename, language=language))
        except AssertionError:
            pass
        except IndexError:
            pass
        except sre_constants.error:
            pass
    if examples != []:
        jsons = json.dumps([ex.__dict__ for ex in examples], sort_keys=True, indent=4)
        out = open('langscijson/%sexamples.json'%filename[:-4].replace('/','-'), 'w')
        #out = open("xigtdata/%sexamples.xml" % filename[:-4].replace("/", "-"), "w")
        #out.write(
            #"""
      #<igt id="igt10-6" doc-id="10" line-range="103-105" tag-types="L G T">
#<metadata>
#<meta id="meta1">
#<dc:subject olac:code="{lg}" xsi:type="olac:language">{lg}</dc:subject>
#<dc:language olac:code="en" xsi:type="olac:language">English</dc:language>
#</meta>
#</metadata>
#<tier id="n" type="odin" alignment="c" state="normalized">
#<item id="n1" alignment="c1" line="103" tag="L">{source}</item>
#<item id="n2" alignment="c2" line="104" tag="G">{imt}</item>
#<item id="n3" alignment="c3" line="105" tag="T">{trs}</item>
#</tier>
#</igt>
#""".format(
                #src=g.src, imt=g.imt, trs=g.trs, lg=lg
            #)
        #)
        #out.close()
