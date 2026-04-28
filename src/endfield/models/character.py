from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from .weapon import WeaponData
from .equipment import EquipData, SuitSet


class SkillInfo(BaseModel):
    skill_id: int
    icon_url: str
    element: str
    level: int
    max_level: int
    enhanced_level: int
    
class SkillMeta(BaseModel):
    normal_skill: str
    ultimate_skill: str
    combo_skill: str
    disp_normal_atk_skill: str
    skills: list[SkillInfo]

class AttrNode(BaseModel):
    attri_id: str
    attri_name: str
    formula: str = "BaseAddition"
    icon_url: str
    values: list[int]    
    total_value: int
    level: int
    
class PoteAtrri(BaseModel):
    attri_id: str
    attri_name: str
    icon_url: str
    value: int | float
    is_float: bool = False
    formula: str
    
class PotentialAttributes(BaseModel):
    required_potential_level: int
    attributes: list[PoteAtrri]
    
class TalentPassiveNode(BaseModel):
    node_id: str
    icon_url: str
    level: int    # 1–3 tier
    index: int    # position in the talent tree
    is_max: bool = False
    type: int


class TalentFactoryNode(BaseModel):
    node_id: str
    icon_url: str
    level: int
    index: int
    is_max: bool = False
    type: int


class TalentInfo(BaseModel):
    latest_break_node: str              
    attr_nodes: AttrNode   
    passive_nodes: list[TalentPassiveNode]
    factory_nodes: list[TalentFactoryNode]
    potential_attributes: list[PotentialAttributes] = []


class ComputedStats(BaseModel):
    str: int
    agi: int
    wisd: int
    will: int
    hp: int
    atk: int
    defense: int
    crit_rate: float = 5.0
    crit_dmg: float  = 50.0
    arts_intensity: float
    healing_received_bonus: float = 0.0
    ultimate_gain_efficiency: float = 100.0

    healing_bonus: Optional[float] = None
    normal_atk_dmg_bonus: Optional[float] = None
    normal_skill_dmg_bonus: Optional[float] = None
    combo_skill_dmg_bonus: Optional[float] = None
    ult_skill_dmg_bonus: Optional[float] = None
    
    physical_dmg_bonus: Optional[float] = None
    fire_dmg_bonus: Optional[float] = None
    pulse_dmg_bonus: Optional[float] = None
    cryst_dmg_bonus: Optional[float] = None
    natural_dmg_bonus: Optional[float] = None
    ether_dmg_bonus: Optional[float] = None
    infliction_enhance: Optional[float] = None
    
class CharAttr(BaseModel):
    attri_id: str
    attri_name: str
    url: str
    
class BaseAttr(BaseModel):
    attri_id: str 
    attri_name: str
    url: str
    value: int | float
    is_float: bool = False

class CharacterData(BaseModel):
    template_id: int
    str_id: str        
    name: str
    rarity: int
    element: str
    profession: str
    weapon_type: str
    level: int
    potential_level: int
    splash_url: str
    bg_url: str
    round_icon_url: str
    # Build
    main_attribute: CharAttr
    sub_attribute:  CharAttr
    base_atk: BaseAttr 
    base_hp: BaseAttr
    base_attribute: list[BaseAttr] = []
    weapon: Optional[WeaponData] = None
    equips: list[EquipData] = []
    suit_sets: SuitSet | None = None
    skills: SkillMeta 
    talents: Optional[TalentInfo] = None
    stats: Optional[ComputedStats] = None