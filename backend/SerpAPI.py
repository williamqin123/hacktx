import os
import serpapi

client = serpapi.Client(api_key=os.getenv("SERPAPI_KEY"))
results = client.search({
  "engine": "google",
  "q": "coffee"
})

print(results)