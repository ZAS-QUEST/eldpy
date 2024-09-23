import json
import sqlite3
from collections import defaultdict
import humanize
import datetime
import pprint

megatype_d = {"jpg" : "image",
              "png" : "image",
              "image" : "image",
              "mpg" : "video",
              "avi" : "video",
              "mov" : "video",
              "mp4" : "video",
              "video" : "video",
              "wav" : "audio",
              "mp3" : "audio",
              "audio" : "audio",
              "xml" : "xml",
              "eaf" : "xml",
              "flextext" : "xml",
              "txt" : "text",
              "trs" : "text",
                  }

iso_replacements=[
    ("mul", '_', "multiple languages"),
    ("awd", "Generic Arawakan", "Arawakan"),
    ("sai", '_', "Generic South American"),
    ("xep", "Isthmian Script", '_'),
    ("tup", "Generic Tupi", "Tupian"),
    ("zap", "Generic Zapotec", "Eastern Otomanguean"),
    ("qwe", "Generic Quechuan", "Quechuan"),
    ("zxx", '_', "Not a language"),
    ("omq", "Generic Otomanguean", "Otomanguean"),
    ("oto", "Oto-Pame", "Otomanguean"),
    ("cba", "Generic Chibchan", "Chibchan"),
    ("nah", "Generic Nahuatl", "Uto-Aztecan"),
    ("sio", "Generic Siouan", "Siouan"),
    ("alg", "Generic Algonquian", "Algonquian-Blackfoot"),
    ("azc", "Generic Uto-Aztecan", "Uto-Aztecan"),
    ("cai", '_', "Generic Central-American"),
    ("nai", '_', "Generic North-American"),
    ("zho", '_', "Generic Chinese"),
    ("chi", '_', "Generic Chinese"),
    ("myn", "Generic Mayan", "Mayan"),
    ("swa", "Generic Swahili", "Benue-Congo"),
    ("aym", "Generic Aymara", "Aymaran"),
    ("hmo", "Hiri Motu", "Malayo-Polynesian (Main)"),
    ("srp", "Serbian", "Classical Indo-European"),
    ("hrv", "Croatian", "Classical Indo-European"),
    ("est", "Estonian", "Classical Indo-European"),
    ("msa", "Malay", "Malayo-Polynesian (Main)"),
    ("zsm", "Malay", "Malayo-Polynesian (Main)"),
    ("fas", "Persian", "Classical Indo-European"),
    ("nep", "Nepali", "Classical Indo-European"),
    ("ori", "Oriya", "Classical Indo-European"),
    ("ase", "American Sign Language", "Sign language"),
    ("fsl", "Langue des signes française", "Sign language"),
    ("bal", "Balochi", "Classical Indo-European"),
    ("pus", "Pashto", "Classical Indo-European"),
    ("ara", "Arabic", "Semitic"),
    ("twi", "Twi", "Kwa Volta-Congo"),
    ("gba", "Gbaya", "Gbaya-Manza-Ngbaka"),
    ("ful", "Fulfulde", "North-Central Atlantic"),
    ("ger", "German", "Classical Indo-European")
    ]



