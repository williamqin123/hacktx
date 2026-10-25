import os
import serpapi
import json
from dotenv import load_dotenv

#https://serpapi.com/google-maps-api

def normalize_address(address):
    return (
        address.lower()
        .replace(",", "")
        .replace(".", "")
        .replace(" rd", " road")
        .replace(" st", " street")
        .replace(" ave", " avenue")
        .replace(" hwy", " highway")
        .strip()
    )

store_ids = []

COORDINATES = """@30.291171,-97.735766,14z"""

with open("walmart-stores.json", "r", encoding="utf-8") as f:
    stores = json.load(f)

load_dotenv()

client = serpapi.Client(api_key= os.getenv("SERPAPI_KEY"))

results = client.search({
  "engine": "google_maps",
  "q": "Walmart near me",
  "ll": COORDINATES,
   "nearby": "true"
})

addresses = [
    store["address"]
    for store in results["local_results"]
]

first_5 = addresses[:1]

print(first_5)

for address in first_5:
    normalized_address = normalize_address(address)

    match = None

    for store in stores:
        store_address = normalize_address(store["address"])

        if store_address in normalized_address or normalized_address in store_address:
            match = store["store_id"]
            break

    store_ids.append(match)

print(store_ids)
