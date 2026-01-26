import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import lingtypology
import json
from webglottolog import string2glottocode
import math

EXCLUDELANGUAGES = """where languagecode != 'eng'
                and languagecode != 'spa'
                and languagecode != 'rus'
                and languagecode != 'por'
                and languagecode != 'ind'
                and languagecode != 'tpi'
                and languagecode != 'fra'
                and languagecode != 'swh'
                and languagecode != '_Chinese, Mandarin'
                and languagecode != '_Chinese'
                """

def totalcount(df,dimension):
    try:
        v = df[f"video{dimension}"]
    except KeyError:
        v = 0
    try:
        a = df[f"audio{dimension}"]
    except KeyError:
        a = 0
    try:
        x = df[f"xml{dimension}"]
    except KeyError:
        x = 0
    return v+a+x

def get_df(sql):
    connection = sqlite3.connect('delaman2025a.db')
    df = pd.read_sql_query(sql, connection)
    connection.close()
    return df


def plot_totalfiles(log=False):
    sql = f"""SELECT languagecode, count(id) as total
                FROM languagesfiles
                {EXCLUDELANGUAGES}
                GROUP BY languagecode;
                """
    df = get_df(sql)


    df = df.sort_values("total", ascending=False)
    plt.figure(figsize=(12,6))
    plt.bar(df["languagecode"], df["total"])
    log_addendum = ''
    if log:
        plt.yscale("log")        # log scale
        log_addendum=("_log")

    n = len(df)
    tick_positions = np.arange(0, n, 200)

    plt.xticks(tick_positions, tick_positions)   # show labels = rank/index
    plt.tick_params(axis='x', which='both', length=4)  # visible tick marks
    plt.xticks(tick_positions, tick_positions, rotation=45)

    plt.xlabel("rank")

    plt.ylabel("total")
    if log:
        plt.ylabel("total (log scale)")
    plt.title(f"Total files per language across the four archives")
    # plt.show()

    plt.savefig(f"files_per_languages_{log_addendum}.png", dpi=300, bbox_inches="tight")

    # plt.tight_layout()
    plt.close()




def plot_languages():
    sql = f"""SELECT archive, COUNT(DISTINCT(languagecode)) as count
                FROM languagesfiles
                GROUP BY archive;
                """
    df = get_df(sql)

    # print(df)

    values = df[f"count"].tolist()
    archives = df["archive"].tolist()


    # bottoms = np.cumsum([0] + values[:-1])

    plt.figure(figsize=(5,7))
    plt.bar(df["archive"], df["count"])


    plt.ylabel("count")
    plt.title(f"Languages covered")
    plt.legend()

    plt.tight_layout()
    # plt.show()
    plt.savefig(f"languages.png", dpi=300, bbox_inches="tight")

    plt.close()


def plot_phyla():
    sql = f"""SELECT archive, COUNT(DISTINCT(phylum)) as count
                FROM languagesfiles, phyla
                WHERE phyla.languagecode=languagesfiles.languagecode
                GROUP BY archive;
                """
    df = get_df(sql)

    # print(df)

    values = df[f"count"].tolist()
    archives = df["archive"].tolist()


    bottoms = np.cumsum([0] + values[:-1])

    plt.figure(figsize=(5,7))
    plt.bar(df["archive"], df["count"])


    plt.ylabel("count")
    plt.title(f"Phyla covered")
    plt.legend()

    plt.tight_layout()
    # plt.show()
    plt.savefig(f"phyla.png", dpi=300, bbox_inches="tight")

    plt.close()


def stacked_plot(mime,dimension):
    sql = f"""SELECT archive, {dimension}s
                FROM archive{dimension}s
                WHERE megatype='{mime}';"""
    df = get_df(sql)

    # print(df)

    values = df[f"{dimension}s"].tolist()
    archives = df["archive"].tolist()


    bottoms = np.cumsum([0] + values[:-1])

    plt.figure(figsize=(5,7))

    for archive, value, bottom in zip(archives, values, bottoms):
        plt.bar(0, value, bottom=bottom, label=archive)

    plt.xticks([])      # no x-axis ticks for a single bar
    plt.ylabel("count")
    plt.title(f"Holdings of {mime} in {dimension}")
    plt.legend()

    plt.tight_layout()
    # plt.show()
    plt.savefig(f"stacked_{mime}_{dimension}.png", dpi=300, bbox_inches="tight")

    # plt.tight_layout()
    plt.close()



def archive_plot(archive, measure):
    sql = f"""SELECT archive, megatype, {measure}(bytes) as value
                FROM files
                WHERE archive = '{archive}'
                AND megatype != ''
                GROUP BY megatype;"""
    df = get_df(sql)
    print(archive, measure, 'bytes')
    # print(df)

    values = df["value"].tolist()
    types = df["megatype"].tolist()


    plt.figure(figsize=(5,7))
    plt.bar(df["megatype"], df["value"])


    if measure == 'count':
        label = 'files'
    if measure == 'sum':
        label = 'bytes'
    plt.ylabel(measure)
    plt.title(f"Holdings of {archive} in {label}")
    plt.legend()

    plt.tight_layout()
    # plt.show()
    plt.savefig(f"{archive}_in_{label}.png", dpi=300, bbox_inches="tight")

    # plt.tight_layout()
    plt.close()



