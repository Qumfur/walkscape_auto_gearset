import gzip
import base64
import json
from models import GearSet

def export_gearset(gearset: GearSet) -> str:
    """
    Exports a GearSet to a Gzipped, Base64-encoded JSON string compatible 
    with the Walkscape spreadsheet import format.
    """
    
    # Define the output order strictly matching the JS "outputOrder" and "indices"
    # Format: (TypeName, Index, GetterFunction)
    slots_map = [
        ("head", 0, lambda g: g.head),
        ("cape", 0, lambda g: g.cape),
        ("back", 0, lambda g: g.back),
        ("chest", 0, lambda g: g.chest),
        ("primary", 0, lambda g: g.primary),
        ("secondary", 0, lambda g: g.secondary),
        ("hands", 0, lambda g: g.hands),
        ("legs", 0, lambda g: g.legs),
        ("neck", 0, lambda g: g.neck),
        ("feet", 0, lambda g: g.feet),
        # Rings (Indices 0, 1)
        ("ring", 0, lambda g: g.rings[0] if len(g.rings) > 0 else None),
        ("ring", 1, lambda g: g.rings[1] if len(g.rings) > 1 else None),
        # Tools (Indices 0-5)
        ("tool", 0, lambda g: g.tools[0] if len(g.tools) > 0 else None),
        ("tool", 1, lambda g: g.tools[1] if len(g.tools) > 1 else None),
        ("tool", 2, lambda g: g.tools[2] if len(g.tools) > 2 else None),
        ("tool", 3, lambda g: g.tools[3] if len(g.tools) > 3 else None),
        ("tool", 4, lambda g: g.tools[4] if len(g.tools) > 4 else None),
        ("tool", 5, lambda g: g.tools[5] if len(g.tools) > 5 else None),
    ]

    json_entries = []

    for type_name, idx, getter in slots_map:
        item = getter(gearset)
        
        # Determine the content of the "item" key
        if item and item.uuid:
            # Construct the inner JSON string for the item data
            inner_data = {
                "id": item.uuid,
                # Default to "Normal" if quality is missing (required field)
                "quality": "Normal", # item.quality_rarity or "Normal", 
                "tag": None
            }
            # Serialize inner object to string (e.g., '{"id":"...","quality":"..."}')
            item_value_str = json.dumps(inner_data, separators=(',', ':'))
        else:
            # Matches JS behavior: fill("\"null\"")
            item_value_str = "null"

        entry = {
            "type": type_name,
            "index": idx,
            "item": item_value_str, # This is a stringified JSON or "null" string
            "errors": []
        }
        json_entries.append(entry)

    # Wrap in root object
    final_obj = {"items": json_entries}
    
    # Serialize to standard JSON
    json_str = json.dumps(final_obj, separators=(',', ':'))
    
    # Compress (Gzip)
    compressed_data = gzip.compress(json_str.encode('utf-8'))
    
    # Encode (Base64)
    return base64.b64encode(compressed_data).decode('utf-8')