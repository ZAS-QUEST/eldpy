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
        json_content = json.loads(open(fn).read())
        for archive in json_content:  # there is only one archive in the json file
            oldskip = None  # we only give skipping information once per skipped file
            for eaf in json_content[archive]:
                dico = defaultdict(dict)  # we store (word,gloss) tuples
                collection = eaf.split("/")[1]
                if collection.startswith("1839"):  # many spurious files start with 1839
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
                # drill down to the relevant information in the ELAN tree
                for tiertype in json_content[archive][eaf]:
                    for tiername in json_content[archive][eaf][tiertype]:
                        for ancestor in json_content[archive][eaf][tiertype][tiername]:
                            for key in ancestor:
                                for word_gloss_tuple in ancestor[key]:
                                    word, gloss = word_gloss_tuple
                                    try:
                                        gloss = gloss.lower().strip()
                                    except AttributeError:
                                        continue
                                    # we exclude all glosses which are not in plain language
                                    nonascii = False
                                    for character in gloss:
                                        if ord(character) > 256:
                                            nonascii = True  # all glosses should be in ascii. If something is not ascii, it is probably not relevant for colexification analysis
                                            continue
                                    if nonascii:
                                        continue
                                    flag = False
                                    for c in " 123*?":
                                        if c in gloss:
                                            flag = True
                                    if flag:
                                        continue
                                    # we skip glosses which are not translations but rather categorizations
                                    if gloss in (
                                        "stem",
                                        "suffix",
                                        "prefix",
                                        "n",
                                        "v",
                                        "nprop",
                                        "adj",
                                        "pron",
                                        "adv",
                                        "q",
                                        "mrph",
                                        "cl",
                                        "interj",
                                        "intr",
                                        "stat",
                                        "rus",
                                        "cardnum",
                                        "ordnum",
                                        "coordconn",
                                        "adp",
                                        "root",
                                        "seq",
                                        "attr",
                                        "exi.neg",
                                        "verb",
                                        "adj>adv",
                                        "vd",
                                        "num>n",
                                        "adj>adv",
                                        "postp",
                                        "conj",
                                        "enclitic",
                                        "num",
                                        "prep",
                                        "pro",
                                        "-",
                                        "conn",
                                    ):
                                        continue
                                    # store the found information
                                    dico[word][gloss] = collection
                # prepare the information for transfer
                for word in dico:
                    if len(dico[word]) < 2:  # skip one letter words
                        continue
                    meaninglist = [x for x in dico[word].keys() if x is not None]
                    meaninglist.sort()
                    # transform the meaninglist to a list of 2-tuples
                    for i, meaning_i in enumerate(meaninglist):
                        if i == len(meaninglist):
                            # avoid going beyond the end of the list with i+1
                            break
                        for j, meaning_j in enumerate(meaninglist[i + 1 :]):
                            # copy the information to the main aggregation dictionary
                            colexification_dic[(meaning_i, meaning_j)][
                                collection
                            ] = True

    strippeddic = {
        key: colexification_dic[key]
        for key in colexification_dic
        if len(colexification_dic[key].keys()) >= threshold
    }
    return strippeddic


if __name__ == "__main__":
    directory = sys.argv[1]
    dic = analyze_colexifications(
        directory, threshold=4, double_files=["268837", "WEW2018", "zauzou-li-0535"]
    )
    sorted_list = sorted([(len(dic[x]), x) for x in dic.keys()], reverse=True)
    print(f"\nfound {len(sorted_list)} colexification candidates")
    print("writing to colexification.json")
    with open("colexification.json", "w") as out:
        out.write(json.dumps(sorted_list))
