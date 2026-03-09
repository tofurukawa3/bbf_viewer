import os
import json
import time
import sys

# Add backend to path to import parser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
import parser

start_time = time.time()
models = parser.get_available_models()

root_node = {
    "name": "BBF Data Models",
    "node_type": "object",
    "access": "readOnly",
    "description": "Unified view of all available BBF YANG Models",
    "children": []
}

for m in models:
    try:
        data = parser.parse_yang_to_dict(m)
        root_node["children"].append(data)
    except Exception as e:
        print(f"Error parsing {m}: {e}")

end_time = time.time()

json_out = json.dumps(root_node)
print(f"Parsed {len(models)} models in {end_time - start_time:.2f} seconds.")
print(f"Total unified tree JSON size: {len(json_out) / 1024 / 1024:.2f} MB")