explict_matches={
    'Hakhun (variety of Nocte)':'njb',
    'Nocte - Namsang variety':'njb',
    'Tangsa - Hakhun variety':'nst',
    'Tangsa - Cholim variety (general name Tonglum)':'nst',
    'Tangsa (Cholim)':'nst',
    'Tangsa - Lochhang variety (general name Langching)':'nst',
    'Tangsa - Bote variety (general name Bongtai)':'nst',
    'Tangsa - Hahcheng variety (general name Hasang)':'nst',
    'Tangsa - Chamchang variety (general name Kimsing)':'nst',
    'Tangsa - Joglei variety (general name Jugly)':'nst',
    'Tangsa - Champang variety (general name Thamphang)':'nst',
    'Tangsa - Haqchum variety':'nst',
    'Tangsa - Khalak variety':'nst',
    'Tangsa - Haqcheng variety (general name Hasang)':'nst',
    'Tangsa - Jiingi variety (general name Donghi)':'nst',
    'Tangsa - Shechhue variety (general name Shangke)':'nst',
    'Tangsa - Moshang variety (general name Mossang)':'nst',
    'Tangsa - Chamkok variety (general name Thamkok)':'nst',
    'Tangsa - Lakki variety':'nst',
    'Tangsa - Hawoi variety (general name Havi)':'nst',
    'Tangsa - Hehle variety (general name Halang)':'nst',
    'Tangsa - Mueshaung':'nst',
    'Tangsa - Ngaimong variety':'nst',
    'Tangsa - Nokya variety':'nst',
    'Tangsa - Gaqlun variety':'nst',
    'Bugis':'bug',
    'Huitoto mïnïka':'hto',
    'Even language':'eve',
    'Hoocąk':'win',
    'Marrku':'mhg-wur',
    'Gunwinggu':'gup',
    'Ngaliwurru':'djd',
    'Djamindjung':'djd',
    'Sami, Akkala':'sja',
    'Saami, Akkala':'sja',
    'Saami, Kildin':'sjd',
    'Sami, Kildin':'sjd',
    'Sami,Kildin':'sjd',
    'Sami, Ter':'sjt',
    'Saami, Ter':'sjt',
    'Sami,Ter':'sjt',
    'Saami, Skolt':'sms',
    'Sami, Skolt':'sms',
    'Sami,Skolt':'sms',
    'Saami, Inari':'smn',
    'Saami, North':'sme',
    'Saami, Pite':'sje',
    'Saami, South':'sma',
    'Chadian Arabic (Dakara dialect)':'shu',
    'Lacandón':'lac',
    'Maya, Yucatán':'yua',
    'Marquesan, North':'mrq',
    'Marquesan, South':'mqm',
    'Kómnzo':'tci',
    'Wára':'tci',
    'Wára (Wära)':'tci',
    'Kómnzo':'tci',
    'Tibetan, Amdo':'adx',
    'Solomon Islands Pijin':'pis',
    'Thai, Southern':'sou',
    'Maniq Tonok':'tnz',
    'Maniq Tonte':'tnz',
    'Batek Deq Kuala Koh':'btq',
    'Batek Teh Pasir Linggi':'btq',
    'Kensiw To':'kns',
    'Kensiw Lubok Legong':'kns',
    'Lanoh Kertei':'lnh',
    'Semnam Malau':'ssm',
    'Batek Teh Sungai Taku':'btq',
    'Batek Teq':'btq',
    'Sanzhi':'dar',
    'Latunde':'ltn',
    'Salamai':'mnd',
    'Mekéns':'skf',
    'Tawande':'xtw',
    'Taa':'nmn',
    'Tai Ahom':'aho',
    'Tai Phake':'phk',
    'Tai Khamyang':'ksu',
    'Trumaí':'tpy',
    'Tuvin':'tyv',
    'Karagas':'mtm',
    'Shor':'cjs',
    'Indonesian':'ind',
    'ENGLISH':'eng',
    'PORTUGUESE':'por',
    'TRUMAÍ':'tpy',
    'Vanga Vanatɨna (Sudest)':'tgo',
    'Tetum Prasa':'tet',
    'Makasai':'mkz',
    'Dakaka':'bpa',
    'Yurakaré':'yuz',
    'Yuracare':'yuz',
    'Malay':'zsm',
    "Anta": "tci",
    "Batek Deq": "btq",
    "BatekTeh": "btq",
    "Bilinarra": "nbj",
    "Hakhi": "njb",
    "Isubu": "szv",
    "Kaili": "kzf",
    "Kentaq Bukit Asu": "",
    "Kuikuro ": "kui",
    "Mawng": "mph",
    "Monguor": "mjg",
    "Nama": "naq",
    "Semnam Air Bah": "ssm",
    "TRUMAI": "tpy",
    "Unknown": "und",
    "Unspecified": "und",
    "Warta Thuntai": "gnt",
    "Wèré": "wei",
    "Fulfulde": "fub"
    }

def round_trip(language_string):
    try:
        isocode = explict_matches[language_string]
        language_name = isod[isocode]['name']
        return language_name
    except KeyError:
        return language_string

def iso2language_name(isocode):
    pruned = isocode.split('-')[-1].lower()
    try:
        language_name = isod[pruned]['name']
    except KeyError:
        return f"_ISO_{isocode}"
    return language_name

