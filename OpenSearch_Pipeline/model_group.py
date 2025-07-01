import requests
import json

# OpenSearch config
OPENSEARCH_HOST = "http://localhost:9200"
url = f"{OPENSEARCH_HOST}/_plugins/_ml/model_groups/_register"
auth = ("admin", "admin")  # Replace with your credentials if needed

# Request headers and payload
headers = {"Content-Type": "application/json"}
payload = {
    "name": "local_model_group",
    "description": "A model group for local models"
}

# Make the POST request
response = requests.post(url, headers=headers, data=json.dumps(payload), auth=auth)

# Output the result
print("Status Code:", response.status_code)
print("Response:", response.text)
