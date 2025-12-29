# Walkscape Gear Optimizer

Calculates best gearset using an activity and a target optimization

## Quick Start

1. **Install Req:** `pip install -r requirements.txt`
2. **Config:** Edit `main.py, check the OPTIMATION_TARGET enum for available targets, for availble activity_name check the acitivities.csv and recipes.csv`
3. ```python
   activity_name = "Create a Gold Ethernite Ring"
   optimize_target = OPTIMAZATION_TARGET.quality
   ```
4. paste your game data json (from the app settings) to user.json file, if you leave it as an empty json it will use all available items
5. **Run:**`python main.py`


## Output

The script prints the best loadout, calculated stats, and an **export string** for other tools

## Notes

* the tool uses Arky's sheet info so it doesnt have the latest activities/recipes and items that were added in the last update
* the tool currently does not take into account collectibles, requirements (e.g need diving set under water), set effects (e.g adventuring set) and service bonuses/ debuffs

## Roadmap

* [X] basic gearset optimization for activities
* [X] add recipes support
* [X] use WalkScape user export support
* [ ] take into account activity requirements and bonuses outside of gearset and over level
* [ ] get data of activity drops/ recipes needed materials (missing from arky's sheet), something like a dump or API acces
* [ ] calculate expected steps per activity drop
* [ ] chain activities/ recipes to calculate final result per step. e.g farganite pickaxe, optimize the gearsets needed including gathering and processing and calculate the total expected steps
* [ ] optimize performance
