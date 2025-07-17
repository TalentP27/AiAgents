import requests

query = "what is LLM?"
url = "https://api.semanticscholar.org/graph/v1/paper/search"
params = {"query": query}
headers = {"x-api-key": "1234567890"}
response = requests.get(url, params=params, headers=headers)
print(response.json())