d = defaultdict(dict)
lgd = {}
isod = {}
with open("mandanaunits.csv") as infile:
    for line in infile.readlines():
        family, unit, language, iso6393 = line.strip().split('\t')
        lgd[language]={'family':family, 'unit':unit, 'iso6393':iso6393}
        isod[iso6393]={'family':family, 'unit':unit, 'name':language}
lgd['Huitoto'] = {'family':'Huitotoan', 'unit':'Huitotoan', 'iso6393':'hto'}
lgd['Huitoto buue'] = {'family':'Huitotoan', 'unit':'Huitotoan', 'iso6393':'hto'}
for em in explict_matches:
    # print(em, explict_matches[em])
    lgd[em] = {'family':'unknown', 'unit':'unknown', 'iso6393':explict_matches[em]}
iso_replacement_d = {t[0]: {'family':'_', 'unit':t[2], 'name':t[1]} for t in iso_replacements}
isod.update(iso_replacement_d)
language_replacement_d = {t[1]: {'family':'_', 'iso':t[0], 'unit':t[2]} for t in iso_replacements}
for key in language_replacement_d:
    if key in lgd:
        continue
    lgd[key] = language_replacement_d[key]

manylist = []
file2language_manylist = []

with open("tla_copy_f.json") as infile:
    j = json.loads(infile.read())

for collection in j:
    for bundle in j[collection]['bundles']:
        for file_ in j[collection]['bundles'][bundle]['files']:
            url = file_['url']
            id_ = url.split('/')[-1]
            size = file_['size']
            type_ = file_['type_'].lower()
            if type_ == 'jpeg':
                type_ = 'jpg'
            if type_ == 'mpeg':
                type_ = 'mpg'
            megatype = megatype_d.get(type_, '')
            archive = 'TLA'
            onelist = [id_, archive, collection, bundle, megatype, type_, size, 0]
            manylist.append(onelist)
            # if type_ not in "mpg mp4 mov avi wav mp3 xml eaf txt".split():
            #     continue
            languages = [x for field in file_['languages'] for x in field.split('\n')]
            for language_in in languages:
                # print(lgd['Yurakaré'])
                try:
                    iso = lgd[language_in]['iso6393']
                    language = round_trip(language_in)
                    file2language_manylist.append((id_, archive, iso))
                except KeyError:
                    pass
                    # print(language_in)
#                 # try:
#                 #     unit = lgd[language]['unit']
#                 # except KeyError:
#                 #     unit = '_unknown'
#                 # if unit not in d:
#                 #     d[unit] = {'languages':{}}
#                 # try:
#                 #     d[unit][type_]['count'] += 1
#                 #     d[unit][type_]['size'] += size
#                 # except KeyError:
#                 #     d[unit][type_] = {'count': 1, 'size': size, 'duration': 0}
#                 # if language not in d[unit]['languages']:
#                 #     d[unit]['languages'][language] = {}
#                 # try:
#                 #     d[unit]['languages'][language][type_]['count'] += 1
#                 #     d[unit]['languages'][language][type_]['size'] += size
#                 # except KeyError:
#                 #     d[unit]['languages'][language][type_] = {'count': 1, 'size': size, 'duration': 0}


with open("ailla_copy_f.json") as infile:
    j = json.loads(infile.read())

for collection in j:
    for bundle in j[collection]['bundles']:
        for file_ in j[collection]['bundles'][bundle]['files']:
            url = file_['url']
            id_ = url.split('/')[-4]
            size = file_['size']
            type_ = file_['type_'].lower()
            if type_ == 'jpeg':
                type_ = 'jpg'
            if type_ == 'mpeg':
                type_ = 'mpg'
            megatype = megatype_d.get(type_, '')
            archive = "AILLA"
            onelist = [id_, archive, collection, bundle, megatype, type_, size, 0]
            manylist.append(onelist)
            # if type_ not in "mpg mp4 mov avi wav mp3 xml eaf txt".split():
            #     continue
            languages = file_['languages']
            for isocode in languages:
                language  = iso2language_name(isocode)
                file2language_manylist.append((id_,archive, isocode))
                # try:
                #     unit = lgd[language]['unit']
