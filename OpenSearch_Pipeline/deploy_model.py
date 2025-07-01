import requests
import json

# OpenSearch settings
OPENSEARCH_HOST = "http://localhost:9200"
MODEL_ID = "u6KQw5cBa5E3d2biRIhN"
auth = ("admin", "admin")  # Replace with your credentials

url = f"{OPENSEARCH_HOST}/_plugins/_ml/models/{MODEL_ID}/_deploy"

# Headers
headers = {
    "Content-Type": "application/json"
}

# POST request to deploy the model
response = requests.post(url, headers=headers)

# Output the result
print("Status Code:", response.status_code)
print("Response:", response.text)


TASK_ID = response.json()["task_id"]
# Construct the URL
url = f"{OPENSEARCH_HOST}/_plugins/_ml/tasks/{TASK_ID}"
headers = {"Content-Type": "application/json"}

# Send GET request
response = requests.get(url, headers=headers)

# Print response
print("Status Code:", response.status_code)
print("Response:", response.text)
