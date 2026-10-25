import os
import serpapi
from dotenv import load_dotenv
from Walmart_Location import store_ids

load_dotenv()

client = serpapi.Client(api_key= os.getenv("SERPAPI_KEY"))

ITEM_SEARCH = """bread"""

results = client.search({
  "engine": "walmart",
  "query": ITEM_SEARCH,
  "store_id": store_ids
})

print(results)