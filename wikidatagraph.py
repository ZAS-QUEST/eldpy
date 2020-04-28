import wptools
import json
import sys
import wikidata_ids

def process(ID):
    global d #stores the found items
    global queuelength
    if queuelength > 1000:
        print int(queuelength/1000)*'K', ID
    elif queuelength > 100:
        print int(queuelength/100)*'C', ID
    else:
        print queuelength*'Q', ID
    queuelength -= 1
    if ID == 'novalue': #wptools returns this string, rather than None
        return
    #setup query
    page = wptools.page(wikibase=ID, silent=True, skip=['imageinfo','labels','requests']) #
    #execute query
    page.get_wikidata()
    #279 is the code for sublass_of
    p279s =  page.data['claims'].get('P279')
    #31 is the code for instance_of
    p31s = page.data['claims'].get('P31')
    #store retrieved data
    d[ID] = {'p31s':p31s, 'p279s':p279s}
    if p279s is None:
        p279s = []
    #setup recursion for superclasses, but skip items we already know or which are already in the queue
    new279s = [p for p in p279s if p not in d and p not in initqueue]
    queuelength += len(new279s)
    if p31s is None:
        p31s = []
    #setup recursion for categories, but skip items we already know or which are already in the queue
    new31s = [p for p in p31s if p not in d and p not in initqueue]
    queuelength += len(new31s)
    #execute recursions
    for super_id in new279s:
        process(super_id)
    for super_id in new31s:
        process(super_id)


if __name__ == "__main__":
    """retrieve all superclasses and categories from wikidata, for IDs in a list"""

    #the wptool module we use pollutes STDERR with useless messages, so we disable this
    print "stderr redirected to log.txt"
    sys.stderr = open('log.txt','w')
    #read cached info to reduce load on wikidata server
    d = json.loads(open('superclasses.json').read())
    print len(d), "cached items"
    #limit list for testing purposes
    LIMIT = 999999
    LIMIT = 500
    #we are only interested in info which is not already in the cache
    initqueue = [x for x in wikidata_ids.wikidata_ids if x not in d][:LIMIT]
    queuelength = len(initqueue)
    print "retrieving parents for %i items from wikidata" %len(initqueue)
    for wikidata_id in initqueue:
        process(wikidata_id)
    #store cached data
    with open('superclasses.json', 'w') as out:
        out.write(json.dumps(d, indent=4, sort_keys=True))

