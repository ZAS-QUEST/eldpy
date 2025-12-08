import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
                where languagecode != 'eng'
                and languagecode != 'spa'
                and languagecode != 'rus'
                and languagecode != 'por'
                and languagecode != 'ind'
                and languagecode != 'tpi'
                and languagecode != 'fra'
                and languagecode != 'swh'
                and languagecode != '_Chinese, Mandarin'
                and languagecode != '_Chinese'
                GROUP BY languagecode;
                """
    df = get_df(sql)


    df = df.sort_values("total", ascending=False)
    print(df)
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
    plt.title(f"Total files per language across the four archives")
    plt.show()

    plt.savefig(f"files_per_languages_{log_addendum}.png", dpi=300, bbox_inches="tight")

    # plt.tight_layout()
    plt.close()




def plot_languages():
    sql = f"""SELECT archive, COUNT(DISTINCT(languagecode)) as count
                FROM languagesfiles
                GROUP BY archive;
                """
    df = get_df(sql)

    print(df)

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

    print(df)

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

    print(df)

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

    print(df)

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

    plt.ylabel("total (log scale)")
    plt.title(f"Total {mime}{dimension} per  {level} across the four archives")


    plt.savefig(f"{mime}{dimension}_per_{level}{log_addendum}.png", dpi=300, bbox_inches="tight")

    # plt.tight_layout()
    plt.close()





# ====================== OK =====================================
# plot_totalfiles()
# plot_totalfiles(log=True)
# for archive in "AILLA ELAR PARADISEC TLA".split():
#     for dimension in "count sum".split():
#         archive_plot(archive, dimension)
#
#
#
# plot_languages()
# plot_phyla()
#
# for mime in "audio video xml".split():
#     for dimension in "count second byte".split():
#         stacked_plot(mime, dimension)
#
#
# for mime in "audio video xml".split():
#     for dimension in "count bytes seconds".split():
#         for boolean in (True, False):
#             rankplot("language", mime, dimension, f"""SELECT
#                         languagecode as code,
#                         {mime}{dimension}
#                     FROM cleanlanguagecsv
#                 """,log=boolean)
#
#
# for mime in "audio video xml".split():
#     for dimension in "count bytes seconds".split():
#         for boolean in (True, False):
#             rankplot("phylum",mime, dimension, f"""SELECT
#                         phylum as code,
#                         {mime}{dimension}
#                     FROM cleanphylumcsv
#                 """,log=boolean)
