import json
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re

#GLOSSFILE = json.loads(open('glosses-tlaeafs.json').read())
#glossdocuments = [" ".join([x for x in GLOSSFILE[f][type_][tier][1]]) for f in GLOSSFILE for type_ in GLOSSFILE[f] for tier in GLOSSFILE[f][type_] ]


TRANSLATIONSFILE = json.loads(open('cache/translations/PARADISEC.json').read())
#translationdocuments = [sentence
                        #for collection in TRANSLATIONSFILE
                        #for eaf in TRANSLATIONSFILE[collection]
                        #for type_ in TRANSLATIONSFILE[collection][eaf]
                        #for tier in type_
                        #for sentence in tier
                        #if len(sentence.split())>4]

translationdocuments = [sentence  for collection in TRANSLATIONSFILE for eaf in TRANSLATIONSFILE[collection] if TRANSLATIONSFILE[collection][eaf]  != [] for tier in TRANSLATIONSFILE[collection][eaf] for sentence in tier if len(sentence.split())>4]




#documents = [" ".join([x for x in JSONFILE[f][type_][tier][1] if re.search("^[^a-z]+$", x) and re.search("[A-Z]", x)]) for f in JSONFILE for type_ in JSONFILE[f] for tier in JSONFILE[f][type_] ]

translationtfidf = TfidfVectorizer().fit_transform(translationdocuments)
# no need to normalize, since Vectorizer will return normalized tf-idf
translationpairwise_similarity = translationtfidf * translationtfidf.T

translationarr = translationpairwise_similarity.toarray()
np.fill_diagonal(translationarr, np.nan)    #no self sim
mostsimilardocnumberstranslation = [np.nanargmax(translationarr[x]) for x, throwaway in enumerate(translationarr)]
mostsimilardocumentstranslation = [ (np.nanargmax(translationarr[x]),translationdocuments[np.nanargmax(translationarr[x])]) for x, throwaway in enumerate(translationarr)]

def match_until_loop(i, exclude=[], printold=True):
    old = i
    new = mostsimilardocnumberstranslation[i]
    oldstring = translationdocuments[old]
    newstring = translationdocuments[new]
    if printold:
        print("%s: %s"%(old, oldstring))
    print("%s: %s"%(new, newstring))
    newexlude = exclude + [old, new]
    #print(newexlude)
    if old in exclude:
        print("full circle at", old)
        return
    match_until_loop(new, exclude = newexlude, printold=False)
