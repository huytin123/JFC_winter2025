import requests
import json

# Replace with your OpenSearch endpoint
OPENSEARCH_HOST = "http://localhost:9200"

url = f"{OPENSEARCH_HOST}/_cluster/settings"
headers = {"Content-Type": "application/json"}

payload = {
    "persistent": {
        "plugins.ml_commons.only_run_on_ml_node": "false",
        "plugins.ml_commons.model_access_control_enabled": "true",
        "plugins.ml_commons.native_memory_threshold": "99"
    }
}

response = requests.put(url, headers=headers, data=json.dumps(payload))

print("Status Code:", response.status_code)
print("Response:", response.text)