def rankplot(level, mime, dimension, sql, log=False, aggregatefunction=totalcount):
    df = get_df(sql)

    # df["total"] = df["videocount"] + df["audiocount"] + df["xmlcount"]
    df["total"] = aggregatefunction(df,dimension)


    df = df.sort_values("total", ascending=False)

    plt.figure(figsize=(12,6))
    plt.bar(df["code"], df["total"])
    # plt.yscale()        # log scale
    # log = ""
    # log = "_log"
    log_addendum = ''
    if log:
        plt.yscale("log")        # log scale
        log_addendum=("_log")

    n = len(df)
    tick_positions = np.arange(0, n, 200)

    plt.xticks(tick_positions, tick_positions)   # show labels = rank/index
    plt.tick_params(axis='x', which='both', length=4)  # visible tick marks
    plt.xticks(tick_positions, tick_positions, rotation=45)

    plt.xlabel("rank")

    plt.ylabel("total")
    if log:
        plt.ylabel("total (log scale)")
    plt.title(f"Total {mime}{dimension} per  {level} across the four archives")


    plt.savefig(f"{mime}{dimension}_per_{level}{log_addendum}.png", dpi=300, bbox_inches="tight")

    # plt.tight_layout()
    plt.close()


def plot_zero_records():
    sql="""select languagecode from (SELECT phyla.languagecode,count(id) as count  FROM  phyla
            LEFT JOIN languagesfiles ON phyla.languagecode=languagesfiles.languagecode group by phyla.languagecode) where count=0;"""
    df = get_df(sql)
    isos = df[df["languagecode"].str.len().isin([3])]["languagecode"].tolist()
    # isos=['eng','fra']
    # print(isos)
    with open('isoglotto2.json') as jsonin:
        glottolog_d = json.load(jsonin)
    bare_glottocodes = [glottolog_d.get(iso) for iso in isos]
    # d={bare_glottocodes[i]:isos[i] for i in range(len(isos))}
    # with open('isoglotto.json', 'w') as jsonout:
    #     jsonout.write(json.dumps(d))
    glottocodes = [x for x in bare_glottocodes if x]
    # print(glottocodes)

    m = lingtypology.LingMap(glottocodes, glottocode=True)
    m.tiles = "openstreetmap"
    m.create_map()
    fname = f"zero_records.png"
    print(f"saving to {fname}")
    m.save_static(fname=fname)
    # image = fname
    # crop(image, (200, 20, 1230, 600), 'otclgs.png')

def mime_gradient_map(mime):
    sql=f"""SELECT languagecode, {mime}count AS count
            FROM fulljoin{mime}s
            WHERE languagecode != 'eng'
            AND languagecode != 'spa'
            AND languagecode != 'rus'
            AND languagecode != 'por'
            AND languagecode != 'ind'
            AND languagecode != 'swh'
            AND languagecode != 'tpi'
            AND languagecode != 'fra';"""
    df = get_df(sql)
    # isos=['eng','fra']
    # print(isos)
    # with open('isoglotto2.json') as jsonin:
    #     glottolog_d = json.load(jsonin)
    # bare_glottocodes = [glottolog_d.get(iso) for iso in isos]

    isos = df["languagecode"].tolist()
    counts = df["count"].tolist()
    counts = [0 if math.isnan(x) else x for x in counts]


    # print(isos)
    # print(counts)

    # glottolog_d = {iso:string2glottocode(iso) for iso in isos}
    # with open('isoglotto3.json', 'w') as jsonout:
    #     jsonout.write(json.dumps(glottolog_d))
    with open('isoglotto3.json') as jsonin:
        glottolog_d = json.load(jsonin)
    glottocodes = [glottolog_d.get(iso) for iso in isos]
    # print(glottocodes)

    #compute the logarithms of the counts. Since 0 has no logarithm, we add a small number, making the result for 0 slightly smaller then 0, and then round up again to 0. The same is done for the other results, but will not lead to distortions since the offset will have to influence on the arity of the count
    logcounts = [math.ceil(x) for x in np.log10([x+0.11 for x in counts])]

    # logcounts = np.log10([x+0.1 for x in counts])
    # print(logcounts)

    m = lingtypology.LingMap(glottocodes, glottocode=True)
    # m.add_features(counts, radius=2, numeric=True)
    m.add_features(logcounts, radius=1, numeric=True)
    m.colormap_colors = ('red', 'blue')
    m.tiles = "openstreetmap"
    m.create_map()
    fname = f"gradient_map_{mime}.png"
    print(f"saving to {fname}")
    m.save_static(fname=fname)



