# LangSci

This package provides tools for interfacing with endangered language archives.

For the time being, only the download functionality is robust enough for general use.

The package contains script for the analysis of ELAN files. These analyses are quantitative (duration, tiers, tokens) as well as qualitative (vernacular language, tranlations, glosses, semantic domains).

The analyses are cached in JSON format and can be exported to RDF.

Sample usage:
- download all ELAN files from the AILLA archives:
```
from eldpy import download
download.bulk_download(archive='AILLA', filetype=1, username='janedoe', password='mypassword')
```
- analyze all downloaded ELAN files
```
from eldpy.bulk import *
bulk_populate(cache=False)
```
- cache for future usage: as above and add
```
bulk_populate(cache=False)
```
- read cached information
```
from eldpy.bulk import *
bulk_populate(cache=True)
```
- compute tokens and durations
```
from eldpy.bulk import *
bulk_populate()
bulk_statistics()
```
- analyze ELAN tier hierarchies
```
from eldpy.bulk import *
bulk_populate()
bulk_fingerprints()
```
-export as rdf
```
from eldpy.bulk import *
bulk_populate()
bulk_rdf()
```