#                 except KeyError:
#                     unit = '_unknown'
#                 if unit not in d:
#                     d[unit] = {'languages':{}}
#                 try:
#                     d[unit][type_]['count'] += 1
#                     d[unit][type_]['size'] += size
#                 except KeyError:
#                     d[unit][type_] = {'count': 1, 'size': size, 'duration': 0}
#                 if language not in d[unit]['languages']:
#                     d[unit]['languages'][language] = {}
#                 try:
#                     d[unit]['languages'][language][type_]['count'] += 1
#                     d[unit]['languages'][language][type_]['size'] += size
#                 except KeyError:
#                     d[unit]['languages'][language][type_] = {'count': 1, 'size': size, 'duration': 0}
#
#
with open("paradisec_copy_f.json") as infile:
    j = json.loads(infile.read())

for collection in j:
    for bundle in j[collection]['bundles']:
        for file_ in j[collection]['bundles'][bundle]['files']:
            url = file_['url']
            id_ = file_['name']
            # print(id_)
            size = file_['size']
            type_ = file_['type_'].lower().split('/')[-1]
            duration_tmp = file_['duration'].lower()
            #convert to seconds
            try:
                duration = sum(x * float(t) for x, t in zip([1, 60, 3600], reversed(duration_tmp.split(":"))))
            except ValueError:
                duration = 0
            if type_ == 'jpeg':
                type_ = 'jpg'
            if type_ == 'mpeg':
                type_ = 'mpg'
            if type_ == 'vnd.wav':
                type_ = 'wav'
            if type_ == 'eaf+xml':
                type_ = 'eaf'
            if type_ == 'flextext+xml':
                type_ = 'flex'
            # if type_ in 'wav vnd.wav mp3'.split():
            #     type_ = 'audio'
            # if type_ in 'png jpg tiff'.split():
            #     type_ = 'image'
            # if type_ in 'mp4 mpg webm mov avi'.split():
            #     type_ = 'video'
            # if type_ not in "mpg mp4 mov avi wav mp3 xml eaf txt webm vnd.wav audio video text image flex".split():
            #     continue
            archive = 'PARADISEC'
            megatype = megatype_d.get(type_, '')
            onelist = [id_, archive, collection, bundle, megatype, type_, size, duration]
            manylist.append(onelist)
            languages = file_['languages']
            for isocode in languages:
                language = iso2language_name(isocode)
                file2language_manylist.append((id_, archive, isocode))
#                 try:
#                     unit = lgd[language]['unit']
#                 except KeyError:
#                     unit = '_unknown'
#                 if unit not in d:
#                     d[unit] = {'languages':{}}
#                 try:
#                     d[unit][type_]['count'] += 1
#                     d[unit][type_]['size'] += size
#                     d[unit][type_]['duration'] += duration
#                 except KeyError:
#                     d[unit][type_] = {'count': 1, 'size': size, 'duration': duration}
#                 if language not in d[unit]['languages']:
#                     d[unit]['languages'][language] = {}
#                 try:
#                     d[unit]['languages'][language][type_]['count'] += 1
#                     d[unit]['languages'][language][type_]['size'] += size
#                     d[unit]['languages'][language][type_]['duration'] += duration
#                 except KeyError:
#                     d[unit]['languages'][language][type_] = {'count': 1, 'size': size, 'duration': duration}


