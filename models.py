from typing import List, Optional
from pydantic import BaseModel, Field

def deduce_max_efficiency(base_steps: int, min_steps: int) -> float:
    if min_steps <= 0: return 0.0
    return (base_steps / min_steps) - 1.0

class Item(BaseModel):
    name: str
    slot: str
    skill: Optional[str] = None
    min_level: Optional[int] = None
    work_eff_percent: Optional[float] = None
    xp_percent: Optional[float] = None
    plus_xp: Optional[float] = None
    chest_percent: Optional[float] = None
    fine_mat_percent: Optional[float] = None
    double_rewards: Optional[float] = None
    double_action: Optional[float] = None
    minus_steps: Optional[int] = None
    minus_steps_percent: Optional[float] = None
    quality_outcome: Optional[float] = None
    no_mats_consumed_percent: Optional[float] = None
    bird_nest_percent: Optional[float] = None
    find_gems_percent: Optional[float] = None
    adventuring_guild_token_percent: Optional[float] = None
    collectible_percent: Optional[float] = None
    gain_coins_percent: Optional[float] = None
    roll_gem_pouch_table_percent: Optional[float] = None
    find_coin_pouch_percent: Optional[float] = None
    keywords: List[str] = Field(default_factory=list)
    region: Optional[str] = None
    underwater_only: bool = False
    clean_item_name: Optional[str] = None
    rarity_sort: Optional[int] = None
    uuid: Optional[str] = None
    export_name: Optional[str] = None

    @classmethod
    def from_csv_row(cls, row: dict):
        def _val(key, is_percent=False, type_func=str):
            v = row.get(key, '').strip()
            if not v or v == '-': return None
            if type_func == bool: return v.upper() == 'TRUE'
            if type_func == list: return [s.strip() for s in v.split(',')]
            if type_func == int: return int(v)
           
            val_str = v.replace('%', '')
            try:
                if is_percent or '%' in key:
                    return float(val_str) / 100.0
                return type_func(val_str)
            except ValueError:
                return None

        # Normalize "Global" to None
        skill_val = _val('Skill')
        if skill_val and skill_val.lower() == 'global':
            skill_val = None
        return cls(
            name=row['Item'],
            slot=row['Slot'],
            skill=skill_val,
            min_level=_val('Min Level', type_func=int),
            work_eff_percent=_val('Work %', type_func=float),
            xp_percent=_val('XP %', type_func=float),
            plus_xp=_val('Plus XP', type_func=float),
            chest_percent=_val('Chest %', type_func=float),
            fine_mat_percent=_val('Fine Mat %', type_func=float),

            double_rewards=_val('Dbl Rewards', is_percent=True, type_func=float),
            double_action=_val('Dbl Action', is_percent=True, type_func=float),
            quality_outcome=_val('Craft Outcome', is_percent=True, type_func=float),
            
            minus_steps=_val('Minus Steps', type_func=int),
            minus_steps_percent=_val('Minus Steps %',type_func=float),
            no_mats_consumed_percent=_val('No Mats %',type_func=float),
            bird_nest_percent=_val('Bird Nest %',type_func=float),
            find_gems_percent=_val('Find Gems %',type_func=float),
            adventuring_guild_token_percent=_val('Ad Guild Token %',type_func=float),
            collectible_percent=_val('Collectible %',type_func=float),
            gain_coins_percent=_val('Gain 1-10 Coins %',type_func=float),
            roll_gem_pouch_table_percent=_val('Roll Gem Pouch Table %',type_func=float),
            find_coin_pouch_percent=_val('Find 1 Coin Pouch %',type_func=float),
            keywords=_val('Keywords', type_func=list) or [],
            region=_val('Region'),
            underwater_only=_val('Underwater Only', type_func=bool) or False,
            rarity_sort=_val('Rarity Sort', type_func=int),
            clean_item_name=_val('Clean Item Name'),
            uuid=_val('UUID'),
            export_name=_val('Export Name')
        )

