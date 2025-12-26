import csv
from models import Item

def parse_csv_to_items(file_path: str) -> list[Item]:
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        items = []
        for row in reader:
            data = {k: v for k, v in row.items() if v != ''}
            if data["Item"] == "None":
                continue
            item = Item.from_csv_row(data)
            items.append(item)
        return items