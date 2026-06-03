from __future__ import annotations
from pydantic import BaseModel


# class WeaponSkillProps(BaseModel):
#     prop_id: str
#     prop_name: str
#     value: float
#     formula: str

class MainStat(BaseModel):
    prop_id: str ="2"
    prop_name: str="Atk_base"
    value: int
    formula: str = "BaseAddition"
    icon_url: str = "https://enka.network/ui/ef/attributeicon/Atk.png"


class WeaponSkill(BaseModel):
    skill_id: str
    tag_id: str
    prop_id: str | list[str]
    base_lvl: int
    max_lvl: int
    current_lvl: int
    formula: str | list[str]
    prop_name: str | list[str]
    icon_url: str | list[str]
    value: float | list[float]
    
class Gem(BaseModel):
    rarity: int
    name: str
    inner_icon_url: str
    cover_icon_url: str


class WeaponData(BaseModel):
    weapon_id: str             
    name: str                  
    rarity: int
    weapon_type: str           
    level: int
    refine_lv: int
    breakthrough_lv: int
    base_atk: float            
    skill_levels: list[int]    
    icon_url: str
    skills: list[WeaponSkill]
    main_stat: MainStat
    gem: Gem | None
