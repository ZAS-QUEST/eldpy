import json
import pprint

infile = open('paradisec.json')
oldj = json.loads(infile.read())
infile.close()

d = {}
for key in oldj:
    s = key.split('/')
    nix, nixx, collection, nixxx, ID = s 
    ELAN = oldj[key]
    #print(collection,ID,ELAN)
    if collection in d:  
        try: 
            d[collection][ID]+=ELAN
        except KeyError:
            d[collection][ID]=ELAN
    else:
         d[collection]={ID:ELAN}
         
outfile =  open('newparadisec.json', 'w')
outfile.write(json.dumps(d, indent=4, sort_keys=True))
outfile.close()


