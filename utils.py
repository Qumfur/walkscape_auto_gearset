import csv
from models import Item, Activity


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
    
def parse_csv_to_activities(file_path: str) -> list[Activity]:
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        activities = []
        for row in reader:
            data = {k: v for k, v in row.items() if v != ''}
            if data["Activity"] == "None":
                continue
            activity = Activity.from_csv_row(data)
            activities.append(activity)
        return activities
    

import math

def calculate_steps(
   activity:Activity,
   player_skill_level: int,
   player_work_efficiency: float,
   player_minus_steps: int,
   player_minus_steps_percent: float,

) -> int:
    level_diff = max(0, player_skill_level - activity.skill_level)
    level_eff = min(0.25, level_diff * 0.0125)

    total_added_eff = level_eff + player_work_efficiency

    effective_eff = min(total_added_eff, activity.max_work_efficiency)

    efficiency_multiplier = 1.0 + effective_eff
    
    step_multiplier = 1.0 - player_minus_steps_percent

    
    steps = math.ceil( (activity.base_steps / efficiency_multiplier) * step_multiplier ) - player_minus_steps

    return max(10, steps)