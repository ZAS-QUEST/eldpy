"""retrieve all superclasses and categories from wikidata, for IDs in a list"""

import json
import time
import wptools
import wikidata_ids


def process(ID, first=False):
    """find all classes this ID subclasses and recurse"""
    global d  # stores the found items
    global queuelength
    time.sleep(0.1)
    if queuelength > 1000:
        print int(queuelength/1000)*'K', ID
    elif queuelength > 100:
        print int(queuelength/100)*'C', ID
    else:
        print queuelength*'Q', ID
    #we are working on an item off the queue
    queuelength -= 1
    if ID == "novalue":  # wptools returns this string, rather than None
        return
    # setup query
    page = wptools.page(
        wikibase=ID, silent=True, skip=["imageinfo", "labels", "requests"]
    )  #
    # execute query
    try:
        page.get_wikidata()
    except LookupError:
        return
    # 279 is the code for sublass_of
    p279s = page.data["claims"].get("P279")
    # 31 is the code for instance_of
    if first: #we only allow instance_of at leaves of the tree, otherwise we get "class is_instance of metaclass" predicates, which we do not want.
        p31s = page.data["claims"].get("P31")
    else:
        p31s = []
    # store retrieved data
    d[ID] = {"p31s": p31s, "p279s": p279s}
    if p279s is None:
        p279s = []
    # setup recursion for superclasses; skip items we already know or which are already in the queue
    new279s = [p for p in p279s if p not in d and p not in initqueue]
    queuelength += len(new279s)
    if p31s is None:
        p31s = []
    # setup recursion for categories; skip items we already know or which are already in the queue
    new31s = [p for p in p31s if p not in d and p not in initqueue]
    queuelength += len(new31s)
    # execute recursions
    for super_id in new279s:
        process(super_id)
    for super_id in new31s:
        process(super_id)


if __name__ == "__main__":

    # the wptool module we use pollutes STDERR with useless messages, so we disable this
    # print "stderr redirected to log.txt"
    # sys.stderr = open('log.txt','a')
    # read cached info to reduce load on wikidata server
    deletedpages = ["Q6481826", "Q7504509"]
    d = json.loads(open("superclasses.json").read())
    print len(d), "cached items"
    # limit list for testing purposes
    LIMIT = 999999
    # LIMIT = 100
    # we are only interested in info which is not already in the cache
    initqueue = [
        x for x in wikidata_ids.wikidata_ids if x not in d and x not in deletedpages
    ][:LIMIT]
    queuelength = len(initqueue)
    print "retrieving parents for %i items from wikidata" % len(initqueue)
    for wikidata_id in initqueue:
        print (wikidata_id)
        process(wikidata_id, first=True)
    # store cached data
    with open("superclasses.json", "w") as out:
        out.write(json.dumps(d, indent=4, sort_keys=True))
