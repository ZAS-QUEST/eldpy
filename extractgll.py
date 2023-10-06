import glob
import sys
import re
import sre_constants
import pprint
import json
import operator
import os
from collections import defaultdict
from rdflib import Namespace, Graph, Literal, RDF, RDFS  # , URIRef, BNode
from . import lod

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
TEXTEXT = re.compile(r"\\text(.*?)\{(.*?)\}")
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
        #try:
        assert len(self.srcwordstex) == len(self.imtwordstex)
        #except AssertionError:
        #pass
        #print(len(self.srcwordstex), len(self.imtwordstex))
        #print(self.srcwordstex, self.imtwordstex)
        self.categories = self.tex2categories(imt)
        #self.srcwordshtml = [self.tex2html(w) for w in self.srcwordstex]
        #self.imtwordshtml = [self.tex2html(w) for w in self.imtwordstex]
        imt_html = '\n'.join(['\t<div class="imtblock">\n\t\t<div class="srcblock">' + self.tex2html(t[0]) + '</div>\n\t\t<div class="glossblock">' + self.tex2html(t[1]) + '</div>\n\t</div>'
                    for t
                    in zip(self.srcwordstex, self.imtwordstex)
                    ])
        self.html = f'<div class="imtblocks">\n{imt_html}\n</div>\n'
        self.srcwordsbare = [self.striptex(w) for w in self.srcwordstex]
        self.imtwordsbare = [self.striptex(w, sc2upper=True) for w in self.imtwordstex]
        self.clength = len(self.src)
        self.wlength = len(self.srcwordsbare)
        self.ID = "%s-%s" % (
            filename.replace(".tex", "").split("/")[-1],
            str(hash(self.src))[:6],
        )
        self.bookID = filename.split('/')[3]
        self.analyze()

    def tex2html(self, s):
        result = re.sub(TEXTEXT, '<span class="\\1">\\2</span>', s)
        for r in TEXREPLACEMENTS:
            result = result.replace(*r)
        return result

    def striptex(self, s, sc2upper=False):
        if sc2upper:
            for c in self.categories:
                try:
                    s = re.sub("\\\\textsc{%s}" % c, c.upper(), s)
                except sre_constants.error:
                    pass
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

langsci_d = {17:'sje', # pite1240
             66:'ybh', #yakk1236
             67:'mhl', # mauw1238
             78:'pmy', # papu1250
             82:'phl', # phal1254
             85:'fpe',   #fern1234 (Pichi)
             118:'mlw', # Molo1266
             124:'rap',  #  rapa1244
             212:'tci',  # wara1294 (Komnzo)
             250:'dar'  #sanz1248          (Iso is not precise here)
             }

