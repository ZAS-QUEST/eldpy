pprint.pprint([len(sentenceID[key]) for c in j for f in j[c] for tiertype in j[c][f] for tierID in j[c][f][tiertype] for sentenceID  in j[c][f][tiertype][tierID] for key in sentenceID])

d = {}
for archive in ("anla","paradisec", "elar", 'tla', 'ailla'):
 j = json.loads(open("%s.json"%archive.upper()).read())
 d[archive] = Counter(" ".join([sentence for c in j for f in j[c] for tier in j[c][f] for sentence in tier] ))

print(json.dumps(d, sort_keys=True, ensure_ascii=False))


d = {}
for archive in ("anla","paradisec", "elar", 'tla', 'ailla'):
    g = json.loads(open("../glosses/%s.json"%archive.upper()).read())
    glosses =  [pairing[1] for c in g for f in g[c] for typ in g[c][f] for tier in g[c][f][typ] for sentence in g[c][f][typ][tier] for pairing in sentence for stuff in sentence for pairing in sentence[stuff] if pairing[1] is not None and  pairing[1].lower()==pairing[1] and pairing[1] not in ('stem', 'root', 'v', 'suffix', 'prefix',  'n', 'bound', 'enclitic', 'proclitic','mrph') and '-' not in pairing[1] and ':' not in pairing[1] and " " not in pairing[1] and "$" not in pairing[1] and "+" not in pairing[1] and "=" not in pairing[1] and "." not in pairing[1] ]
    tmp =   Counter(glosses)
    d[archive] = tmp.most_common(50)

pprint.pprint(d)


elarj = json.loads(open('ELAR.json').read())
g = elarj
elarg = [pairing for c in g for f in g[c] for typ in g[c][f] for tier in g[c][f][typ] for sentence in g[c][f][typ][tier] for pairing in sentence for stuff in sentence for pairing in sentence[stuff] if pairing[1] is not None and  pairing[1].lower()==pairing[1] and pairing[1] not in ('stem', 'root', 'v', 'suffix', 'prefix',  'n', 'bound', 'enclitic', 'proclitic','mrph') and '-' not in pairing[1] and ':' not in pairing[1] and " " not in pairing[1] and "$" not in pairing[1] and "+" not in pairing[1] and "=" not in pairing[1] and "." not in pairing[1] ]

d = defaultdict(list)
for p in elarg:
 d[p[1]].append(p[0])
 e = d{k:list(set(d[k])) for k in d}
{k:len(e[k]) for k in e if len(e[k])>50}

import pprint
from collections import defaultdict, Counter
d = defaultdict(int)
for archive in ["AILLA","ANLA","ELAR","PARADISEC","TLA"]:
    print("processing", archive)
    lines = open('tierranks-%s.txt'%archive).readlines()
    for line in lines:
        v,k = line.strip().split(':')
        d[k] += int(v)

pprint.pprint(d)



>>> len(d)
2187
>>> sum([d[v] for v in d])
20089
>>>

values = sorted([d[v] for v in d])[::-1]
labels = values[:38]
squarify.plot(
    sizes=values,
    label=labels,
    color=[cm.pink(x * 0.1) for x in [2, 8, 4, 7, 1, 6, 3, 9, 5]],
)  # jumble colormap
plt.axis("off")
plt.savefig("tiertypetreemap-all.png")


import matplotlib.pyplot as plt
fig, ax = plt.subplots()
plt.xlabel('Number of tier structures covered')
plt.ylabel('Number of files covered')
plt.xlim(0,110)
plt.ylim(0,21000)
g=f[:110]
ax.scatter(range(len(g)),g,s=1)
plt.savefig("asymptote2.pdf")


from Crypto.Cipher import ARC4
from Crypto.Hash import SHA
from Crypto.Random import get_random_bytes
import binascii



##salt = json.loads(session.get("https://elar.soas.ac.uk/AJAX/JSON?method=getSalt").text)["data"]
##encodeURIComponent_pw = password
##unescaped_pw = encodeURIComponent_pw
##base64pw =  base64.b64encode(bytes(unescaped_pw,encoding='latin1'))
##cipher = ARC4.new(salt)
##rc4Encrypt_pw = cipher.encrypt(base64pw)
##hexed_pw = binascii.hexlify(rc4Encrypt_pw)
##print(hexed_pw)
##password needs to be salted and hashed
##
##https://elar.soas.ac.uk/themes/elar/js/common.js?_=1456746694
##password = rc4Encrypt(salt, btoa(unescape(encodeURIComponent(password))));
##// hex encode the encrypted password
##password = hexEncode(password);

##http://api.drupalhelp.net/api/simplenews_statistics/rc4.inc/function/rc4Encrypt/6.2
##https://docs.python.org/3/library/base64.html
##https://www.w3schools.com/jsref/met_win_btoa.asp
##https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/encodeURIComponent
##https://gist.github.com/valentinkostadinov/5875467

##https://pycryptodome.readthedocs.io/en/latest/src/cipher/arc4.html
##>>> key = b'Very long and confidential key'
##>>> nonce = get_random_bytes(16)
##>>> tempkey = SHA.new(key+nonce).digest()
##>>> cipher = ARC4.new(tempkey)
##>>> msg = nonce + cipher.encrypt(b'Open the pod bay doors, HAL')
