import urllib.request
import json
import traceback

try:
    req2 = urllib.request.Request("http://127.0.0.1:8000/models/bbf-device.yang")
    with urllib.request.urlopen(req2) as response:
        device_data = json.loads(response.read().decode())
        
    def print_resolved(node, path=''):
        d_type = node.get('detailed_type', '')
        if len(d_type) > 0 and 'enum' not in node['name']:
            print(f"{path}{node['name']}: {node.get('data_type')} ({d_type})")
        for child in node.get('children', []):
            print_resolved(child, path + node['name'] + '.')
            
    print_resolved(device_data)
except Exception as e:
    traceback.print_exc()
