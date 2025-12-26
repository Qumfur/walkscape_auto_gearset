from utils import parse_csv_to_items
from models import Item



file_name = "items.csv"

items = parse_csv_to_items(file_name)
for item in items:
    print(item.name, item.rarity_sort)

for key in Item.model_fields.keys():
    if all(getattr(item, key) is None for item in items):
        print(key)

print(len(items))