def gradient_map():
    sql=f"""SELECT phyla.languagecode, count(id) AS count
            FROM  phyla
            LEFT JOIN languagesfiles
            ON phyla.languagecode=languagesfiles.languagecode
            WHERE LENGTH(phyla.languagecode)=3
            AND phyla.languagecode != 'eng'
            AND phyla.languagecode != 'spa'
            AND phyla.languagecode != 'rus'
            AND phyla.languagecode != 'por'
            AND phyla.languagecode != 'ind'
            AND phyla.languagecode != 'swh'
            AND phyla.languagecode != 'tpi'
            AND phyla.languagecode != 'fra'
            GROUP BY phyla.languagecode;"""
    df = get_df(sql)
    # isos=['eng','fra']
    # print(isos)
    # with open('isoglotto2.json') as jsonin:
    #     glottolog_d = json.load(jsonin)
    # bare_glottocodes = [glottolog_d.get(iso) for iso in isos]

    isos = df["languagecode"].tolist()
    counts = df["count"].tolist()

    # print(isos)
    # print(counts)

    # glottolog_d = {iso:string2glottocode(iso) for iso in isos}
    # with open('isoglotto3.json', 'w') as jsonout:
    #     jsonout.write(json.dumps(glottolog_d))
    with open('isoglotto3.json') as jsonin:
        glottolog_d = json.load(jsonin)
    glottocodes = [glottolog_d.get(iso) for iso in isos]
    # print(glottocodes)

    #compute the logarithms of the counts. Since 0 has no logarithm, we add a small number, making the result for 0 slightly smaller then 0, and then round up again to 0. The same is done for the other results, but will not lead to distortions since the offset will have to influence on the arity of the count
    logcounts = [math.ceil(x) for x in np.log10([x+0.11 for x in counts])]

    # logcounts = np.log10([x+0.1 for x in counts])
    # print(logcounts)

    m = lingtypology.LingMap(glottocodes, glottocode=True)
    # m.add_features(counts, radius=2, numeric=True)
    m.add_features(logcounts, radius=1, numeric=True)
    m.colormap_colors = ('red', 'blue')
    m.tiles = "openstreetmap"
    m.create_map()
    fname = f"gradient_map.png"
    print(f"saving to {fname}")
    m.save_static(fname=fname)


def plot_existing_records():
    sql="""select languagecode from (SELECT phyla.languagecode,count(id) as count  FROM  phyla
            LEFT JOIN languagesfiles ON phyla.languagecode=languagesfiles.languagecode group by phyla.languagecode) where count>0;"""
    df = get_df(sql)
    codes = df[df["languagecode"].str.len().isin([3])]["languagecode"].tolist()
    # print(codes)
    m = lingtypology.LingMap(codes)
    m.tiles = "openstreetmap"
    m.create_map()
    fname = f"existing_records.png"
    print(f"saving to {fname}")
    m.save_static(fname=fname)

print('collections')
print(get_df("""select archive, count(distinct(collection)) from files group by archive;"""))
print('bundles')
print(get_df("""select archive, count(distinct(collection)) from files group by archive;"""))
print('files')
for t in ('audio', 'video', 'xml'):
    print(f"{t} count")
    print(get_df(f"select archive, count(distinct(id))  from files where megatype='{t}' group by archive;"))
    print(f"{t} seconds")
    print(get_df(f"select archive, sum(seconds)  from files where megatype='{t}' group by archive;"))
    print(f"{t} bytes")
    print(get_df(f"select archive, sum(bytes)  from files where megatype='{t}' group by archive;"))

print('total bytes')
print(get_df("select archive, count(bytes)  from files group by archive;"))

print('languages')
print(get_df('select archive, count(distinct languagecode) from languagesfiles group by archive;'))

print('phyla')
print(get_df('select archive, count(distinct phylum) from languagesfiles,phyla where languagesfiles.languagecode=phyla.languagecode group by archive;'))

# ====================== OK =====================================
mime_gradient_map('audio')
mime_gradient_map('video')
mime_gradient_map('xml')
gradient_map()
plot_totalfiles()
plot_totalfiles(log=True)
for archive in "AILLA ELAR PARADISEC TLA".split():
    for dimension in "count sum".split():
        archive_plot(archive, dimension)



plot_languages()
plot_phyla()

for mime in "audio video xml".split():
    for dimension in "count second byte".split():
        stacked_plot(mime, dimension)


for mime in "audio video xml".split():
    for dimension in "count bytes seconds".split():
        for boolean in (True, False):
            rankplot("language", mime, dimension, f"""SELECT
                        languagecode as code,
                        {mime}{dimension}
                    FROM cleanlanguagecsv
                    {EXCLUDELANGUAGES}
                """,log=boolean)


for mime in "audio video xml".split():
    for dimension in "count bytes seconds".split():
        for boolean in (True, False):
            rankplot("phylum",mime, dimension, f"""SELECT
                        phylum as code,
                        {mime}{dimension}
                    FROM cleanphylumcsv
                """,log=boolean)
