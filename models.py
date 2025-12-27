from typing import List, Optional
from pydantic import BaseModel, Field

def deduce_max_efficiency(base_steps: int, min_steps: int) -> float:
    """
    Returns the effective max efficiency required to hit the min_steps.
    Matches logic in image_3a5dc4.png.
    """
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
        def _val(key, type_func=str):
            v = row.get(key, '').strip()
            if not v or v == '-': return None
            if type_func == bool: return v.upper() == 'TRUE'
            if type_func == list: return [s.strip() for s in v.split(',')]
            return type_func(v.replace('%', ''))

        return cls(
            name=row['Item'],
            slot=row['Slot'],
            skill=_val('Skill'),
            min_level=_val('Min Level', int),
            work_eff_percent=_val('Work %', float),
            xp_percent=_val('XP %', float),
            plus_xp=_val('Plus XP', float),
            chest_percent=_val('Chest %', float),
            fine_mat_percent=_val('Fine Mat %', float),
            double_rewards=_val('Dbl Rewards', float),
            double_action=_val('Dbl Action', float),
            minus_steps=_val('Minus Steps', int),
            minus_steps_percent=_val('Minus Steps %', float),
            quality_outcome=_val('Craft Outcome', float),
            no_mats_consumed_percent=_val('No Mats %', float),
            bird_nest_percent=_val('Bird Nest %', float),
            find_gems_percent=_val('Find Gems %', float),
            adventuring_guild_token_percent=_val('Ad Guild Token %', float),
            collectible_percent=_val('Collectible %', float),
            gain_coins_percent=_val('Gain 1-10 Coins %', float),
            roll_gem_pouch_table_percent=_val('Roll Gem Pouch Table %', float),
            find_coin_pouch_percent=_val('Find 1 Coin Pouch %', float),
            keywords=_val('Keywords', list) or [],
            region=_val('Region'),
            underwater_only=_val('Underwater Only', bool) or False,
            rarity_sort=_val('Rarity Sort', int),
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
            max_work_efficiency=deduce_max_efficiency(base_steps=_val('Base Steps', int), min_steps=_val('"Min" Steps', int)),
        )