def langsciextract(directory):
    #directory = sys.argv[1]

    books = glob.glob(f"{directory}/*")
    graph = lod.create_graph()
    graph.add((lod.QUEST.morph2,#TODO needs better label
            lod.RDFS.subPropertyOf,
            lod.LIGT.annotation
            ))
    graph.add((lod.QUEST.gloss2, #TODO needs better label
            lod.RDFS.subPropertyOf,
            lod.LIGT.annotation
            ))
    for book in books:
        book_ID = int(book.split("/")[-1])
        book_lod_ID = f"book{book_ID}"
        #print("found %i books in %s" % (len(books), directory))
        language = langsci_d.get(int(book_ID), "und")
        glossesd = defaultdict(int)
        excludechars = ".\\}{=~:/"
        files = glob.glob(f"{directory}/{book_ID}/chapters/*tex")
        print(" found %i tex files for %s" % (len(files), book_ID))
        for filename in files:
            try:
                s = open(filename).read()
            except UnicodeDecodeError:
                print("Unicode problem in %s"% filename)
            examples = []
            glls = GLL.findall(s)
            #print(filename, end=": ")
            #print(f"  {len(glls)}")
            for g in glls:
                try:
                    thisgll = gll(*g, filename=filename, language=language)
                except AssertionError:
                    continue
                examples.append(thisgll)
                example_block_ID = f"{book_lod_ID}_{thisgll.ID}"
                sentence_word_tier_lod_ID = f"{example_block_ID}_wt"
                sentence_morph_tier_lod_ID = f"{example_block_ID}_mt"
                wordstring =  " ".join(thisgll.srcwordsbare)
                glossstring =  " ".join(thisgll.imtwordsbare)
                example_block_nif_label = wordstring
                words_nif_label =  wordstring
                gloss_language_id = "eng"
                vernacular_language_id = language
                graph.add((lod.ARCHIVE_NAMESPACES['langsci'][book_lod_ID],
                    lod.LIGT.hasTier,
                    lod.QUESTRESOLVER[example_block_ID],
                ))
                graph.add((lod.QUESTRESOLVER[example_block_ID],
                            RDF.type,
                            lod.LIGT.InterlinearText
                ))
                graph.add((lod.QUESTRESOLVER[example_block_ID],
                        RDF.type,
                        lod.LIGT.Utterance
                        ))
                graph.add((lod.QUESTRESOLVER[example_block_ID],
                        lod.NIF.anchorOf,
                        Literal(example_block_nif_label, lang=vernacular_language_id),
                        ))
                graph.add((lod.QUESTRESOLVER[example_block_ID],
                        lod.LIGT.hasTier,
                        lod.QUESTRESOLVER[sentence_word_tier_lod_ID],
                        ))
                graph.add((lod.QUESTRESOLVER[example_block_ID],
                        lod.LIGT.hasTier,
                        lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                        ))
                #words
                graph.add((lod.QUESTRESOLVER[sentence_word_tier_lod_ID],
                        RDF.type,
                        lod.LIGT.WordTier,
                        ))
                graph.add((lod.QUESTRESOLVER[sentence_word_tier_lod_ID],
                        lod.NIF.anchorOf,
                        Literal(example_block_ID, lang=vernacular_language_id),
                        ))
                #morphs
                graph.add((lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                        RDF.type,
                        lod.LIGT.MorphTier,
                        ))
                graph.add((lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                        lod.NIF.anchorOf,
                        Literal(example_block_ID, lang=vernacular_language_id),
                        ))
                words = thisgll.srcwordsbare
                wordglosses = thisgll.imtwordsbare

                for i in range(len(words)):
                    word = words[i]
                    word_id = f"{sentence_word_tier_lod_ID}_{i}"
                    wordgloss = wordglosses[i]
                    try:
                        wordgloss = wordgloss.strip()
                    except TypeError:
                        wordgloss = ""
                    #add items to tier
                    graph.add((lod.QUESTRESOLVER[sentence_word_tier_lod_ID],
                        lod.LIGT.item,
                        lod.QUESTRESOLVER[word_id]
                        ))
                    #anchor in superstring about items
                    graph.add((lod.QUESTRESOLVER[word_id],
                        lod.NIF.anchorOf,
                        lod.QUESTRESOLVER[sentence_word_tier_lod_ID]
                        ))
                    #forward link to create linked list
                    try:
                        nextword = words[i + 1]
                        nextword_id = f"{sentence_word_tier_lod_ID}_{i+1}"
                        graph.add((lod.QUESTRESOLVER[word_id],
                                lod.LIGT.nextWord,
                                lod.QUESTRESOLVER[nextword_id]
                                ))
                    except IndexError:  # we have reached the end of the list
                        graph.add((lod.QUESTRESOLVER[word_id],
                                lod.LIGT.nextWord,
                                lod.RDF.nil,
                            ))
                    #give labels for words
                    graph.add((lod.QUESTRESOLVER[word_id],
                                lod.QUEST.word2, #TODO probably use not   "word2" here
                                Literal(word, lang=vernacular_language_id),
                            ))
                    graph.add((lod.QUESTRESOLVER[word_id],
                                lod.QUEST.gloss2, #TODO probably use not   "gloss2" here
                                Literal(wordgloss, lang=gloss_language_id)
                            ))

                    morphs = re.split("[-=]", word)
                    morphglosses = re.split("[-=]", wordgloss)
                    try:
                        assert len(morphs) == len(morphglosses)
                    except AssertionError:
                        #print(len(morphs), len(morphglosses), morphs, morphglosses)
                        continue

                    for j in range(len(morphs)):
                        morph = morphs[j]
                        morph_id = f"{sentence_morph_tier_lod_ID}_{i}_{j}"
                        morphgloss = morphglosses[j]
                        #try:
                            #morphgloss = morphgloss.strip()
                        #except TypeError:
                            #morphgloss = ""
                        #add items to tier
                        graph.add((lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                            lod.LIGT.item,
                            lod.QUESTRESOLVER[morph_id]
                            ))
                        #anchor in superstring about items
                        graph.add((lod.QUESTRESOLVER[morph_id],
                            lod.NIF.anchorOf,
                            lod.QUESTRESOLVER[sentence_morph_tier_lod_ID]
                            ))
                        #forward link to create linked list
                        try:
                            nextmorph = morphs[j + 1]
                            nextmorph_id = f"{sentence_morph_tier_lod_ID}_{j + 1}"
                            graph.add((lod.QUESTRESOLVER[morph_id],
                                    lod.LIGT.nextWord,
                                    lod.QUESTRESOLVER[nextmorph_id]
                                    ))
                        except IndexError:  # we have reached the end of the list
                            graph.add((lod.QUESTRESOLVER[morph_id],
                                    lod.LIGT.nextWord,
                                    lod.RDF.nil,
                                ))
                        #give labels for morphs
                        graph.add((lod.QUESTRESOLVER[morph_id],
                                    lod.QUEST.morph2, #TODO probably use not   "morph2" here
                                    Literal(morph, lang=vernacular_language_id),
                                ))
                        graph.add((lod.QUESTRESOLVER[morph_id],
                                    lod.QUEST.gloss2, #TODO probably use not   "gloss2" here
                                    Literal(morphgloss, lang=gloss_language_id)
                                ))

                        for subgloss in re.split("[-=.:]", morphgloss):
                            subgloss = (
                                subgloss.replace("1", "")
                                .replace("2", "")
                                .replace("3", "")
                            )
                            if subgloss in lod.LGRLIST:
                                graph.add((lod.QUESTRESOLVER[morph_id],
                                        lod.QUEST.has_lgr_value,
                                        lod.LGR[subgloss]
                                        ))


                #count root occurrences (could probably go to separte module
                for imtgloss in thisgll.imtwordsbare:
                    for imtmorph in re.split("[-=]", imtgloss):
                        if  imtmorph.isupper():
                            continue
                        glossesd[imtmorph] += 1

                #except IndexError:
                #pass
            #except sre_constants.error:
                #pass
            if examples != []:
                jsons = json.dumps([ex.__dict__ for ex in examples], sort_keys=True, indent=4, ensure_ascii=False)
                jsonname = 'langscijson/%sexamples.json'%filename[:-4].replace('/','-').replace('eldpy-langscitex--','').replace('-chapters', '')
                #print(filename)
                print("   ", jsonname)
                with open(jsonname, 'w', encoding='utf8') as jsonout:
                    jsonout.write(jsons)
    #print(len(graph), "gloss triples")
    #lod.write_graph(graph, "langsci-glosses.n3")
    #with open('imtwords.json', 'w') as glossout:
        #sorted_glosses = sorted(glossesd.items(), key=operator.itemgetter(1))
        #glossout.write("\n".join(
                                #["%s: %i" % (x[0], x[1]) for x in sorted_glosses[::-1]]
                            #)
                    #)



    #n3out = open("langsci-glosses.n3", "w")

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
