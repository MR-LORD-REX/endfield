from __future__ import annotations
from pydantic import BaseModel

from .profile import PlayerProfile
from .character import CharacterData


class ShowcaseData(BaseModel):
    """Root output model returned by Endfield.get_showcase()."""
    profile: PlayerProfile
    characters: list[CharacterData]
