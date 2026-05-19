from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
import json
from collections import Counter

import aiohttp
import asyncio

from .decoder import DataDecoder
from .resolver import AssetResolver
from .calculator import compute_final_stats
from .errors import APIError, CharacterNotFoundError, WeaponNotFoundError
from .models import (
    ShowcaseData, PlayerProfile, ProfileCharacter, DomainProgress,
    CharacterData, ComputedStats, SkillInfo, SkillMeta , TalentInfo, 
    TalentPassiveNode, TalentFactoryNode, AttrNode, PoteAtrri, PotentialAttributes,
    WeaponData, WeaponSkill, MainStat,CharAttr,BaseAttr,
    EquipData, AttrModifier, SuitSet, SuitSetEffect,PropMap ,
    StatDetail , ComputedStatsWithDetails , Gem , Medal , Medals
)
from .update import check_update, download_update
from .calculator import ID_TO_PROP, ID_TO_OBJ_MAP, OBJ_TO_ID , OBJ_TO_NAME

logger = logging.getLogger(__name__)

_ENKA_API = "https://enka.network/ef/{uid}/__data.json?x-sveltekit-invalidated=01"


class Endfield:

    def __init__(
        self,
        session: Optional[aiohttp.ClientSession] = None,
        debug: bool = False,
    ) -> None:
        self._assets_path = Path(__file__).parent / "assets"
        self._external_session = session
        self._session: Optional[aiohttp.ClientSession] = aiohttp.ClientSession() 
        self._resolver: Optional[AssetResolver] = AssetResolver(self._assets_path, self._session)
        self._debug = debug

        log_level = logging.DEBUG if debug else logging.WARNING
        logging.basicConfig(
            level=log_level,
            format="%(levelname)s [%(name)s] %(message)s",
        )
        logger.setLevel(log_level)

    async def __aenter__(self) -> "Endfield":
        await self._init_session()
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
        
    def __exit__(self, exc_type, exc, tb):
        if self._session :
            asyncio.run(self.close())

    async def _init_session(self) -> None:
        if self._external_session:
            self._session = self._external_session
        else:
            self._session = aiohttp.ClientSession()
        self._resolver = AssetResolver(self._assets_path, self._session)

    async def close(self) -> None:
        if self._session and not self._external_session:
            await self._session.close()
            
    def get_detailed_stats(self, char_data: CharacterData) -> ComputedStatsWithDetails:
        details = []
        main_att= char_data.main_attribute.attri_id
        sub_att= char_data.sub_attribute.attri_id
        for obj_name, display_name in OBJ_TO_NAME.items():
            value = getattr(char_data.stats, obj_name, None)
            if value is not None:
                prop_id = OBJ_TO_ID.get(obj_name, "unknown")
                details.append(StatDetail(
                    value=value,
                    name=display_name,
                    icon_url=self._resolver.get_attribute_url(prop_id),
                    stat_id=prop_id,
                    main_attri= prop_id == main_att,
                    sub_attri= prop_id == sub_att
                ))
        return ComputedStatsWithDetails(all=details)

    async def get_showcase(self, uid: int | str) -> ShowcaseData:
        if not self._session:
            await self._init_session()
        raw = await self._fetch_api(str(uid))
        decoded = DataDecoder(raw).decode()
        char_data = decoded["playerInfo"].get("charData", [])
        if self._debug:
            with open(f"debug_{uid}.json", "w", encoding="utf-8") as f:
                json.dump(decoded, f, ensure_ascii=False, indent=2)
                
        profile= await self._build_player_profile(decoded)
        
        c_tasks = []
        for cd in char_data:
            c_tasks.append(self._build_character_data(cd))
        characters = await asyncio.gather(*c_tasks)
        c_tasks.clear()
        
        for c in characters:
            st=self.get_detailed_stats(c)
            c.detailed_stats= st
            
        sk= ShowcaseData(
            profile=profile,
            characters=characters
        )
        if self._debug:
            with open(f"debug_showcase_{uid}.json", "w", encoding="utf-8") as f:
                js=sk.model_dump_json(indent=2)
                f.write(js)
        return sk
    
    async def get_character_showcase(self, uid: int | str, index: int = 0) -> CharacterData:
        if not self._session:
            await self._init_session()
        raw = await self._fetch_api(str(uid))
        decoded = DataDecoder(raw).decode()
        char_data = decoded["playerInfo"].get("charData", [])
        if index < 0 or index >= len(char_data):
            raise CharacterNotFoundError(f"Character index {index} out of range for user {uid}")
        char_data= char_data[index]
        character = await self._build_character_data(char_data)
        character.detailed_stats= self.get_detailed_stats(character)
        return character
    
    async def get_profile(self, uid: int | str) -> PlayerProfile:
        if not self._session:
            await self._init_session()
        raw = await self._fetch_api(str(uid))
        decoded = DataDecoder(raw).decode()
        return await self._build_player_profile(decoded)
    
    async def check_for_updates(self) :
        return await check_update()
    
    async def update_assets(self) -> None:
        await download_update()

    async def test_equip(self, uid: int | str):
        if not self._session:
            await self._init_session()
        raw = await self._fetch_api(str(uid))
        decoded = DataDecoder(raw).decode()
        char_data = decoded["playerInfo"].get("charData", [])
        char_data= char_data[0] 
        equip= char_data["equip"][0]
        equip_data= await self._build_equip(equip)
        logger.debug(f"Equip data: {equip_data}")
        
    async def test_suit_set(self, suit_id: str, active:bool=False, equiped:int=0):
        suit= await self._build_suit_set(suit_id, active, equiped)
        logger.debug(f"Suit set: {suit}")
    
    async def test_weapon(self, uid: int | str):
        if not self._session:
            await self._init_session()
        raw = await self._fetch_api(str(uid))
        decoded = DataDecoder(raw).decode()
        char_data = decoded["playerInfo"].get("charData", [])
        for cd in char_data:
            char_id= cd.get("templateId", 0)
            char_info = self._resolver.get_character(str(char_id))
            logger.debug(f"Character: {char_info.get('NameHash', 'unknown')} (ID: {char_id})")
            weapon_raw= cd.get("weapon", {})
            weapon_data= await self._build_weapon(weapon_raw)
            logger.debug(f"Weapon data: {weapon_data}")
            
    async def test_skill_meta(self, uid: int | str):
        if not self._session:
            await self._init_session()
        raw = await self._fetch_api(str(uid))
        decoded = DataDecoder(raw).decode()
        char_data = decoded["playerInfo"].get("charData", [])
        for cd in char_data:
            char_id= cd.get("templateId", 0)
            skill_info= cd.get("skillInfo", {})
            skill_meta= await self._build_skill_meta(skill_info, str(char_id))
            logger.debug(f"Character ID: {char_id}, Skill Meta: {skill_meta}")
    
    async def test_talent_info(self, uid: int | str):
        if not self._session:
            await self._init_session()
        raw = await self._fetch_api(str(uid))
        decoded = DataDecoder(raw).decode()
        char_data = decoded["playerInfo"].get("charData", [])
        for cd in char_data:
            char_id= cd.get("templateId", 0)
            talent_info= cd.get("talent", {})
            pote= cd.get("potentialLevel", 0)
            talent_meta= await self._build_talent_info(talent_info, str(char_id),potential=pote)
            logger.debug(f"Character ID: {char_id}, Talent Info: {talent_meta}")
    
    async def test_full_character_data(self, uid: int | str):
        if not self._session:
            await self._init_session()
        raw = await self._fetch_api(str(uid))
        decoded = DataDecoder(raw).decode()
        char_data = decoded["playerInfo"].get("charData", [])
        for cd in char_data:
            char_id= cd.get("templateId", 0)
            char_full_data= await self._build_character_data(cd)
            logger.debug(f"Character ID: {char_id}, Full Data: {char_full_data}")
            
    async def _fetch_api(self, uid: str) -> dict:
        url = _ENKA_API.format(uid=uid)
        logger.debug(f"Fetching API: {url}")
        async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                raise APIError(resp.status, url)
            return await resp.json(content_type=None)

    async def _build_player_profile(self, decoded: dict) -> PlayerProfile:
        player= decoded["playerInfo"].get("businessCard", {}) 
        stats= player.get("statistic", {})
        char_list = player.get("charList", [])
        char_data_list = decoded["playerInfo"].get("charData", [])
        domain_progress = []
        for domain in player["domainDev"]["domains"]:
            domain_progress.append(DomainProgress(
                domain_id=domain["domainId"],
                level=domain["level"],
                name=self._resolver.resolve_domain(domain["domainId"]),
            ))
        characters = []
        for cl , cd in zip(char_list, char_data_list):
            try:
                temp_id = cd.get("templateId", 27)
                temp_id_str = cl.get("templateId", "unknown")
                char_info = self._resolver.get_character(str(temp_id))
                characters.append(ProfileCharacter(
                    template_id=temp_id,
                    str_id=temp_id_str,
                    name=self._resolver.name_map.get(str(char_info.get("NameHash", "unknown")), "unknown"),
                    level=cl.get("level", 1),
                    potential_level=cl.get("potentialLevel", 0),
                    rarity=char_info.get("Rarity", 6),
                    element=char_info.get("Element", "unknown"),
                    profession=char_info.get("Profession", "unknown"),
                    splash_url=self._resolver.get_splash_url(temp_id_str),
                    round_icon_url=self._resolver.get_round_icon_url(temp_id_str),
                ))
            except Exception as e:
                logger.warning(f"Failed to process character {cl.get('templateId', 'unknown')}: {e}")
                continue
            
        medals = await self._build_medals(player.get("achievement", {}))
        
        bg_url = self._resolver.business_card_bg.get(str(player.get("businessCardTopicId", ""))).get("Icon", "")
        bg_url = self._resolver.get_pfp_bg_url(bg_url) 
        avatar_url = self._resolver.avatar_icon.get(str(player.get("userAvatarId", ""))).get("Icon", "")
        avatar_url = self._resolver.get_item_icon_url(avatar_url) 
        
        return PlayerProfile(
            uid=decoded.get("uid", "unknown"),
            name=player.get("name", "unknown"),
            short_id=player.get("shortId", "unknown"),
            signature=player.get("signature", ""),
            avatar_url=avatar_url,
            bg_url=bg_url,
            adventure_level=player.get("adventureLevel", 0),
            world_level=player.get("worldLevel", 0),
            char_count=stats.get("charNum", 0),
            weapon_count=stats.get("weaponNum", 0),
            doc_count=stats.get("docNum", 0),
            medals=medals,
            domain_progress=domain_progress,
            characters=characters,
        )
        
    async def _build_medals(self, achievement_data: dict) -> Medals:
        medals = []
        display_list = achievement_data.get("infoList", [])
        display_order= achievement_data.get("display", [])
        display_map = {item.get("value"): item.get("key") for item in display_order}

        for entry in display_list:
            medal_id = entry.get("achieveNumId")
            medal_level = entry.get("level")
            
            if not medal_id:
                continue
                
            medal_info = self._resolver.medals.get(str(medal_id), {})
            if not medal_info:
                logger.warning(f"Medal ID not found: {medal_id}")
                continue
            
            medal_name = medal_info.get("Name", "unknown")
            level_infos = medal_info.get("LevelInfos", {})

            description = ""
            if level_infos:
                description= level_infos.get(str(medal_level), {}).get("ConditionDesc", "")
                icon_id = level_infos.get(str(medal_level), {}).get("Icon", "")
            medal_url = self._resolver.get_medal_url(icon_id)
            
            medals.append(Medal(
                index=display_map.get(medal_id, 0),
                name=medal_name,
                description=description,
                icon_url=medal_url,
            ))
        
        return Medals(medals=medals)
    
    async def _build_equip(self, equip_raw: dict) -> EquipData:
        slot_id = equip_raw.get("key", 0)
        template_id = equip_raw.get("value", {}).get("templateid", 0)
        item_info = self._resolver.relic_item.get(str(template_id), {})
        if not item_info:
            logger.warning(f"Relic item not found for template_id: {template_id}")
        attribute_modifiers = []
        attr_mods_list = item_info.get("AttrModifiers", [])
        if not attr_mods_list:
            logger.warning(f"No AttrModifiers found for relic item {template_id}")
            return EquipData(
                slot_id=slot_id,
                template_id=template_id,
                rarity=item_info.get("Rarity", 5),
                suit_id=item_info.get("SuitId", 0),
                attr_modifiers=attribute_modifiers,
                icon_url=self._resolver.get_item_icon_url(item_info.get("Icon", "")),
            )
        
        enhance_map = {}
        for en in equip_raw["value"].get("enhance", []):
            enhance_map[en.get("key", 0)] = en.get("value", 0)

        prev_level    = None
        prev_index    = None
        prev_attr_type = None

        for index, attr_mod in enumerate(attr_mods_list):
            attr_type = attr_mod.get("AttrType", 0)
            formula   = attr_mod.get("Formula", "unknown")
            values    = attr_mod.get("Values", [0])

            if index in enhance_map:
                # This index has its own explicit enhance key
                enhance_level  = enhance_map[index]
                prev_level     = enhance_level
                prev_index     = index
                prev_attr_type = attr_type

            elif (
                prev_level is not None
                and prev_index is not None
                and index == prev_index + 1          
                and attr_type == prev_attr_type
                or (attr_type == attr_mods_list[-1].get("AttrType"))      
            ):
                enhance_level  = prev_level
                prev_index     = index               
            else:
                enhance_level  = 0
                prev_level     = None
                prev_index     = None
                prev_attr_type = None
            if enhance_level is None:
                enhance_level = 0
            value       = values[enhance_level] 
            enhance_lvl = enhance_level + 1 

            attribute_modifiers.append(AttrModifier(
                index=index,
                attr_type=attr_type,
                attr_name=self._resolver.prop_by_id.get(str(attr_type), "unknown"),
                formula=formula,
                enhance_level=enhance_lvl,
                value=round(value, 3),
                icon=self._resolver.get_attribute_url(attr_type)
            ))
        
        return EquipData(
            slot_id=slot_id,
            template_id=template_id,
            rarity=item_info.get("Rarity", 5),
            suit_id=item_info.get("SuitId", 0),
            attr_modifiers=attribute_modifiers,
            icon_url=self._resolver.get_item_icon_url(item_info.get("Icon", "")),
        )
    
    async def _build_suit_set(self, suit_id: str,active:bool=False,equiped:int=0) -> SuitSet:
        suit_info = self._resolver.relic_suit.get(str(suit_id), {})
        if not suit_info:
            logger.warning(f"Relic suit not found for suit_id: {suit_id}")
        skill_id= suit_info.get("SkillId", "")
        if not skill_id:
            logger.warning(f"No SkillId found for suit {suit_id}")
        skill_info = self._resolver.effects_map.get(str(skill_id), {})
        if not skill_info:
            logger.warning(f"Skill info not found for skill_id: {skill_id}")
        skill_map=[]
        for key, value in skill_info.get("PropMap", {}).items():
            values_list = value.get("Values", [0])
            value_index = min(max(0, equiped - 1), len(values_list) - 1)
            skill_map.append(PropMap(
                prop_id=str(key),
                prop_name=self._resolver.prop_by_id.get(str(key), "unknown"),
                value=values_list[value_index],
                formula=value.get("Formula", "unknown")
            ))
        active_bonus = SuitSetEffect(
            tagid=skill_info.get("TagId", ""),
            propmap=skill_map
        )
        return SuitSet(
            suit_id=suit_id,
            name=suit_info.get("NameHash", "unknown"),
            icon_url=self._resolver.get_item_icon_url(suit_info.get("Icon", "")),
            pieces_equipped=equiped,
            is_active=active,
            active_bonus=active_bonus if active else None
        )
        
    async def _build_weapon(self, weapon_raw: dict) -> WeaponData:
        template_id = weapon_raw.get("templateId", 0)
        if not template_id:
            logger.warning(f"No templateId found in weapon_raw")
        weapon_lvl = weapon_raw.get("weaponLv", 1)
        ref_lvl= weapon_raw.get("refineLv", 0)
        breakthrough_lvl= weapon_raw.get("breakthroughLv", 0)
        gems= weapon_raw.get("attachedGem",{})
        gem_temp_id= gems.get("templateId", 0)
        
        gem = None
        if gem_temp_id:
            try:
                outer_icon= self._resolver.weapon_gem_template.get(str(gem_temp_id), {}).get("Icon", "")
                rarity= outer_icon.split("/")[-1].split(".")[0].split("_")[-1] if outer_icon else 3
                outer_icon_url= self._resolver.get_item_icon_url(outer_icon) 
            except Exception as e:
                logger.warning(f"Failed to determine gem rarity for template_id {gem_temp_id}: {e}")
                rarity=3
                outer_icon_url=""
            
            gem_terms=gems.get("terms", [])
            
            term_name = ""
            inner_icon = ""
            
            if gem_terms:
                term=self._resolver.weapon_gem_term.get(str(gem_terms[-1].get("termNumId", "")), {})
                inner_icon= term.get("TagIcon", "")
                inner_icon= self._resolver.get_item_icon_url(inner_icon)
                term_name_hash= term.get("TagNameHash", "")
                term_name= self._resolver.name_map.get(str(term_name_hash), term_name_hash) if term_name_hash else ""
                    
            total_cost=gems.get("totalCost", 0)
            
            gem= Gem(
                rarity=int(rarity),
                name=term_name ,
                inner_icon_url=inner_icon if inner_icon else "",
                cover_icon_url=outer_icon_url if outer_icon_url else ""
            )
        else:
            logger.warning(f"No attached gem found for weapon with template_id {template_id}")
        
        weapon_info = self._resolver.get_weapon(str(template_id))
        if not weapon_info:
            logger.warning(f"Weapon info not found for template_id: {template_id}")
        skill_ids = weapon_info.get("SkillList", [])
        if not skill_ids:
            logger.warning(f"No SkillList found for weapon {template_id}")
        lvl= weapon_info.get("LevelTemplateId", "")
        if not lvl:
            logger.warning(f"No LevelTemplateId found for weapon {template_id}")
        lvl = self._resolver.weapon_breakthrough.get("LevelCurves", {}).get(str(lvl), {})
        if not lvl:
            logger.warning(f"Level curve not found for weapon {template_id}")
            lvl = [0]
        if weapon_lvl - 1 >= len(lvl):
            logger.warning(f"Weapon level {weapon_lvl} out of range for weapon {template_id}")
            weapon_lvl = len(lvl)
        lvl=lvl[weapon_lvl-1]
        main= MainStat(
            value=int(lvl)
        )
        base_bounds= weapon_info.get("BreakthroughTemplateId", "")
        if not base_bounds:
            logger.warning(f"No BreakthroughTemplateId found for weapon {template_id}")
        base_bounds = self._resolver.weapon_breakthrough.get("BreakSkillLevelBounds", {}).get(str(base_bounds), {})
        if not base_bounds:
            logger.warning(f"BreakSkillLevelBounds not found for weapon {template_id}")
        base_bounds = base_bounds.get(str(breakthrough_lvl), [])
        if not base_bounds:
            logger.warning(f"No base bounds for breakthrough level {breakthrough_lvl} on weapon {template_id}")
        skills = []
        term_type_map = {}
        for term in gem_terms:
            term_id= term.get("termNumId", "")
            cost= term.get("cost", 1)
            term_type= self._resolver.weapon_gem_term.get(str(term_id), {}).get("TermType", "")
            if not term_type:
                logger.warning(f"Term type not found for term_id {term_id} in weapon {template_id}")
                continue
            term_type_map[term_type] = cost
        
        pote_bounds=[]
        if ref_lvl>0:
            pote_bounds= self._resolver.weapon_breakthrough.get("TalentSkillLevelBounds", {}).get(str(weapon_info.get("TalentTemplateId", "")), {}).get(str(ref_lvl),[] )
            if not pote_bounds:
                logger.warning(f"Talent skill level bounds not found for refine level {ref_lvl} on weapon {template_id}")
    
        for i , skill in enumerate(skill_ids):
            skill_info = self._resolver.weapon_skill.get(str(skill), {})
            cost= term_type_map.get(i+1, 0)
            
            if not skill_info:
                logger.warning(f"Weapon skill info not found for skill_id: {skill}")
                continue
            
            pote_lower= pote_bounds[i].get("lowerBound", 0) if pote_bounds else 0
            pote_upper= pote_bounds[i].get("upperBound", 0) if pote_bounds else 0
            
            lower= base_bounds[i].get("lowerBound", 1) + pote_lower
            upper= base_bounds[i].get("upperBound", 9) + pote_upper
            opt= min(int(lower) + cost, int(upper))
            
            s_info= skill_info.get("PropMap", {})
            if len(s_info) == 1:
                skills.append(WeaponSkill(
                    skill_id=str(skill),
                    tag_id=skill_info.get("TagId", ""),
                    prop_id=list(s_info.keys())[0],
                    base_lvl=int(lower) if lower else 1,
                    max_lvl=int(upper),
                    current_lvl=int(opt) if lower else 1,
                    formula=list(s_info.values())[0].get("Formula", "unknown"),
                    prop_name=self._resolver.prop_by_id.get(str(list(s_info.keys())[0]), "unknown"),
                    icon_url=self._resolver.get_attribute_url(list(s_info.keys())[0]),
                    value=list(s_info.values())[0].get("Values", [0])[opt-1]
                ))
            else:
                skills.append(WeaponSkill(
                        skill_id=str(skill),
                        tag_id=skill_info.get("TagId", ""),
                        prop_id=list(s_info.keys()),
                        base_lvl=int(lower) if lower else 1,
                        max_lvl=int(upper),
                        current_lvl=int(opt) if lower else 1,
                        formula=[s.get("Formula", "unknown") for s in s_info.values()],
                        prop_name=[self._resolver.prop_by_id.get(str(k), "unknown") for k in s_info.keys()],
                        icon_url=[self._resolver.get_attribute_url(k) for k in s_info.keys()],
                        value=[round(v.get("Values", [0])[opt-1], 3) for v in s_info.values()]
                    ))
        name_hash=str(weapon_info.get("NameHash"))
        
        return WeaponData(
            weapon_id=str(template_id),
            name=self._resolver.name_map.get(name_hash, name_hash),
            rarity=weapon_info.get("Rarity", 5),
            weapon_type=weapon_info.get("WeaponType", "unknown"),
            level=weapon_lvl,
            refine_lv=ref_lvl,
            breakthrough_lv=breakthrough_lvl,
            base_atk=round(float(lvl), 3),
            skill_levels=[s.current_lvl for s in skills],
            icon_url=self._resolver.get_weapon_icon_url(str(template_id)),
            skills=skills,
            main_stat=main,
            gem=gem
        )
        
    async def _build_skill_meta(self, skill_info: dict , char_temp_id: str) -> SkillMeta:
        char_skill_info = self._resolver.get_character(str(char_temp_id)).get("SkillInfoMap", {})
        n_skill_id = skill_info.get("normalSkill", "")
        u_skill_id = skill_info.get("ultimateSkill", "")
        c_skill_id = skill_info.get("comboSkill", "")
        d_skill_id = skill_info.get("dispNormalAttackSkill", "")
        skills = []
        for skill in skill_info.get("levelInfo", []):
            skill_id= skill.get("skillId", "")
            skill_data = char_skill_info.get(str(skill_id), {})
            if not skill_data:
                logger.warning(f"Skill {skill_id} not found in SkillInfoMap for character {char_temp_id}")
                continue
            skills.append(SkillInfo(
                skill_id=str(skill_id),
                icon_url=self._resolver.get_item_icon_url(skill_data.get("Icon", "")),
                element=skill_data.get("Element", "unknown"),
                level=skill.get("skillLevel", 1),
                max_level=skill.get("skillMaxLevel", 12),
                enhanced_level=skill.get("skillEnhancedLevel", 1),
            ))
        return SkillMeta(
            normal_skill=str(n_skill_id),
            ultimate_skill=str(u_skill_id),
            combo_skill=str(c_skill_id),
            disp_normal_atk_skill=str(d_skill_id),
            skills=skills
        )
            
    async def _build_talent_info(self, talent_info: dict,char_temp_id:str,potential:int = 0) -> TalentInfo:
        char_info = self._resolver.get_character(str(char_temp_id))
        if not char_info:
            logger.warning(f"Character info not found for char_temp_id: {char_temp_id}")
        char_node_skill_map = char_info.get("NodeSkillMap", {})
        if not char_node_skill_map:
            logger.warning(f"No NodeSkillMap found for character {char_temp_id}")
        char_attr_node_map = char_info.get("AttributeNodes", {})
        if not char_attr_node_map:
            logger.warning(f"No AttributeNodes found for character {char_temp_id}")
        
        latest_break_node = talent_info.get("latestBreakNode", "")
        attr_nodes = talent_info.get("attrNodes", [])
        pass_nodes= talent_info.get("latestPassiveSkillNodes", [])
        fact_nodes= talent_info.get("latestFactorySkillNodes", [])
        
        if not char_attr_node_map.values():
            logger.warning(f"No attribute node map values for character {char_temp_id}")
            main_attribute_id = "0"
        else:
            main_attribute=list(char_attr_node_map.values())[0]
            main_attribute_keys = list(main_attribute.keys())
            if not main_attribute_keys:
                logger.warning(f"No keys in main attribute for character {char_temp_id}")
                main_attribute_id = "0"
            else:
                main_attribute_id = main_attribute_keys[0]
        attribute_nodes = AttrNode(
            attri_id=main_attribute_id,
            attri_name=self._resolver.prop_by_id.get(str(main_attribute_id), "unknown"),
            icon_url=self._resolver.get_attribute_url(main_attribute_id),
            values=[],
            total_value=0,
            level=0
        )
        
        for attr in attr_nodes:
            attr_map = char_attr_node_map.get(attr)
            if not attr_map:
                logger.warning(f"Attribute map not found for attr node {attr} in character {char_temp_id}")
                continue
            attr_value = attr_map.get(main_attribute_id, 0)
            attribute_nodes.values.append(attr_value)
            attribute_nodes.total_value += int(attr_value)
            attribute_nodes.level += 1

        passive_nodes = []
        for p_node in pass_nodes:
            node_info = char_node_skill_map.get(str(p_node), {})
            if not node_info:
                logger.warning(f"Passive node info not found for node {p_node} in character {char_temp_id}")
                continue
            passive_nodes.append(TalentPassiveNode(
                node_id=str(p_node),
                icon_url=self._resolver.get_item_icon_url(node_info.get("Icon", "")),
                level=node_info.get("Level", 1),
                index=node_info.get("Index", 0),
                is_max= int(node_info.get("Level", 1)) >= 2,
                type=node_info.get("Type", 4)
            ))
        
        factory_nodes = []
        for f_node in fact_nodes:
            node_info = char_node_skill_map.get(str(f_node), {})
            if not node_info:
                logger.warning(f"Factory node info not found for node {f_node} in character {char_temp_id}")
                continue
            factory_nodes.append(TalentFactoryNode(
                node_id=str(f_node),
                icon_url=self._resolver.get_item_icon_url(node_info.get("Icon", "")),
                level=node_info.get("Level", 1),
                index=node_info.get("Index", 0),
                is_max= int(node_info.get("Level", 1)) >= 2,
                type=node_info.get("Type", 4)
            ))
        potential_attributes = []
        
        if potential > 0:
            for p_attr in char_info.get("PotAttributes", []):
                if potential >= p_attr.get("Level", 0):
                    pot_attri=[]
                    for key , value in p_attr.get("Attrs", {}).items():
                        pot_attri.append(PoteAtrri(
                            attri_id=str(key),
                            attri_name=self._resolver.prop_by_id.get(str(key), "unknown"),
                            icon_url=self._resolver.get_attribute_url(str(key)),
                            value=value.get("Value", 0),
                            is_float= type(value.get("Value", 0)) == float,
                            formula=value.get("Formula", "unknown")
                        ))
                    potential_attributes.append(PotentialAttributes(
                        required_potential_level=p_attr.get("Level", 0),
                        attributes=pot_attri
                    ))
            return TalentInfo(
                latest_break_node=str(latest_break_node),
                attr_nodes=attribute_nodes,
                passive_nodes=passive_nodes,
                factory_nodes=factory_nodes,
                potential_attributes=potential_attributes
            )
        return TalentInfo(
            latest_break_node=str(latest_break_node),
            attr_nodes=attribute_nodes,
            passive_nodes=passive_nodes,
            factory_nodes=factory_nodes
        )
        
    async def _build_character_data(self, char_data: dict) -> CharacterData:
        char_id = char_data.get("templateId", 0)
        if not char_id:
            logger.warning(f"No templateId found in char_data")
        char_info = self._resolver.get_character(str(char_id))
        if not char_info:
            logger.warning(f"Character info not found for char_id: {char_id}")
        char_full= self._resolver.character_full.get(str(char_id), {})
        if not char_full:
            logger.warning(f"Character full data not found for char_id: {char_id}")
        pote= char_data.get("potentialLevel", 0)
        
        str_id= char_info.get("StrId", "unknown")
        name= char_info.get("NameHash", "unknown")
        name= self._resolver.name_map.get(str(name), name)
        element= char_info.get("Element", "unknown")
        profession= char_info.get("Profession", "unknown")
        rarity= char_info.get("Rarity", 6)
        weapon_type= char_info.get("WeaponType", "unknown")
        lvl= char_data.get("level", 1)

        main_attribute=str(char_info.get("MainAttrId", "1"))
        main_attribute=CharAttr(
            attri_id=main_attribute,
            attri_name=self._resolver.prop_by_id.get(str(main_attribute), "unknown"),
            url=self._resolver.get_attribute_url(main_attribute)
        )
        
        base_atk_list = char_full.get("BaseAtkByLevel", [])
        if not base_atk_list or lvl - 1 >= len(base_atk_list):
            logger.warning(f"BaseAtkByLevel not found or level {lvl} out of range for character {char_id}")
            base_atk_value = 0
        else:
            base_atk_value = base_atk_list[lvl-1]
        base_atk= BaseAttr(
            attri_id="2",
            attri_name="Atk_base",
            url=self._resolver.get_attribute_url("2"),
            value= base_atk_value,
            is_float=False
        )
        
        base_hp_list = char_full.get("BaseHpByLevel", [])
        if not base_hp_list or lvl - 1 >= len(base_hp_list):
            logger.warning(f"BaseHpByLevel not found or level {lvl} out of range for character {char_id}")
            base_hp_value = 0
        else:
            base_hp_value = base_hp_list[lvl-1]
        base_hp= BaseAttr(
            attri_id="1",
            attri_name="MaxHp_base",
            url=self._resolver.get_attribute_url("1"),
            value= base_hp_value,
            is_float=False
        )
        
        base_attributes= []
        for key, value in char_full.get("BaseAttributes", {}).items():
            if not value:
                logger.warning(f"Missing base attribute value for attr key {key} in character {char_id}")
                continue
            base_attributes.append(BaseAttr(
                attri_id=str(key),
                attri_name=self._resolver.prop_by_id.get(str(key), "unknown"),
                url=self._resolver.get_attribute_url(str(key)),
                value=value.get("BaseValue", 0) + (value.get("AddValue", 0) * lvl-1),
                is_float= type(value.get("BaseValue", 0) + (value.get("AddValue", 0) * lvl-1)) == float
            ))
        
        sub_attribute=str(char_info.get("SubAttrId", "0"))
        sub_attribute=CharAttr(
            attri_id=sub_attribute,
            attri_name=self._resolver.prop_by_id.get(str(sub_attribute), "unknown"),
            url=self._resolver.get_attribute_url(sub_attribute)
        )
        
        splash_url= self._resolver.get_splash_url(str_id)
        round_icon_url= self._resolver.get_round_icon_url(str_id)
        bg_url= self._resolver.get_bg_url(str_id)
        
        equip_raw= char_data.get("equip", [])
        weapon_raw= char_data.get("weapon", {})
        skill_info_raw= char_data.get("skillInfo", {})
        talent_info_raw= char_data.get("talent", {})
        
        eq_tasks = [self._build_equip(equip) for equip in equip_raw]
        equips = await asyncio.gather(*eq_tasks)
        
        counts= Counter(equip.suit_id for equip in equips)
        active_suit_id= {k: v for k, v in counts.items() if v >= 3}
        if active_suit_id:
            active_suit_id= list(active_suit_id.keys())[0]
            equiped_count= counts[active_suit_id]
            suit_set= await self._build_suit_set(active_suit_id, active=True,equiped=equiped_count)
        else:
            if equips:
                logger.warning(f"No complete suit set found for character {char_id}")
            suit_set= None
        
        tasks= []
        tasks.append(self._build_weapon(weapon_raw))
        tasks.append(self._build_skill_meta(skill_info_raw, str(char_id)))
        tasks.append(self._build_talent_info(potential=pote,talent_info=talent_info_raw,char_temp_id=str(char_id)))
        weapon, skill_meta, talent_info = await asyncio.gather(*tasks)

        c_data=CharacterData(
            template_id=char_id,
            str_id=str_id,
            name=name,
            rarity=rarity,
            main_attribute=main_attribute,
            sub_attribute=sub_attribute,
            base_atk=base_atk,
            base_hp=base_hp,
            base_attribute=base_attributes,
            element=element,
            weapon_type=weapon_type,
            level=lvl,
            potential_level=char_data.get("potentialLevel", 0),
            profession=profession,
            splash_url=splash_url,
            round_icon_url=round_icon_url,
            bg_url=bg_url,
            weapon=weapon,
            equips=equips,
            suit_sets=suit_set,
            skills=skill_meta,
            talents=talent_info
        )
        stats= compute_final_stats(c_data)
        c_data.stats= stats
        return c_data
    

            