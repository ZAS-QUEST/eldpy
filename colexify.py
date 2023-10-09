import json
import glob
from collections import defaultdict
import pprint
import sys


def analyze_colexifications(directory, threshold=3, double_files=[]):
    """return  a list of colexifications found in a directory with json files

    directory -- the directory where the json files are found
    threshold -- how many files should have occurrences of (word,gloss) for it to count as colexification
    double_files -- a list of known double tfile names to be skipped
    """

    colexification_dic = defaultdict(dict)
    print(f"scanning {directory}")
    json_files = glob.glob(f"{directory}/*json")
    print(f"found {len(json_files)} json files")
    for fn in json_files:
        print(f"\nreading {fn}")
        j = json.loads(open(fn).read())
        for a in j: #there is only one archive in the json file
            oldskip = None
            for eaf in j[a]:
                dico = defaultdict(dict)
                collection = eaf.split('/')[1]
                if collection.startswith("1839"):
                   continue
                if collection in double_files:
                    if oldskip is None:
                        print()
                    if collection == oldskip:
                        print(".", end="")
                    else:
                        print(f"\nskipping doublet file {collection}")
                        oldskip = collection
                    continue
                oldskip = None
                for tiertype in j[a][eaf]:
                    for tiername in j[a][eaf][tiertype]:
                        for ancestor in j[a][eaf][tiertype][tiername]:
                            for key in ancestor:
                                for word_gloss_tuple in ancestor[key]:
                                    #print(word_gloss_tuple,len(word_gloss_tuple))
                                    word,gloss = word_gloss_tuple
                                    try:
                                        gloss = gloss.lower().strip()
                                    except AttributeError:
                                        continue
                                    nonascii = False
                                    for character in gloss:
                                        if ord(character)>256:
                                            nonascii = True #all glosses should be in ascii. If something is not ascii, it is probably not relevant for colexification analysis
                                            continue
                                    if nonascii:
                                        continue
                                    flag = False
                                    for c in " 123*АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯяҷөғɨβŋñ?":
                                        if c in gloss:
                                            flag = True
                                    if flag:
                                        continue
                                    if gloss in ("stem", "suffix", "prefix", "n", "v", "nprop", "adj","pron","adv", "q", "mrph", "cl", "interj", "intr", "stat", "rus", "cardnum", "ordnum", "coordconn", "adp", "root", "seq", "attr", "exi.neg", "verb","adj>adv", "vd", "num>n", "adj>adv","postp","conj","enclitic","num", "prep","pro","-", "conn"):
                                        continue

                                    dico[word][gloss] = collection
                for word in dico:
                    if len(dico[word])<2:
                        continue
                    meaninglist= [x for x in dico[word].keys() if x is not None]
                    meaninglist.sort()
                    for i, meaning in enumerate(meaninglist[:-1]):
                        meaning1 = meaninglist[i]
                        meaning2 = meaninglist[i+1]
                        colexification_dic[(meaning1,meaning2)][collection] = True

    strippeddic = {key:colexification_dic[key] for key in colexification_dic if len(colexification_dic[key].keys())>=threshold}
    return strippeddic


if __name__ == "__main__":
    directory = sys.argv[1]
    dic = analyze_colexifications(directory,double_files=["268837","WEW2018","zauzou-li-0535"])
    # pprint.pprint(dic)
    sorted_list = sorted([(len(dic[x]),x) for x in dic.keys()],reverse=True)
    print(f"\nfound {len(sorted_list)} colexification candidates")
    print("writing to colexification.json")
    with open("colexification.json", "w") as out:
        out.write(json.dumps(sorted_list))
