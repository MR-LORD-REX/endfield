from typing import Optional, Union, List, Dict, Literal

from ..models.basic.character import (
    ComputedStats, TalentInfo, SkillInfo, CharacterData,
    TalentPassiveNode, TalentFactoryNode, ComputedStatsWithDetails , StatDetail
)
from ..models.basic.equipment import EquipData, SuitSet
from ..models.basic.weapon import WeaponData


F_TYPES   = Literal["BaseAddition", "BaseMultiplier", "BaseFinalAddition", "BaseFinalMultiplier"]
ATTRI_IDS = Literal["39", "40", "41", "42"]

ID_TO_PROP: Dict[str, str] = {
    "1":  "MaxHp_base",
    "2":  "Atk_base",
    "3":  "Def_base",
    "9":  "CriticalRate_base",
    "10": "CriticalDamage_base",
    "17": "NormalAtkDamageIncrease_base",
    "28": "UltimateSkillDamageIncrease_base",
    "29": "HealOutputIncrease_base",
    "30": "HealTakenIncrease_base",
    "32": "NormalSkillDamageIncrease_base",
    "33": "ComboSkillDamageIncrease_base",
    "39": "Str_base",
    "40": "Agi_base",
    "41": "Wisd_base",
    "42": "Will_base",
    "44": "UltimateSpGainScalar_base",
    "50": "PhysicalDamageIncrease_base",
    "51": "FireDamageIncrease_base",
    "52": "PulseDamageIncrease_base",
    "53": "CrystDamageIncrease_base",
    "54": "NaturalDamageIncrease_base",
    "55": "EtherDamageIncrease_base",
    "87": "PhysicalAndSpellInflictionEnhance_base",
    "10000": "Main_ratio",
    "10001": "Sub_ratio",
}

ID_TO_OBJ_MAP: Dict[str, str] = {
    "1":  "hp",
    "2":  "atk",
    "3":  "defense",
    "9":  "crit_rate",
    "10": "crit_dmg",
    "17": "normal_atk_dmg_bonus",
    "28": "ult_skill_dmg_bonus",
    "29": "healing_bonus",
    "30": "healing_received_bonus",
    "32": "normal_skill_dmg_bonus",
    "33": "combo_skill_dmg_bonus",
    "39": "str",
    "40": "agi",
    "41": "wisd",
    "42": "will",
    "44": "ultimate_gain_efficiency",
    "50": "physical_dmg_bonus",
    "51": "fire_dmg_bonus",
    "52": "pulse_dmg_bonus",
    "53": "cryst_dmg_bonus",
    "54": "natural_dmg_bonus",
    "55": "ether_dmg_bonus",
    "87": "infliction_enhance",
    "10000": "main_attri_ratio",
    "10001": "sub_attri_ratio",
}

OBJ_TO_ID: Dict[str, str] = {v: k for k, v in ID_TO_OBJ_MAP.items()}

OBJ_TO_NAME: Dict[str, str] = {
    "hp": "HP",
    "atk": "Attack",
    "defense": "Defense",
    "crit_rate": "Critical Rate",
    "crit_dmg": "Critical DMG",
    "normal_atk_dmg_bonus": "Basic Attack DMG Bonus",
    "ult_skill_dmg_bonus": "Ultimate DMG Bonus",
    "healing_bonus": "Treatment Bonus",
    "healing_received_bonus": "Treatment Received Bonus",
    "normal_skill_dmg_bonus": "Battle Skill DMG Bonus",
    "combo_skill_dmg_bonus": "Combo Skill DMG Bonus",
    "str": "Strength",
    "agi": "Agility",
    "wisd": "Intellect",
    "will": "Will",
    "ultimate_gain_efficiency": "Ultimate Gain Efficiency",
    "physical_dmg_bonus": "Physical DMG Bonus",
    "fire_dmg_bonus": "Heat DMG Bonus",
    "pulse_dmg_bonus": "Electric DMG Bonus",
    "cryst_dmg_bonus": "Cryo DMG Bonus",
    "natural_dmg_bonus": "Nature DMG Bonus",
    "ether_dmg_bonus": "Ether DMG Bonus",
    "infliction_enhance": "Arts Intensity",
    "arts_intensity": "Arts Intensity",
    "main_attri_ratio": "Main Attribute Ratio",
    "sub_attri_ratio": "Sub Attribute Ratio",
}

