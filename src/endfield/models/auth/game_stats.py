from typing import List 
from pydantic import BaseModel
from datetime import datetime

class SanityPoint(BaseModel):
    current: int
    max: int
    full_recover_at: datetime | None
    
class BattlePass(BaseModel):
    max_level: int
    current_level: int
    
class DailyPoints(BaseModel):
    current: int
    max: int
    
class WeeklyPoints(BaseModel):
    score: int
    total: int
    
class FactoryMoney(BaseModel):
    current: int
    max: int
    
class Settlement(BaseModel):
    id: str
    name: str
    level: int
    exp_to_level_up: int
    current_exp: int
    max_money: int
    remaining_money: int
    char_icon: str| None
    last_ticked: datetime | None
    
class Region(BaseModel):
    region_id: str
    region_name: str
    factory_level: int
    factory_money: FactoryMoney
    settlements: List[Settlement]
    
    
class Regions(BaseModel):
    all: List[Region]
    
class GameStats(BaseModel):
    regions: Regions
    sanity_point: SanityPoint
    battle_pass: BattlePass
    daily_points: DailyPoints
    weekly_points: WeeklyPoints