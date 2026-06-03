from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class AttrModifier(BaseModel):
    index: int          # position in the attr_modifiers array
    attr_type: int      
    attr_name: str     
    formula: str        # "BaseAddition" | "BaseMultiplier" | "BaseFinalMultiplier"
    enhance_level: int  
    value: float 
    icon: str       


class EquipData(BaseModel):
    slot_id: int        
    template_id: int
    rarity: int
    suit_id: str
    icon_url: str
    attr_modifiers: list[AttrModifier]
    
class PropMap(BaseModel):
    prop_id: str
    prop_name: str
    value: float
    formula: str


class SuitSetEffect(BaseModel):
    tagid: str| None = None
    propmap: list[PropMap] | None = None


class SuitSet(BaseModel):
    suit_id: str
    name: Optional[str] = None    
    icon_url: str
    pieces_equipped: int
    is_active: bool              
    active_bonus: Optional[SuitSetEffect] = None