INT_FIELDS    = {"hp", "atk", "defense", "str", "agi", "wisd", "will"}
CHAR_ATTRI    = {"39", "40", "41", "42"}
SPECIAL_IDS   = {"10000", "10001"}


class _HpState:
    __slots__ = ("mult", "flat", "final_mult")

    def __init__(self):
        self.mult:       float = 0.0   
        self.flat:       float = 0.0  
        self.final_mult: float = 0.0   

pending_attri_multipliers: list[tuple[str, float, str]] = []

def apply_prop(
    computed: ComputedStats,
    prop_id: str,
    value: int | float,
    formula: F_TYPES = "BaseAddition",
    main_attri_id: ATTRI_IDS = "39",
    sub_attri_id:  ATTRI_IDS = "40",
    base_attri_value: int | float = 0,   
    sub_attri_value:  int | float = 0,  
    base_atk: int = 0,
    base_hp:  int = 0,
    base_attributes: dict | None = None, 
    hp_state: _HpState | None = None,
) -> None:

    if prop_id in SPECIAL_IDS:
        attri_id = main_attri_id if prop_id == "10000" else sub_attri_id
        if attri_id not in CHAR_ATTRI:
            return
        base_val = base_attri_value if prop_id == "10000" else sub_attri_value
        obj      = ID_TO_OBJ_MAP[attri_id]
        cur      = getattr(computed, obj, 0) or 0
        if value <= 1.5 or formula == "BaseMultiplier":
            pending_attri_multipliers.append((attri_id, value, formula))
        else:
            new_val = cur + value
            setattr(computed, obj, int(new_val) if obj in INT_FIELDS else new_val)
        return

    obj = ID_TO_OBJ_MAP.get(prop_id)
    if obj is None:
        print(f"[apply_prop] Unknown prop_id: {prop_id}")
        return

    cur = getattr(computed, obj, None)
    if cur is None:
        cur = 0

    if prop_id == "1" and hp_state is not None:
        if formula == "BaseMultiplier":
            hp_state.mult += value
        elif formula in ("BaseAddition", "BaseFinalAddition"):
            hp_state.flat += value
        elif formula == "BaseFinalMultiplier":
            hp_state.final_mult += value
        else:
            print(f"[apply_prop] Unknown HP formula: {formula}")
        return

    if formula == "BaseAddition":
        new_val = cur + value

    elif formula == "BaseMultiplier":
        if prop_id == "2":          
            base_val = base_atk
        elif prop_id == "1":        
            base_val = base_hp
        elif base_attributes and prop_id in base_attributes:
            base_val = base_attributes[prop_id].value
        else:
            print(f"[apply_prop] BaseMultiplier: no base value for prop_id={prop_id}")
            return
        if not base_val:
            print(f"[apply_prop] BaseMultiplier: base_val is zero for prop_id={prop_id}")
            return
        new_val = cur + base_val * value

    elif formula == "BaseFinalAddition":
        new_val = cur + value

    elif formula == "BaseFinalMultiplier":
        new_val = cur + cur * value

    else:
        print(f"[apply_prop] Unknown formula: {formula}")
        return

    if obj in INT_FIELDS:
        new_val = int(new_val)
    setattr(computed, obj, new_val)

