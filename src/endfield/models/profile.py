from __future__ import annotations
from pydantic import BaseModel


class DomainProgress(BaseModel):
    domain_id: str
    level: int
    name: str = "unknown"
    
class Medal(BaseModel):
    index: int
    name: str
    description: str
    icon_url: str
    
class Medals(BaseModel):
    medals: list[Medal]

class ProfileCharacter(BaseModel):
    template_id: int
    str_id: str
    name: str
    level: int
    potential_level: int
    rarity: int
    element: str
    profession: str
    splash_url: str
    round_icon_url: str


class PlayerProfile(BaseModel):
    uid: str
    name: str
    short_id: str
    signature: str
    avatar_url: str
    bg_url: str
    frame_url: str | None = None
    adventure_level: int
    world_level: int
    char_count: int
    weapon_count: int
    doc_count: int
    domain_progress: list[DomainProgress]
    medals: Medals
    characters: list[ProfileCharacter]
    ttl: int | None = None