class Activity(BaseModel):
    activity: str
    locations: List[str] = Field(default_factory=list)
    region: Optional[str] = None
    required_keywords: List[str] = Field(default_factory=list)
    is_underwater: bool = False
    skill: Optional[str] = None
    skill_level: Optional[int] = None
    base_xp: Optional[float] = None
    base_gem_drop_rate: Optional[float] = None
    max_work_efficiency: Optional[float] = None
    base_steps: Optional[int] = None
    min_steps: Optional[int] = None

    @classmethod
    def from_csv_row(cls, row: dict):
        def _val(key, type_func=str):
            v = row.get(key, '').strip()
            if not v or v == '-': return None
            if type_func == bool: return v.upper() == 'TRUE'
            if type_func == list: return [s.strip() for s in v.split(',')]
            return type_func(v.replace('%', ''))

        return cls(
            activity=row['Activity'],
            locations=_val('Location(s)', list) or [],
            region=_val('Region'),
            required_keywords=_val('Required Keywords', list) or [],
            is_underwater=_val('Is Underwater', bool) or False,
            skill=_val('Skill1'),
            skill_level=_val('S1 Min', int),
            base_xp=_val('Base XP (S1)', float),
            base_gem_drop_rate=_val('Base Gem Drop Rate', float),
            base_steps=_val('Base Steps', int),
            min_steps=_val('"Min" Steps', int),
            max_work_efficiency=deduce_max_efficiency(base_steps=_val('Base Steps', int) or 0, min_steps=_val('"Min" Steps', int) or 0),
        )

class GearSet(BaseModel):
    head: Optional[Item] = None
    chest: Optional[Item] = None
    legs: Optional[Item] = None
    feet: Optional[Item] = None
    cape: Optional[Item] = None
    back: Optional[Item] = None
    neck: Optional[Item] = None
    hands: Optional[Item] = None
    primary: Optional[Item] = None
    secondary: Optional[Item] = None
    rings: List[Item] = Field(default_factory=list)
    tools: List[Item] = Field(default_factory=list)
    pet: Optional[Item] = None
    consumable: Optional[Item] = None

    @property
    def all_items(self) -> List[Item]:
        single = [self.head, self.chest, self.legs, self.feet, self.cape, self.back, self.neck, self.hands, self.primary, self.secondary, self.pet, self.consumable]
        return [i for i in single if i] + self.rings + self.tools

    def get_stats(self, activity_skill: str):
        stats = {
            "work_efficiency": 0.0, "xp_percent": 0.0, "flat_xp": 0.0,
            "chest_finding": 0.0, "double_action": 0.0, "double_rewards": 0.0,
            "no_mats": 0.0, "fine_material": 0.0,
            "flat_step_reduction": 0, "percent_step_reduction": 0.0
        }
        for item in self.all_items:
            item_skills = item.skill.split(',') if item.skill else []
            if item.skill is None or activity_skill in item_skills:
                if item.work_eff_percent: stats["work_efficiency"] += item.work_eff_percent
                if item.xp_percent: stats["xp_percent"] += item.xp_percent
                if item.plus_xp: stats["flat_xp"] += item.plus_xp
            
            if item.chest_percent: stats["chest_finding"] += item.chest_percent
            if item.double_action: stats["double_action"] += item.double_action
            if item.double_rewards: stats["double_rewards"] += item.double_rewards
            if item.no_mats_consumed_percent: stats["no_mats"] += item.no_mats_consumed_percent
            if item.fine_mat_percent: stats["fine_material"] += item.fine_mat_percent
            if item.minus_steps: stats["flat_step_reduction"] += item.minus_steps
            if item.minus_steps_percent: stats["percent_step_reduction"] += item.minus_steps_percent
        
        stats["double_action"] = min(1.0, stats["double_action"])
        stats["double_rewards"] = min(1.0, stats["double_rewards"])
        return stats