import itertools
import copy
from typing import Dict, List
from models import Item, Activity, GearSet
from utils import calculate_steps, calculate_quality_probabilities
from enum import Enum


RESTRICTED_TOOL_KEYWORDS = {"pickaxe", "hatchet", "fishingTool", "lure","hammer", "splitter"} # need to add more
OPTIMAZATION_TARGET = Enum("OPTIMAZATION_TARGET", ["reward_rolls", "xp", "chests", "materials", "fine", "collectibles", "quality"])

class GearOptimizer:
    activity: Activity
    player_level: int
    player_skill_level: int
    tool_slots: int
    optimazation_target: OPTIMAZATION_TARGET
    locked_slots: set[str]
    locked_tools: list[Item]
    locked_rings: list[Item]
    
    def __init__(self, all_items: List[Item]):
        self.all_items = all_items
        self.player_level = 0
        self.player_skill_level = 0
        self.tool_slots = 3
        self.optimazation_target = OPTIMAZATION_TARGET.reward_rolls
        self.locked_slots = set()
        self.locked_tools = []
        self.locked_rings = []

    def optimize(self, activity: Activity, player_level: int, player_skill_level: int, optimazation_target: OPTIMAZATION_TARGET = OPTIMAZATION_TARGET.reward_rolls):
        self.activity = activity
        self.player_level = player_level
        self.player_skill_level = player_skill_level
        self.optimazation_target = optimazation_target
        if player_level >= 80: self.tool_slots = 6
        elif player_level >= 50: self.tool_slots = 5
        elif player_level >= 20: self.tool_slots = 4
        else: self.tool_slots = 3

        candidates = self._get_candidates(activity)

        candidates = self._keep_best_versions(candidates, activity, self.calculate_score_for_set)

        best_set = GearSet()
        base_score = self.calculate_score_for_set(best_set)


        single_slots = ["head", "chest", "legs", "feet", "cape", "back", "neck", "hands", "primary", "secondary", "pet", "consumable"]
        
        #sets
        set_names = self.get_all_sets()
        set_data = self.preprocessing_sets(set_names, candidates)
        scored_sets = self.score_sets_on_empty_gear_set(set_names, set_data)
        scored_sets.sort(key=lambda x: x[0], reverse=True)
        top_sets = [x[1] for x in scored_sets[:5]]
        
        changed = True
        changed_iter = 0
        while changed:
            changed = False
            changed_iter += 1
            if changed_iter > 100: # Exit condition in case of flip-flopping gear
                print("Optimization loop exited after 100 loops. Potentially not optimal solution")
                break
            pre_iter_score = base_score
            
            for slot_attr in single_slots:
                if slot_attr in self.locked_slots:
                    continue
                best_item = getattr(best_set, slot_attr)
                max_slot_score = base_score 
                slot_key = slot_attr.capitalize()
                if slot_attr == "primary": slot_key = "Primary" 
                
                for item in candidates.get(slot_key, []):
                    setattr(best_set, slot_attr, item)
                    if item.set_name != None and not self._check_for_set_conditions(item, best_set):
                        continue
                    score = self.calculate_score_for_set(best_set)
                    
                    if score > max_slot_score:
                        max_slot_score = score
                        best_item = item
                    setattr(best_set, slot_attr, None) # Unequip
                
                setattr(best_set, slot_attr, best_item)
                base_score = max_slot_score

            ring_items = candidates.get("Ring", [])
            if ring_items:
                best_rings = best_set.rings
                max_r_score = base_score
                open_slots = 2 - len(self.locked_rings)
                if open_slots == 0: best_rings = self.locked_rings
                for subset_rings in itertools.combinations_with_replacement(ring_items, open_slots):
                    best_set.rings = list(subset_rings) + self.locked_rings
                    score = self.calculate_score_for_set(best_set)
                    if score > max_r_score:
                        max_r_score = score
                        best_rings = list(subset_rings) + self.locked_rings
                best_set.rings = best_rings
                base_score = max_r_score

            tool_items = candidates.get("Tool", [])
            if tool_items:
                best_tools = best_set.tools
                max_t_score = base_score
                
                scored_tools = []
                for t in tool_items:
                    best_set.tools = [t]
                    scored_tools.append( (self.calculate_score_for_set(best_set), t) )
                scored_tools.sort(key=lambda x: x[0], reverse=True)
                top_tools = [x[1] for x in scored_tools[:30]]

                best_set.tools = []
                for r in range(1, self.tool_slots - len(self.locked_tools) + 1):
                    for subset in itertools.combinations(top_tools, r):
                        used_tools = list(subset) + self.locked_tools
                        if self._is_valid_tool_set(used_tools):
                            best_set.tools = list(used_tools)
                            score = self.calculate_score_for_set(best_set)
                            if score > max_t_score:
                                max_t_score = score
                                best_tools = list(subset)
                best_set.tools = best_tools
                self._is_valid_tool_set(best_tools)
            
            #Set consideration
            set_with_most_improvement = []
            improved = False
            saved_set = copy.deepcopy(best_set)
            max_score = self.calculate_score_for_set(best_set)
            
            for considered_set_items in top_sets:
                score = self.process_set(copy.deepcopy(saved_set), considered_set_items)
                if score > max_score:
                    max_score = score
                    improved = True
                    set_with_most_improvement = considered_set_items
            
            
            if improved:
                #Apply set to best set
                rings = []
                tools = []
                for item in set_with_most_improvement:
                    slot_attr = item.slot
                    if slot_attr == "Ring":
                        rings.append(item)
                    elif slot_attr == "Tool":
                        tools.append(item)
                    else:
                        setattr(best_set, slot_attr.lower(), item)
                best_set.rings = rings
                best_set.tools = tools
                #Lock slots of the best set to ensure that set items are not replaced
                for item in set_with_most_improvement:
                    slot_attr = item.slot
                    if slot_attr == "Ring":
                        if slot_attr + "1" not in self.locked_slots:
                            self.locked_slots.add(slot_attr + "1")
                        elif slot_attr + "2" not in self.locked_slots:
                            self.locked_slots.add(slot_attr + "1")
                        self.locked_rings.append(item)
                        continue
                    if slot_attr == "Tool":
                        i = 1
                        while True:
                            if slot_attr + str(i) not in self.locked_slots:
                                self.locked_slots.add(slot_attr + str(i))
                                break
                            i += 1
                        self.locked_tools.append(item)
                        continue
                    if slot_attr.lower() not in self.locked_slots:
                        self.locked_slots.add(slot_attr.lower())
                
                    
            
            #Iterative consideration
            base_score = self.calculate_score_for_set(best_set)
            if pre_iter_score < base_score:
                changed = True
                print(f"Optimization loop {changed_iter} yielded improvement")
            pass
        
        return best_set

    def _get_candidates(self, activity: Activity) -> Dict[str, List[Item]]:
        slots = {}
        for item in self.all_items:
            item_skills = item.skill.split(',') if item.skill else []

            if item.skill is not None and activity.skill not in item_skills and not item.is_part_of_set: continue
            if item.region and item.region != activity.region: continue
            if item.underwater_only and not activity.is_underwater: continue
            
            if item.slot not in slots: slots[item.slot] = []
            slots[item.slot].append(item)
        return slots

    def _keep_best_versions(self, candidates: Dict, activity: Activity, score_func) -> Dict:
        """
        Groups items by 'clean_item_name' and picks the one with highest score.
        Uses the exact same score_func as the main optimizer to guarantee alignment.
        """
        cleaned_candidates = {}
        temp_set = GearSet()
        
        for slot, items in candidates.items():
            best_versions = {}
            for item in items:
                key = item.clean_item_name or item.name
                
                if item.set_name != None:
                    key += str(item.set_count) #Keeps all set items
                
                if slot == "Tool": temp_set.tools = [item]
                elif slot == "Ring": temp_set.rings = [item]
                else: setattr(temp_set, slot.lower(), item)
                
                score = score_func(temp_set)
                
                if slot == "Tool": temp_set.tools = []
                elif slot == "Ring": temp_set.rings = []
                else: setattr(temp_set, slot.lower(), None)

                if key not in best_versions or score > best_versions[key][0]:
                    best_versions[key] = (score, item)
            
            cleaned_candidates[slot] = [v[1] for v in best_versions.values()]
        return cleaned_candidates
    
    def calculate_score_for_set(self, current_set: GearSet) -> float:
        stats = current_set.get_stats(self.activity.skill)
        steps = calculate_steps(
            activity=self.activity,
            player_skill_level=self.player_skill_level, 
            player_work_efficiency=stats["work_efficiency"],
            player_minus_steps=stats["flat_step_reduction"],
            player_minus_steps_percent=stats["percent_step_reduction"]
        )
        da_mult = 1.0 + stats["double_action"]
        dr_mult = 1.0 + stats["double_rewards"]
        nmc_mult = 1.0 / (1.0 - min(0.99, stats["no_mats"]))
        
        
        if self.optimazation_target == OPTIMAZATION_TARGET.reward_rolls:
            return (da_mult * dr_mult) / steps
        elif self.optimazation_target == OPTIMAZATION_TARGET.xp:
            base_xp = self.activity.base_xp or 0
            xp_mult = 1.0 + stats["xp_percent"]
            flat_xp = stats["flat_xp"]
            return ((base_xp * xp_mult + flat_xp) * da_mult) / steps
        elif self.optimazation_target == OPTIMAZATION_TARGET.chests:
            return ((1.0 + stats["chest_finding"]) * da_mult * dr_mult) / steps
        elif self.optimazation_target == OPTIMAZATION_TARGET.materials:
            return  (dr_mult * nmc_mult)
        elif self.optimazation_target == OPTIMAZATION_TARGET.fine:
            return ((1.0 + stats["fine_material"]) * da_mult * dr_mult) / steps
        elif self.optimazation_target == OPTIMAZATION_TARGET.collectibles:
            return ((1.0 + stats["collectible_percent"]) * da_mult * dr_mult) / steps
        elif self.optimazation_target == OPTIMAZATION_TARGET.quality:
            flat_quality_bonus = stats["quality_outcome"]
            
            probs = calculate_quality_probabilities(
                activity_min_level=self.activity.skill_level or 0,
                player_skill_level=self.player_skill_level,
                quality_bonus=flat_quality_bonus
            )
            
            return probs.get("Eternal", 0.0) * dr_mult * nmc_mult
        else:
            return 0.0
    
    def _is_valid_tool_set(self, tools: List[Item]) -> bool:
        seen_keywords = set()
        for t in tools:
            for k in t.keywords:
                if k in RESTRICTED_TOOL_KEYWORDS:
                    if k in seen_keywords: return False
                    seen_keywords.add(k)
        names = [t.name for t in tools]
        if len(names) != len(set(names)): return False
        return True
    
    def _check_for_set_conditions(self, check_item: Item, current_set: GearSet) -> bool:
        set_count_goal = check_item.set_count
        set_count_current = 0
        for i in current_set.all_items:
            if i.set_name == check_item.set_name and i.is_part_of_set:
                set_count_current += 1
        return bool(set_count_current >= set_count_goal)
    
    def get_all_sets(self) -> set[str]:
        sets = set()
        for item in self.all_items:
            if item.set_name != None:
                if item.set_name not in sets:
                    sets.add(item.set_name)
        return sets
    
    def preprocessing_sets(self, set_names, candidates):
        set_data = {}
        for ind_set in set_names:
            ind_set_data = {}
            items_in_set = list()
            for slot,items in candidates.items():
                for item in items:
                    if item.set_name == ind_set:
                        items_in_set.append(item)
            
            #Take out items that are part of the set but without set attr
            items_without_set_attr = []
            for item in items_in_set[:]:
                if not item.has_set_attr:
                    items_in_set.remove(item)
                    items_without_set_attr.append(item)
            
            #Take out items without set attributes that don't give an advantage for the activity
            #Those might still be useful to achieve the necessary count of a set item
            items_without_set_attr_without_adv = []
            temp_set = GearSet()
            zero_score = self.calculate_score_for_set(temp_set)
            for item in items_without_set_attr[:]:
                temp_set = GearSet()
                slot_attr = item.slot
                if slot_attr == "Ring":
                    temp_set.rings = [item]
                elif slot_attr == "Tool":
                    temp_set.tools = [item]
                else:
                    setattr(temp_set, slot_attr.lower(), item)
                temp_score = self.calculate_score_for_set(temp_set)
                if abs(temp_score - zero_score) > 0.000001: continue
                items_without_set_attr_without_adv.append(item)
                items_without_set_attr.remove(item)
            
            #Seperate all items into set_counts
            grouped = {}
            for item in items_in_set:
                key = item.set_count
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(item)
                
            ind_set_data["items_without_set_attr"] = items_without_set_attr
            ind_set_data["items_without_set_attr_without_adv"] = items_without_set_attr_without_adv
            ind_set_data["grouped"] = grouped
            set_data[ind_set] = ind_set_data
        return set_data                        
                
    def process_tools(self, tools, current_set):
        original_tools = current_set.tools
        count_of_non_replaced_tools = len(original_tools) - len(tools) - len(self.locked_tools)
        current_max_score = float("-inf")
        if count_of_non_replaced_tools <= 0:
            current_set.tools = list(tools)
            current_max_score = self.calculate_score_for_set(current_set)
            current_set.tools = original_tools
        else:
            for subset_current_tools in itertools.combinations(original_tools, count_of_non_replaced_tools):
                tools_used = list(subset_current_tools) + tools + self.locked_tools
                if self._is_valid_tool_set(tools_used):
                    current_set.tools = list(tools_used)
                    score = self.calculate_score_for_set(current_set)
                    current_set.tools = original_tools
                    if score > current_max_score:
                        current_max_score = score
        return current_max_score
    
    def process_set(self, current_set, set_items: List[Item]) -> float:
        score = 0
        set_can_be_equipped = True
        rings = []
        tools = []
        for item in set_items:
            slot_attr = item.slot
            if slot_attr.lower() in self.locked_slots:
                set_can_be_equipped = False
                break
            if slot_attr == "Tool":
                tools.append(item)
            elif slot_attr == "Ring":
                rings.append(item)
            else:
                setattr(current_set, slot_attr.lower(), item)
        if not set_can_be_equipped: return float("-inf")
        if len(rings) > 2 - len(self.locked_rings): return float("-inf")
        if len(tools) > self.tool_slots - len(self.locked_tools): return float("-inf")
        score = self.process_tools(tools, current_set)

        
        return score
    
    def score_sets_on_empty_gear_set(self, set_names, set_data):
        scored_sets = []
        for ind_set in set_names:
            items_without_set_attr = set_data[ind_set]["items_without_set_attr"]
            items_without_set_attr_without_adv = set_data[ind_set]["items_without_set_attr_without_adv"]
            grouped = set_data[ind_set]["grouped"]

            #For each set count try out all possibilities and check if they have a better score
            for count,items in grouped.items():
                #Add items that don't have a set attribute but are part of the set
                items.extend(items_without_set_attr)
                #Remove items that have a set attribute but are not part of the set
                items_not_part_of_set= []
                for item in items[:]:
                    if not item.is_part_of_set:
                        items.remove(item)
                        items_not_part_of_set.append(item)
                #If the amount of set items is too low to achieve the count add items enough items that are part of the set but don't give any advantage
                if len(items) < count:
                    count_items_needed = count - len(items)
                    items.extend(items_without_set_attr_without_adv[:count_items_needed])
                if len(items) < count: continue
                #Checking the set without any items that are not part of the set
                for subset in itertools.combinations(items, count):
                    score =  self.process_set(GearSet(), list(subset))
                    scored_sets.append((score, list(subset)))
                #Adding every combination of set item that are not part of the set and calculate the score of each
                for i in range(1,len(items_not_part_of_set)+1):
                    for subset_att_items in itertools.combinations(items_not_part_of_set, i):                        
                        for subset in itertools.combinations(items, count):
                            considered_set_items = list(subset) + list(subset_att_items)
                            score =  self.process_set(GearSet(), list(considered_set_items))
                            scored_sets.append((score, list(considered_set_items)))
        
        return scored_sets