import csv
import sys
import requests
import json
import pprint
from constants import NER_BLACKLIST

url = "http://localhost:8090/service/disambiguate"

def get_ner(text):
    if len(text.split()) < 5:  # cannot do NER on less than 5 words
        return []
    # send text
    rtext = requests.post(url, json={"text": text}).text
    # parse json
    if rtext == None:
        return {}
    retrieved_entities = json.loads(rtext).get("entities", [])
    # print(retrieved_entities)
    # extract names and wikidataId's
    return {x["wikidataId"]: (x["rawName"],x["confidence_score"])
            for x in retrieved_entities
            if x.get("wikidataId") and x["wikidataId"] not in NER_BLACKLIST and x["confidence_score"] > .4
            }

if __name__ == "__main__":
    filename = sys.argv[1]
    translations = []
    with open(filename, mode='r', encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            translation = row["Translated_Text"]
            translations.append(translation)
    pprint.pprint(get_ner(".".join(translations)))


