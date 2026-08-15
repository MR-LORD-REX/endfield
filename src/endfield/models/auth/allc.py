from pydantic import BaseModel

class Character(BaseModel):
    char_id: str
    name: str
    level: int
    potential_level: int
    evolve_phase: int
    rarity: int
    square_icon: str 
    proffesion: str  # keep Uppercase 
    element: str  # first letter Uppercase
    rect_icon: str
    splash_icon: str
    owned_at: int # timestamp of when the character was obtained

class AllCharacters(BaseModel):
    characters: list[Character]
    total: int = 0
    