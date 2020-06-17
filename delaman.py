from .archive import Archive

archives = {
    "ANLA": Archive(
        "ANLA",
        "https://www.uaf.edu/anla/collections/",
        collectionprefix="https://uafanlc.alaska.edu/Online",
        landingpage_template = "https://www.uaf.edu/anla/collections/search/resultDetail.xml?resource=%s"
    ),
    "PARADISEC": Archive(
        "PARADISEC",
        "https://catalog.paradisec.org.au/",
        collectionprefix="http://catalog.paradisec.org.au/repository",
        collection_url_template="http://catalog.paradisec.org.au/repository/%s/%s/%s",
        landingpage_template = "https://catalog.paradisec.org.au/collections/%s"
    ),
    "ELAR": Archive(
        "ELAR",
        "elar.soas.ac.uk",
        collectionprefix="https://elar.soas.ac.uk/Collection/",
        collection_url_template="https://elar.soas.ac.uk/Collection/%s",
        landingpage_template = "https://elar.soas.ac.uk/Collection/%s"
    ),
    "TLA": Archive(
        "TLA",
        "https://archive.mpi.nl",
        collectionprefix="https://archive.mpi.nl/islandora/object/",
        collection_url_template="https://archive.mpi.nl/islandora/object/%s",
        landingpage_template = "https://archive.mpi.nl/islandora/object/%s"
    ),
    "AILLA": Archive(
        "AILLA",
        "https://ailla.utexas.org",
        collectionprefix="https://ailla.utexas.org/islandora/object/",
        collection_url_template="https://ailla.utexas.org/islandora/object/%s",
        landingpage_template = "https://ailla.utexas.org/islandora/object/%s"
    ),
}