def compute_final_stats(character: CharacterData) -> ComputedStats:
    base_atk_char = character.base_atk.value
    base_hp       = character.base_hp.value

    main_attri_id = character.main_attribute.attri_id
    sub_attri_id  = character.sub_attribute.attri_id

    all_base_attri   = {item.attri_id: item for item in character.base_attribute}
    main_attri_value = all_base_attri[main_attri_id].value
    sub_attri_value  = all_base_attri[sub_attri_id].value

    base_str  = all_base_attri["39"].value
    base_agi  = all_base_attri["40"].value
    base_wisd = all_base_attri["41"].value
    base_will = all_base_attri["42"].value
    
    weapon_base_atk = character.weapon.base_atk
    weapon_skills   = {skill.skill_id: skill for skill in character.weapon.skills}

    total_base_atk = base_atk_char + weapon_base_atk

    computed = ComputedStats(
        str=int(base_str),
        agi=int(base_agi),
        wisd=int(base_wisd),
        will=int(base_will),
        hp=int(base_hp),
        atk=int(total_base_atk), 
        defense=0,
        crit_rate=0.05,
        crit_dmg=0.5,
        arts_intensity=0.0,
        healing_received_bonus=0.0,
        ultimate_gain_efficiency=1.0,
        healing_bonus=0.0,
        normal_atk_dmg_bonus=0.0,
        normal_skill_dmg_bonus=0.0,
        combo_skill_dmg_bonus=0.0,
        ult_skill_dmg_bonus=0.0,
        physical_dmg_bonus=0.0,
        fire_dmg_bonus=0.0,
        pulse_dmg_bonus=0.0,
        cryst_dmg_bonus=0.0,
        natural_dmg_bonus=0.0,
        ether_dmg_bonus=0.0,
        infliction_enhance=0.0,
    )

    hp_state = _HpState()

    def _apply(prop_id, value, formula):
        apply_prop(
            computed, prop_id, value, formula,
            main_attri_id, sub_attri_id,
            main_attri_value, sub_attri_value,
            int(total_base_atk), int(base_hp),
            all_base_attri, hp_state,
        )

                
    for equip in character.equips:
        for attri in equip.attr_modifiers:
            _apply(str(attri.attr_type), attri.value, attri.formula)



    if character.talents and character.talents.attr_nodes:
        t = character.talents.attr_nodes
        _apply(t.attri_id, t.total_value, t.formula)

    if character.suit_sets:
        for prop in character.suit_sets.active_bonus.propmap:
            _apply(prop.prop_id, prop.value, prop.formula)


    if character.talents.potential_attributes:
        for pote_attr in character.talents.potential_attributes:
            for attr in pote_attr.attributes:
                _apply(attr.attri_id, attr.value, attr.formula)
                
    for skill in weapon_skills.values():
        if type(skill.prop_id) == str:
            _apply(skill.prop_id, skill.value, skill.formula)
        elif type(skill.prop_id) == list:
            for i , prop_id in enumerate(skill.prop_id):
                val = skill.value[i] 
                formula = skill.formula[i]
                _apply(prop_id, val, formula)

    for attri_id, value, formula in pending_attri_multipliers:
        cur=getattr(computed, ID_TO_OBJ_MAP[attri_id], 0) or 0
        new_val = cur + cur * value
        setattr(computed, ID_TO_OBJ_MAP[attri_id], int(new_val))
       
    pending_attri_multipliers.clear()

    hp_before_mult = base_hp + computed.str * 5
    computed.hp = int(hp_before_mult * (1.0 + hp_state.mult) + hp_state.flat)
    if hp_state.final_mult:
        computed.hp = int(computed.hp * (1.0 + hp_state.final_mult))


    def _final_attri(attri_id: str) -> int:
        return {"39": computed.str, "40": computed.agi,
                "41": computed.wisd, "42": computed.will}.get(attri_id, 0)

    atk_mult = 1.0 + _final_attri(main_attri_id) * 0.005 + _final_attri(sub_attri_id) * 0.002
    computed.atk = round(computed.atk * atk_mult)

    computed.healing_received_bonus = round(computed.will * 0.001, 6)
    return computed
