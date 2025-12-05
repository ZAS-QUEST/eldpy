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

def rankplot(level, mime, dimension, sql, log=False, aggregatefunction=totalcount):
    connection = sqlite3.connect('delaman2025a.db')
    df = pd.read_sql_query(sql, connection)

    connection.close()

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


# items per archive
# size per archive
# languages per archive

# audiosize per archive
# videosize per archive
# xmlsize per archive



# languages lacking any representation in the archive

# rankplot("file_count_per_language","""SELECT
#             languagecode as code,
#             videocount,
#             audiocount,
#             xmlcount
#         FROM cleanlanguagecsv
#     """)
#
# rankplot("file_count_per_language","""SELECT
#             languagecode as code,
#             videocount,
#             audiocount,
#             xmlcount
#         FROM cleanlanguagecsv
#     """, log=True)


for mime in "audio video xml".split():
    for dimension in "count bytes seconds".split():
        for boolean in (True, False):
            rankplot("language", mime, dimension, f"""SELECT
                        languagecode as code,
                        {mime}{dimension}
                    FROM cleanlanguagecsv
                """,log=boolean)


for mime in "audio video xml".split():
    for dimension in "count bytes seconds".split():
        for boolean in (True, False):
            rankplot("phylum",mime, dimension, f"""SELECT
                        phylum as code,
                        {mime}{dimension}
                    FROM cleanphylumcsv
                """,log=boolean)


#
#
# rankplot("file_count_per_phylum","""SELECT
#             phylum as code,
#             videocount,
#             audiocount,
#             xmlcount
#         FROM cleanphylumcsv
#     """)
#
# rankplot("file_count_per_phylum","""SELECT
#             phylum as code,
#             videocount,
#             audiocount,
#             xmlcount
#         FROM cleanphylumcsv
#     """, log=True)
