import json
import glob
from collections import defaultdict
import pprint

#language = 'abc'
colexification_dic = defaultdict(dict)
dico = defaultdict(dict)
#FIXME forloop collections
for fn in glob.glob('../cache/glosses/*'):
    print(fn)
    j = json.loads(open(fn).read())
    for a in j: #there is only one archive in the json file
        for eaf in j[a]:
            collection = eaf.split('/')[1]
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
                                if " " in gloss: #most likely a multi-gloss item
                                    continue
                                dico[word][gloss] = True
    #print(dico)
    for word in dico:
        if len(dico[word])<2:
            continue
        meaninglist= [x for x in dico[word].keys() if x is not None]
        meaninglist.sort()
        for i, meaning in enumerate(meaninglist[:-1]):
            meaning1 = meaninglist[i]
            meaning2 = meaninglist[i+1]
            colexification_dic[(meaning1,meaning2)][collection] = True

pprint.pprint(colexification_dic)