# with open("thomasout.json") as infile:
#     j = json.loads(infile.read())
#     for key in j:
#         id_=key.split('|')[-1]
#         l = j[key]
#         ld = {x['name'] : x['value'] for x in l}
#         size = ld.get('xip.size_r_Display',0)
#         types = ld.get('imdi.mediaFileFormat', '')
#         imdi_lgs = ld.get('imdi.languageId', [])
#         languages = [lg.split(':')[-1] for lg in imdi_lgs if ':' in lg]
#         for type_ in types:
#             type_ = type_.split('/')[0].lower()
#             # print(type_,imdi_lgs,size)
#             if type_ == 'jpeg':
#                 type_ = 'jpg'
#             if type_ == 'mpeg':
#                 type_ = 'mpg'
#             megatype = megatype_d.get(type_, '')
#             archive = 'ELAR'
#             onelist = [id_, archive, collection, bundle, megatype, type_, size, 0]
#             manylist.append(onelist)
#             # if type_ not in "mpg mp4 mov avi wav mp3 xml eaf txt".split():
#             #     continue
#             for isocode in languages:
#                 language = iso2language_name(isocode)
#                 file2language_manylist.append((id_, archive, language))
#                 try:
#                     unit = lgd[language]['unit']
#                 except KeyError:
#                     unit = '_unknown'
#                 if unit not in d:
#                     d[unit] = {'languages':{}}
#                 try:
#                     d[unit][type_]['count'] += 1
#                     d[unit][type_]['size'] += size
#                 except KeyError:
#                     d[unit][type_] = {'count': 1, 'size': size, 'duration': 0}
#                 if language not in d[unit]['languages']:
#                     d[unit]['languages'][language] = {}
#                 try:
#                     d[unit]['languages'][language][type_]['count'] += 1
#                     d[unit]['languages'][language][type_]['size'] += size
#                 except KeyError:
#                     d[unit]['languages'][language][type_] = {'count': 1, 'size': size, 'duration': 0}
# with open('test.json', 'w', encoding='utf8') as out:
#     out.write(json.dumps(d, indent=4, sort_keys=True,ensure_ascii=False))
#
# with  open('report.txt', 'w', encoding='utf8') as out:
#     for unit in sorted(d.keys()):
#         out.write(f'\n{unit}: ')
#         for field in d[unit]:
#             if field != 'languages':
#                 out.write(f'{field}:{d[unit][field]["count"]} '.replace(' Bytes',''))
#         for language in sorted(d[unit]['languages'].keys()):
#             out.write(f'\n  {language}: ')
#             for field2 in d[unit]['languages'][language]:
#                 out.write(f'{field2}:{d[unit]["languages"][language][field2]["count"]} '.replace(' Bytes',''))
#                 if d[unit]["languages"][language][field2]["duration"] > 0:
#                     out.write(f'[{datetime.timedelta(seconds = int(d[unit]["languages"][language][field2]["duration"]))}] ')
#
# with  open('report_units_elar.csv', 'w', encoding='utf8') as out:
#     out.write('Unit\tVideo\tSize\tDuration\tAudio\tSize\tDuration\tEAF\tSize\tDuration\tXML\tSize\tDuration')
#     for unit in sorted(d.keys()):
#         out.write(f'\n{unit}\t')
#         for field in 'video audio eaf xml'.split():
#             try:
#                 out.write(f'{d[unit][field]["count"]}\t{d[unit][field]["size"]}\t{int(d[unit][field]["duration"])}\t')
#             except KeyError:
#                 out.write('\t\t\t')
#
# with  open('report_lgs_elar.csv', 'w', encoding='utf8') as out:
#     out.write('Language\tVideo\tSize\tDuration\tAudio\tSize\tDuration\tEAF\tSize\tDuration\tXML\tSize\tDuration')
#     for unit in sorted(d.keys()):
#         for language in d[unit]['languages']:
#             out.write(f'\n{language}\t')
#             current_lg = d[unit]['languages'][language]
#             for field in 'video audio eaf xml'.split():
#                 try:
#                     out.write(f'{current_lg[field]["count"]}\t{current_lg[field]["size"]}\t{int(current_lg[field]["duration"])}\t')
#                 except KeyError:
#                     out.write('\t\t\t')

# CREATE TABLE delaman_report.files(ID TEXT, archive TEXT NOT NULL, collection TEXT NOT NULL, bundle TEXT, megatype TEXT, filetype TEXT NOT NULL, size int, length int, PRIMARY KEY (ID, archive));

connection = sqlite3.connect('/home/snordhoff/git/eldpy/eldpy/delaman_report.db')
cursor = connection.cursor()
# sql_insertstring = f"INSERT INTO files VALUES ({},{},{})")
# cursor.execute(sql_insertstring)
# sql_insert_many_list = [(1,2,3,4,5,6,7,8),(9,8,9,0,1,2,3,4)]
# pprint.pprint(manylist)
# for ml in manylist:
#     try:
#         cursor.execute("INSERT INTO files VALUES(?,?,?,?,?,?,?,?)", ml)
#     except sqlite3.IntegrityError:
#         pass
        # print(ml)
for mlg in set(file2language_manylist):
    try:
        # print(mlg)
        cursor.execute("INSERT INTO languages VALUES(?,?,?)", mlg)
    except sqlite3.IntegrityError:
        # print(mlg)
        pass
# cursor.executemany("INSERT INTO files VALUES(?,?,?,?,?,?,?,?)", manylist)
# cursor.executemany("INSERT INTO languages VALUES(?,?)", file2language_manylist)
connection.commit()
connection.close()


