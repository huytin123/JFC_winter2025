import requests
import json

# Register Model
url = "http://localhost:9200/_plugins/_ml/models/_register"
headers = {"Content-Type": "application/json"}

payload = {
  "name": "huggingface/sentence-transformers/all-MiniLM-L6-v2",
  "version": "1.0.2",
  "model_group_id": "q6J5w5cBa5E3d2biZYiO",
  "model_format": "TORCH_SCRIPT"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(response.status_code, response.text)

# Config
OPENSEARCH_HOST = "http://localhost:9200"
TASK_ID = response.json()["task_id"]
auth = ("admin", "admin")  # Replace with your OpenSearch credentials if needed

# Build URL
url = f"{OPENSEARCH_HOST}/_plugins/_ml/tasks/{TASK_ID}"
headers = {"Content-Type": "application/json"}

# Make the GET request
response = requests.get(url, headers=headers, auth=auth)

# Output result
print("Status Code:", response.status_code)
print("Response:", response.text)
