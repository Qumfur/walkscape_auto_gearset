from utils import parse_csv_to_items, parse_csv_to_activities
from models import Item, Activity
from math import ceil, floor





items_file_name = "items.csv"
activity_file_name = "activities.csv"


items = parse_csv_to_items(items_file_name)
print(len(items), "items loaded")

activities = parse_csv_to_activities(activity_file_name)
for a in activities:
    max_eff = round((a.base_steps / a.min_steps - 1) * 100)
    print(a.activity, max_eff, "%")
    
print(len(activities), "activities loaded")