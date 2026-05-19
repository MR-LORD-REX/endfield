from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)

ENKA_BASE = "https://enka.network"
ENDFIELDTOOLS_BASE = "https://endfieldtools.dev/localdb/optimized"
ROUND_ICON_BASE = "https://enka.network/ui/ef/charroundicon/icon_round_{tempId}.png"
SPLASH_BASE = "https://enka.network/ui/ef/splash/{tempId}.webp"
BG_BASE = "https://enka.network/ui/ef/charinfo/bg_charinfo_{str_id}.png"
ATTRIBUTE_BASE = "https://enka.network/ui/ef/attributeicon/{name}.png"
MEDAL_BASE="https://enka.network/ui/ef/{medal}.png"

domains={
    "domain_1": "Valley IV",
    "domain_2": "Wuling",
}


class AssetResolver:
    """
    Loads all static asset JSONs at init time.
    Provides sync lookups and async fetch+cache for missing weapon/suit details.
    """

    def __init__(self, assets_path: Path | str, session: aiohttp.ClientSession) -> None:
        self.assets_path = Path(assets_path)
        self.session = session
        self._load_all()

    def _load_json(self, filename: str) -> dict:
        path = self.assets_path / filename
        if not path.exists():
            logger.warning("Asset file not found: %s", path)
            return {}
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def _load_all(self) -> None:
        self.ascension_break_node:     dict = self._load_json("ascension_break_node.json")
        self.avatar_icon:              dict = self._load_json("avatar_icon.json")
        self.business_card_bg:         dict = self._load_json("business_card_bg.json")
        self.character_full:           dict = self._load_json("character_full.json")
        self.character:                dict = self._load_json("character.json")
        self.element:                  dict = self._load_json("element.json")
        self.equip_type:               dict = self._load_json("equip_type.json")
        self.formula_suffix:           dict = self._load_json("formula_suffix.json")
        self.gender:                   dict = self._load_json("gender.json")
        self.node_skill_type:          dict = self._load_json("node_skill_type.json")
        self.prop_by_id:               dict = self._load_json("prop_by_id.json")
        self.prop_by_name:             dict = self._load_json("prop_by_name.json")
        self.relic_item:               dict = self._load_json("relic_item.json")
        self.relic_suit:               dict = self._load_json("relic_suit.json")
        self.role:                     dict = self._load_json("role.json")
        self.splash_offset:            dict = self._load_json("splash_offset.json")
        self.weapon_breakthrough:      dict = self._load_json("weapon_breakthrough_template.json")
        self.weapon_gem_template:      dict = self._load_json("weapon_gem_template.json")
        self.weapon_gem_term:          dict = self._load_json("weapon_gem_term.json")
        self.weapon_skill:             dict = self._load_json("weapon_skill.json")
        self.weapon_type:              dict = self._load_json("weapon_type.json")
        self.weapon:                   dict = self._load_json("weapon.json")
        self.effects_map:              dict = self._load_json("effects_map.json")
        self.name_map:                 dict = self._load_json("nameMap.json")
        self.medals:                   dict = self._load_json("medals.json")
    
    def resolve_domain(self, domain_id: str) -> str:
        return domains.get(domain_id, domain_id)
    
    def get_round_icon_url(self, temp_id: str) -> str:
        return ROUND_ICON_BASE.format(tempId=temp_id)

    def get_splash_url(self, temp_id: str) -> str:
        return SPLASH_BASE.format(tempId=temp_id)
    
    def get_bg_url(self, str_id: str) -> str:
        return BG_BASE.format(str_id=str_id)
    
    def get_medal_url(self, medal: str) -> str:
        return MEDAL_BASE.format(medal=medal)
    
    def get_attribute_url(self, attri_id:str) -> str:
        attri=self.prop_by_id.get(str(attri_id), "Atk")
        attri_Name=attri.split("_")[0]
        return ATTRIBUTE_BASE.format(name=attri_Name)
    
    def get_item_icon_url(self, partial_icon: str) -> str:
        return ENKA_BASE + partial_icon
    
    def get_weapon_icon_url(self, weapon_id: str) -> Optional[str]:
        weapon_data = self.weapon.get(str(weapon_id))
        if not weapon_data:
            logger.warning("Weapon ID not found: %s", weapon_id)
            return None
        icon_path = weapon_data.get("Icon").split("/")[-1]
        return ENKA_BASE + "/ui/ef/itemicon/" + icon_path
    
    def get_name_from_id(self, id: str) -> str:
        hash=self.prop_by_id.get(str(id), "unknown")
        return self.name_map.get(hash, hash)
        
    def get_character_full(self, char_id: str) -> dict:
        return self.character_full.get(str(char_id), {})
    
    def get_character(self, char_id: str) -> dict:
        return self.character.get(str(char_id), {})
    
    def get_weapon(self, weapon_id: str) -> dict:
        return self.weapon.get(str(weapon_id), {})