from app.parser import parse_xml_to_dict

print("Testing parser on tr-181-2-18-0-cwmp.xml...")
try:
    data = parse_xml_to_dict("tr-181-2-18-0-cwmp.xml")
    
    # Let's find some parameters to print their detailed_type constraints
    def find_params_with_constraints(node, results):
        if node.get("node_type") == "parameter" and node.get("detailed_type"):
            results.append(node)
        
        children = node.get("children", [])
        if children:
            for child in children:
                find_params_with_constraints(child, results)
                
    results = []
    find_params_with_constraints(data, results)
    
    print(f"Found {len(results)} parameters with detailed_type constraints.")
    if len(results) > 0:
        print("\nSample constraints:")
        for r in results[:10]:
            print(f" - {r['name']}: {r['data_type']} -> {r['detailed_type']}")
            
except Exception as e:
    import traceback
    traceback.print_exc()
    print("Error:", e)
