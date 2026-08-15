from __future__ import annotations

import math
from pathlib import PurePosixPath
import re
from typing import Any

from ..resolver import AssetResolver


_SKILL_TYPES = (
    ("skill_type_normal_attack", "dispNormalAttackSkill", "NormalAttack"),
    ("skill_type_normal_skill", "normalSkill", "NormalSkill"),
    ("skill_type_ultimate_skill", "ultimateSkill", "UltimateSkill"),
    ("skill_type_combo_skill", "comboSkill", "ComboSkill"),
)

_EQUIP_SLOTS = (
    ("bodyEquip", 1, "body"),
    ("secondAccessory", 3, "edc"),
    ("firstAccessory", 2, "edc"),
    ("armEquip", 0, "hand"),
)

_GAME_PROPERTY_EXPANSIONS = {
    "cryst_and_pulse_damage_increase": (
        "cryst_damage_increase",
        "pulse_damage_increase",
    ),
    "fire_and_natural_damage_increase": (
        "fire_damage_increase",
        "natural_damage_increase",
    ),
    "main": ("main_ratio",),
    "sub": ("sub_ratio",),
}


class GameCharacterAdapter:
    """Translate a Skport game character into the Enka-like builder input."""

    def __init__(self, resolver: AssetResolver) -> None:
        self.resolver = resolver

    def convert(self, game_character: dict[str, Any]) -> dict[str, Any]:
        template_id = self._resolve_character_template_id(game_character)
        return {
            "templateId": template_id,
            "level": int(game_character.get("level", 1)),
            "potentialLevel": int(game_character.get("potentialLevel", 0)),
            "equip": self._convert_equips(game_character),
            "weapon": self._convert_weapon(game_character.get("weapon") or {}),
            "skillInfo": self._convert_skills(game_character, template_id),
            "talent": self._convert_talent(game_character, template_id),
        }

    def _resolve_character_template_id(self, game_character: dict[str, Any]) -> int:
        talent = game_character.get("talent") or {}
        char_data = game_character.get("charData") or {}
        passive_node_ids = list(talent.get("latestPassiveSkillNodes") or [])
        for template_id, character in self.resolver.character.items():
            str_id = str(character.get("StrId", ""))
            if str_id and any(
                node_id == str_id or str(node_id).startswith(f"{str_id}_")
                for node_id in passive_node_ids
            ):
                return int(template_id)

        node_ids = list(talent.get("attrNodes") or [])
        for field in ("abilityTalents", "combatTalents", "cultivationTalents"):
            node_ids.extend(
                node.get("id", "")
                for node in char_data.get(field) or []
                if isinstance(node, dict)
            )

        for template_id, character in self.resolver.character.items():
            str_id = str(character.get("StrId", ""))
            if str_id and any(
                node_id == str_id or str(node_id).startswith(f"{str_id}_")
                for node_id in node_ids
            ):
                return int(template_id)

        game_name = str(char_data.get("name", ""))
        matches = [
            int(template_id)
            for template_id, character in self.resolver.character.items()
            if self._localized_name(character) == game_name
        ]
        if len(matches) == 1:
            return matches[0]
        raise ValueError(
            f"Could not map game character {game_name!r} to an Enka template ID"
        )

    def _convert_talent(
        self,
        game_character: dict[str, Any],
        template_id: int,
    ) -> dict[str, Any]:
        talent = dict(game_character.get("talent") or {})
        character = self.resolver.get_character(str(template_id))
        attr_node_ids = set((character.get("AttributeNodes") or {}).keys())
        skill_node_ids = set((character.get("NodeSkillMap") or {}).keys())

        talent["attrNodes"] = [
            self._resolve_node_id(str(node_id), attr_node_ids)
            for node_id in talent.get("attrNodes") or []
        ]
        for field in (
            "latestPassiveSkillNodes",
            "latestFactorySkillNodes",
            "latestSpaceshipSkillNodes",
        ):
            talent[field] = [
                self._resolve_node_id(str(node_id), skill_node_ids)
                for node_id in talent.get(field) or []
            ]
        return talent

    @staticmethod
    def _resolve_node_id(node_id: str, candidates: set[str]) -> str:
        if node_id in candidates:
            return node_id
        suffix = node_id.rpartition("_")[2]
        matches = [candidate for candidate in candidates if candidate.endswith(f"_{suffix}")]
        return matches[0] if len(matches) == 1 else node_id

    def _convert_skills(
        self,
        game_character: dict[str, Any],
        template_id: int,
    ) -> dict[str, Any]:
        character = self.resolver.get_character(str(template_id))
        str_id = str(character.get("StrId", ""))
        static_skills = game_character.get("charData", {}).get("skills") or []
        user_skills = game_character.get("userSkills") or {}
        static_by_type = {
            skill.get("type", {}).get("key"): skill
            for skill in static_skills
            if isinstance(skill, dict)
        }

        result: dict[str, Any] = {
            "normalSkill": "",
            "ultimateSkill": "",
            "comboSkill": "",
            "dispNormalAttackSkill": "",
            "levelInfo": [],
        }
        for game_type, field, suffix in _SKILL_TYPES:
            static_skill = static_by_type.get(game_type)
            canonical_id = f"{str_id}_{suffix}"
            if canonical_id not in character.get("SkillInfoMap", {}):
                continue

            result[field] = canonical_id
            game_skill_id = str((static_skill or {}).get("id", ""))
            skill_state = user_skills.get(game_skill_id) or {}
            level = int(skill_state.get("level", 1))
            result["levelInfo"].append(
                {
                    "skillId": canonical_id,
                    "skillLevel": level,
                    "skillMaxLevel": int(skill_state.get("maxLevel", 12)),
                    "skillEnhancedLevel": level,
                }
            )
        return result

    def _convert_weapon(self, game_weapon: dict[str, Any]) -> dict[str, Any]:
        weapon_data = game_weapon.get("weaponData") or {}
        if not weapon_data:
            return {}

        template_id = self._resolve_weapon_template_id(weapon_data)
        return {
            "templateId": template_id,
            "weaponLv": int(game_weapon.get("level", 1)),
            "refineLv": int(game_weapon.get("refineLevel", 0)),
            "breakthroughLv": int(game_weapon.get("breakthroughLevel", 0)),
            "attachedGem": self._convert_gem(game_weapon),
        }

    def _resolve_weapon_template_id(self, weapon_data: dict[str, Any]) -> int:
        game_name = str(weapon_data.get("name", ""))
        game_rarity = self._rarity(weapon_data.get("rarity"))
        game_type = str(weapon_data.get("type", {}).get("key", "")).removeprefix(
            "weapon_type_"
        )
        candidates = []
        for template_id, weapon in self.resolver.weapon.items():
            if self._localized_name(weapon) != game_name:
                continue
            if game_rarity and int(weapon.get("Rarity", 0)) != game_rarity:
                continue
            local_type = str(weapon.get("WeaponType", "")).lower()
            if game_type and local_type != game_type.lower():
                continue
            candidates.append(int(template_id))

        if len(candidates) == 1:
            return candidates[0]
        raise ValueError(f"Could not map game weapon {game_name!r} to an Enka ID")

    def _convert_gem(self, game_weapon: dict[str, Any]) -> dict[str, Any]:
        game_gem = game_weapon.get("gem") or {}
        gem_data = game_gem.get("gemData") or {}
        if not gem_data:
            return {}

        game_template = str(gem_data.get("templateId", ""))
        template_ids = [
            int(template_id)
            for template_id, template in self.resolver.weapon_gem_template.items()
            if PurePosixPath(str(template.get("Icon", ""))).stem == game_template
        ]
        if len(template_ids) != 1:
            raise ValueError(f"Could not map game gem template {game_template!r}")

        skill_infos = {
            info.get("skill", {}).get("key"): info
            for info in game_weapon.get("weaponData", {}).get("skillInfos") or []
        }
        term_metadata: dict[str, tuple[str, int]] = {}
        for term_type, skill in enumerate(game_weapon.get("skills") or [], start=1):
            info = skill_infos.get(skill.get("key")) or {}
            term_metadata[str(skill.get("gemTermId", ""))] = (
                str(info.get("gemTagId", "")),
                term_type,
            )

        terms = []
        for term_index, game_term in enumerate(
            game_gem.get("terms") or [],
            start=1,
        ):
            game_term_id = str(game_term.get("id", ""))
            tag_id, term_type = term_metadata.get(game_term_id, ("", 0))
            matches = [
                int(term_id)
                for term_id, term in self.resolver.weapon_gem_term.items()
                if str(term.get("TagId", "")) == tag_id
                and int(term.get("TermType", 0)) == term_type
            ]
            if len(matches) != 1:
                # The endpoint can return a socketed third term that differs
                # from the weapon's currently described innate skill. The
                # localized term name and its ordered socket type still map
                # directly to the Enka asset entry.
                game_term_name = str(game_term.get("name", ""))
                matches = [
                    int(term_id)
                    for term_id, term in self.resolver.weapon_gem_term.items()
                    if int(term.get("TermType", 0)) == term_index
                    and self._localized_term_name(term) == game_term_name
                ]
            if len(matches) != 1:
                raise ValueError(
                    f"Could not map game gem term {game_term.get('name', game_term_id)!r}"
                )
            terms.append(
                {
                    "termNumId": matches[0],
                    "cost": int(game_term.get("cost", 0)),
                }
            )

        return {
            "templateId": template_ids[0],
            "terms": terms,
            "totalCost": sum(term["cost"] for term in terms),
        }

    def _convert_equips(self, game_character: dict[str, Any]) -> list[dict[str, Any]]:
        equips = []
        for field, slot_id, slot_type in _EQUIP_SLOTS:
            game_equip = game_character.get(field) or {}
            if not game_equip.get("equipData"):
                continue
            template_id = self._resolve_equip_template_id(game_equip, slot_type)
            enhance = game_equip.get("enhance") or {}
            enhance_items = (
                enhance.items() if isinstance(enhance, dict) else ()
            )
            equips.append(
                {
                    "key": slot_id,
                    "value": {
                        "templateid": template_id,
                        "enhance": [
                            {"key": int(index), "value": int(level)}
                            for index, level in sorted(
                                enhance_items, key=lambda item: int(item[0])
                            )
                        ],
                    },
                }
            )
        return equips

    def _resolve_equip_template_id(
        self,
        game_equip: dict[str, Any],
        slot_type: str,
    ) -> int:
        equip_data = game_equip.get("equipData") or {}
        suit = equip_data.get("suit") or {}
        suit_name = str(suit.get("name", ""))
        suit_ids = {
            suit_id
            for suit_id, suit in self.resolver.relic_suit.items()
            if self._localized_name(suit) == suit_name
        }
        if suit_name and not suit_ids:
            raise ValueError(
                f"Could not map game equipment suit {suit_name!r}"
            )
        game_properties = []
        for prop in equip_data.get("properties") or []:
            if str(prop).strip():
                game_properties.extend(self._normalize_game_property(str(prop)))
        game_rarity = self._rarity(equip_data.get("rarity"))
        base_value = float(equip_data.get("baseAttrValue", 0))

        broad_matches = []
        exact_matches = []
        for template_id, item in self.resolver.relic_item.items():
            item_suit_id = str(item.get("SuitId") or "")
            if suit_ids and item_suit_id not in suit_ids:
                continue
            # A null suit in the game API denotes a standalone item. Do not
            # let a same-stat set item become an accidental match.
            if not suit_name and item_suit_id:
                continue
            if game_rarity and int(item.get("Rarity", 0)) != game_rarity:
                continue
            icon = str(item.get("Icon", ""))
            if f"_{slot_type}_" not in icon:
                continue
            modifiers = item.get("AttrModifiers") or []
            if not modifiers:
                continue
            values = modifiers[0].get("Values") or [0]
            if not values or not self._base_value_matches(float(values[0]), base_value):
                continue
            broad_matches.append(int(template_id))

            local_properties = [
                self._normalize_property(
                    self.resolver.prop_by_id.get(str(modifier.get("AttrType")), "")
                )
                for modifier in modifiers[1:]
            ]
            if local_properties == game_properties:
                exact_matches.append(int(template_id))

        if len(exact_matches) == 1:
            return exact_matches[0]
        if len(broad_matches) == 1:
            return broad_matches[0]
        raise ValueError(
            f"Could not uniquely map game equipment {equip_data.get('name', '')!r}"
        )

    def _localized_name(self, data: dict[str, Any]) -> str:
        name_hash = str(data.get("NameHash", ""))
        return str(self.resolver.name_map.get(name_hash, name_hash))

    def _localized_term_name(self, data: dict[str, Any]) -> str:
        name_hash = str(data.get("TagNameHash", ""))
        return str(self.resolver.name_map.get(name_hash, name_hash))

    @staticmethod
    def _normalize_property(name: str) -> str:
        value = str(name).removesuffix("_base")
        value = re.sub(r"(?<!^)(?=[A-Z])", "_", value)
        return value.lower()

    @staticmethod
    def _normalize_game_property(name: str) -> list[str]:
        value = name.removeprefix("equip_attr_")
        value = value.removeprefix("equip_")
        value = re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
        return list(_GAME_PROPERTY_EXPANSIONS.get(value, (value,)))

    @staticmethod
    def _base_value_matches(local_value: float, game_value: float) -> bool:
        if math.isclose(local_value, game_value, rel_tol=0.0, abs_tol=1e-6):
            return True
        # The game endpoint truncates some lower-rarity base values (for
        # example 28.8 is returned as 28). Preserve that representation while
        # still requiring an exact integer match after truncation.
        return (
            game_value.is_integer()
            and local_value >= 0
            and math.floor(local_value) == int(game_value)
        )

    @staticmethod
    def _rarity(value: Any) -> int:
        if isinstance(value, dict):
            value = value.get("key") or value.get("value")
        match = re.search(r"(\d+)$", str(value or ""))
        return int(match.group(1)) if match else 0
