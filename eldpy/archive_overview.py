import json
from collections import defaultdict
import humanize
import datetime



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


with open("tla_copy_f.json") as infile:
    j = json.loads(infile.read())

for collection in j:
    for bundle in j[collection]['bundles']:
        for file_ in j[collection]['bundles'][bundle]['files']:
            url = file_['url']
            size = file_['size']
            type_ = file_['type_'].lower()
            if type_ == 'jpeg':
                type_ = 'jpg'
            if type_ == 'mpeg':
                type_ = 'mpg'
            if type_ not in "mpg mp4 mov avi wav mp3 xml eaf txt".split():
                continue
            languages = [x for field in file_['languages'] for x in field.split('\n')]
            for language_in in languages:
                language = round_trip(language_in)
                try:
                    unit = lgd[language]['unit']
                except KeyError:
                    unit = '_unknown'
                if unit not in d:
                    d[unit] = {'languages':{}}
                try:
                    d[unit][type_]['count'] += 1
                    d[unit][type_]['size'] += size
                except KeyError:
                    d[unit][type_] = {'count': 1, 'size': size, 'duration': 0}
                if language not in d[unit]['languages']:
                    d[unit]['languages'][language] = {}
                try:
                    d[unit]['languages'][language][type_]['count'] += 1
                    d[unit]['languages'][language][type_]['size'] += size
                except KeyError:
                    d[unit]['languages'][language][type_] = {'count': 1, 'size': size, 'duration': 0}


with open("ailla_copy_f.json") as infile:
    j = json.loads(infile.read())

for collection in j:
    for bundle in j[collection]['bundles']:
        for file_ in j[collection]['bundles'][bundle]['files']:
            url = file_['url']
            size = file_['size']
            type_ = file_['type_'].lower()
            if type_ == 'jpeg':
                type_ = 'jpg'
            if type_ == 'mpeg':
                type_ = 'mpg'
            # if type_ not in "mpg mp4 mov avi wav mp3 xml eaf txt".split():
            #     continue
            languages = file_['languages']
            for isocode in languages:
                language  = iso2language_name(isocode)
                try:
                    unit = lgd[language]['unit']
                except KeyError:
                    unit = '_unknown'
                if unit not in d:
                    d[unit] = {'languages':{}}
                try:
                    d[unit][type_]['count'] += 1
                    d[unit][type_]['size'] += size
                except KeyError:
                    d[unit][type_] = {'count': 1, 'size': size, 'duration': 0}
                if language not in d[unit]['languages']:
                    d[unit]['languages'][language] = {}
                try:
                    d[unit]['languages'][language][type_]['count'] += 1
                    d[unit]['languages'][language][type_]['size'] += size
                except KeyError:
                    d[unit]['languages'][language][type_] = {'count': 1, 'size': size, 'duration': 0}


with open("paradisec_copy_f.json") as infile:
    j = json.loads(infile.read())

for collection in j:
    for bundle in j[collection]['bundles']:
        for file_ in j[collection]['bundles'][bundle]['files']:
            url = file_['url']
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
            if type_ == 'eaf+xml':
                type_ = 'eaf'
            if type_ == 'flextext+xml':
                type_ = 'flex'
            if type_ in 'png jpg tiff':
                type_ = 'image'
            if type_ not in "mpg mp4 mov avi wav mp3 xml eaf txt webm vnd.wav audio video text image flex".split():
                continue
            languages = file_['languages']
            for isocode in languages:
                language = iso2language_name(isocode)
                try:
                    unit = lgd[language]['unit']
                except KeyError:
                    unit = '_unknown'
                if unit not in d:
                    d[unit] = {'languages':{}}
                try:
                    d[unit][type_]['count'] += 1
                    d[unit][type_]['size'] += size
                    d[unit][type_]['duration'] += duration
                except KeyError:
                    d[unit][type_] = {'count': 1, 'size': size, 'duration': duration}
                if language not in d[unit]['languages']:
                    d[unit]['languages'][language] = {}
                try:
                    d[unit]['languages'][language][type_]['count'] += 1
                    d[unit]['languages'][language][type_]['size'] += size
                    d[unit]['languages'][language][type_]['duration'] += duration
                except KeyError:
                    d[unit]['languages'][language][type_] = {'count': 1, 'size': size, 'duration': duration}


with open("thomasout.json") as infile:
    j = json.loads(infile.read())
    for key in j:
        id_=key.split('|')[-1]
        l = j[key]
        ld = {x['name'] : x['value'] for x in l}
        size = ld.get('xip.size_r_Display',0)
        types = ld.get('imdi.mediaFileFormat', '')
        imdi_lgs = ld.get('imdi.languageId', [])
        languages = [lg.split(':')[-1] for lg in imdi_lgs if ':' in lg]
        for type_ in types:
            type_ = file_['type_'].lower()
            if type_ == 'jpeg':
                type_ = 'jpg'
            if type_ == 'mpeg':
                type_ = 'mpg'
            # if type_ not in "mpg mp4 mov avi wav mp3 xml eaf txt".split():
            #     continue
            for isocode in languages:
                language = iso2language_name(isocode)
                try:
                    unit = lgd[language]['unit']
                except KeyError:
                    unit = '_unknown'
                if unit not in d:
                    d[unit] = {'languages':{}}
                try:
                    d[unit][type_]['count'] += 1
                    d[unit][type_]['size'] += size
                except KeyError:
                    d[unit][type_] = {'count': 1, 'size': size, 'duration': 0}
                if language not in d[unit]['languages']:
                    d[unit]['languages'][language] = {}
                try:
                    d[unit]['languages'][language][type_]['count'] += 1
                    d[unit]['languages'][language][type_]['size'] += size
                except KeyError:
                    d[unit]['languages'][language][type_] = {'count': 1, 'size': size, 'duration': 0}
with open('test.json', 'w', encoding='utf8') as out:
    out.write(json.dumps(d, indent=4, sort_keys=True,ensure_ascii=False))

with  open('report.txt', 'w', encoding='utf8') as out:
    for unit in sorted(d.keys()):
        out.write(f'\n{unit}: ')
        for field in d[unit]:
            if field != 'languages':
                out.write(f'{field}:{d[unit][field]["count"]} ({humanize.naturalsize(d[unit][field]["size"])}) '.replace(' Bytes',''))
        for language in d[unit]['languages']:
            out.write(f'\n  {language}: ')
            for field2 in d[unit]['languages'][language]:
                out.write(f'{field2}:{d[unit]["languages"][language][field2]["count"]} ({humanize.naturalsize(d[unit]["languages"][language][field2]["size"])}) '.replace(' Bytes',''))
                if d[unit]["languages"][language][field2]["duration"] > 0:
                    out.write(f'[{datetime.timedelta(seconds = int(d[unit]["languages"][language][field2]["duration"]))}] ')





