from pydantic import BaseModel
from typing import Dict, List, Optional , Literal , Union

class OutputItems(BaseModel):
    id: str
    name: str
    per_minute: int
    icon_url: str

class Blueprint(BaseModel):
    id: str
    name: str
    description: str
    code: str
    screenshot_url: str
    region: str
    output_items: List[OutputItems]
    
class FactoryPlans(BaseModel):
    blueprints: List[Blueprint]