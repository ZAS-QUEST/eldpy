import csv
import sys
import json
import pprint
import requests
from constants import NER_BLACKLIST

URL = "http://localhost:8090/service/disambiguate"


def get_ner(text):
    if len(text.split()) < 5:  # cannot do NER on less than 5 words
        return []
    # send text
    rtext = requests.post(URL, json={"text": text}, timeout=1200).text
    # parse json
    if rtext is None:
        return {}
    retrieved_entities = json.loads(rtext).get("entities", [])
    # print(retrieved_entities)
    # extract names and wikidataId's
    result =  {
        x["wikidataId"]: (x["rawName"], x["confidence_score"])
        for x in retrieved_entities
        if x.get("wikidataId")
        and x["wikidataId"] not in NER_BLACKLIST
        and x["confidence_score"] > 0.4
    }
    pprint.pprint(result)
    return(result)


if __name__ == "__main__":
    filename = sys.argv[1]
    translations = []
    with open(filename, mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            translation = row["Translated_Text"]
            translations.append(translation)
    get_ner(".".join(translations))
