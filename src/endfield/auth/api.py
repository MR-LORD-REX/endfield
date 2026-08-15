from typing import List
import aiohttp
import asyncio
import logging
from datetime import datetime, timezone

from ..models.auth.game_stats import (
    GameStats , Regions , Region , 
    Settlement , FactoryMoney , WeeklyPoints , 
    DailyPoints , BattlePass , SanityPoint
)
from ..models.auth.user import User
from ..models.auth.indie_hard import IndieHardData
from ..data_cache import CacheManager
from ..models.auth.allc import AllCharacters , Character

logger = logging.getLogger(__name__)

from .auth import ( get_skport_roles ,login , SERVER_CONFIG , 
    get_skport_user , generate_sign , get_endfield_roles 
)
from .services import ( get_game_stats, 
    do_daily_sign , get_monument_data , get_all , get_char)

cfg=SERVER_CONFIG["global"]

element_map = {
    "Electric":"Pulse",
    "Physical":"Physical",
    "Cryo": "Cryst",
    "Nature": "Natural",
    "Heat":"Fire",
}

proffesion_map = {
    "Defender":"DEFENDER",
    "Striker": "ASSAULT",
    "Guard":  "GUARD" ,
    "Caster": "CASTER",
    "Vanguard" : "VANGUARD",
    "Supporter": "SUPPORTER"
}

class GameApi:
    def __init__(self):
        self.user_cache = CacheManager[User]()
        
    async def verify_user(
        self,
        token: str,
        session: aiohttp.ClientSession,
        server: int = 3
    )-> User | None:
        """Verify the user and return a User object if valid, otherwise None."""
        try:
            cred, sign_token = await login(session, token, cfg)
            roles_task = get_endfield_roles(session, cred, sign_token, cfg)
            user_task = get_skport_user(session, cred, sign_token)
            roles, user = await asyncio.gather(roles_task, user_task)
            
            roles = roles["defaultRole"] or roles["roles"][0]
            role_id = int(roles["roleId"])
            server_id = int(roles["serverId"])
            sk_game_role = f"{server}_{role_id}_{server_id}"
            user_id = int(user["userId"])
            name = user.get("nickname", "Unknown")
            
            return User(
                uid=role_id,
                skport_id=user_id,
                skport_name=name,
                server_id=server_id,
                cred=cred,
                sign_token=sign_token,
                sk_role=sk_game_role
            )
        except Exception as e:
            logger.error(f"Error verifying user: {e}")
            return None
        
    async def game_stats(
        self,
        session: aiohttp.ClientSession,
        token: str,
        server: int=3
    ) -> GameStats | None:

        user = self.user_cache.get(token)
        if not user:
            user = await self.verify_user(token, session, server)
            if not user:
                return None
            self.user_cache.set(token, user, ttl=300)  # Cache for 5 minutes
        
        cred , sign , role = user.cred , user.sign_token , user.sk_role
        
        stats = await get_game_stats(session, cred,sign,role)
        if not stats:
            return None
        sanity_point = SanityPoint(
            current=int(stats["dungeon"]["curStamina"]),
            max=int(stats["dungeon"]["maxStamina"]),
            full_recover_at=datetime.fromtimestamp(int(stats["dungeon"]["maxTs"]), tz=timezone.utc) if stats["dungeon"].get("maxTs") else None
        )
        battle_pass = BattlePass(
            max_level=int(stats["bpSystem"]["maxLevel"]),
            current_level=int(stats["bpSystem"]["curLevel"])
        )
        daily_points = DailyPoints(
            current=int(stats["dailyMission"]["dailyActivation"]),
            max=int(stats["dailyMission"]["maxDailyActivation"])
        )
        weekly_points = WeeklyPoints(
            score=int(stats["weeklyMission"]["score"]),
            total=int(stats["weeklyMission"]["total"])
        )
        regions = []
        for domain in stats["domain"]:
            settlements = []
            for settlement in domain["settlements"]:
                settlements.append(Settlement(
                    id=settlement["id"],
                    name=settlement["name"],
                    level=int(settlement["level"]),
                    exp_to_level_up=int(settlement["expToLevelUp"]),
                    current_exp=int(settlement["exp"]),
                    max_money=int(settlement["moneyMax"]),
                    remaining_money=int(settlement["remainMoney"]),
                    char_icon=settlement.get("officerCharAvatar") or None,
                    last_ticked=datetime.fromtimestamp(int(settlement["lastTickTime"])) if settlement.get("lastTickTime") else None
                ))
            regions.append(Region(
                region_id=domain["domainId"],
                region_name=domain["name"],
                factory_level=int(domain["level"]),
                factory_money=FactoryMoney(
                    current=int(domain["moneyMgr"]["count"]),
                    max=int(domain["moneyMgr"]["total"])
                ),
                settlements=settlements
            ))
        game_stats = GameStats(
            regions=Regions(all=regions),
            sanity_point=sanity_point,
            battle_pass=battle_pass,
            daily_points=daily_points,
            weekly_points=weekly_points
        )
        return game_stats

    async def perform_daily_sign(
        self,
        session: aiohttp.ClientSession, 
        token: str) -> str:

        msg=await do_daily_sign(session, token, cfg)
        return msg

    async def get_monument(
        self,
        session: aiohttp.ClientSession,
        token: str
    ) -> IndieHardData | None:
        
        user = self.user_cache.get(token)
        if not user:
            user = await self.verify_user(token, session)
            if not user:
                return None
            self.user_cache.set(token, user, ttl=300)  # Cache for 5 minutes
        if not user:
            raise RuntimeError("Could not resolve the authenticated Skport user")
        monument_data = await get_monument_data(
            session,
            cred=user.cred,
            sign_token=user.sign_token,
            uid=user.uid,
            skport_id=user.skport_id,
            server_id=user.server_id
        )
        
        return IndieHardData.model_validate(monument_data)
    
    async def get_all_characters(
        self,
        session: aiohttp.ClientSession,
        token: str
    ) -> AllCharacters | None:
        user = self.user_cache.get(token)
        if not user:
            user = await self.verify_user(token, session)
            if not user:
                return None
            self.user_cache.set(token, user, ttl=300)  # Cache for 5 minutes
        if not user:
            raise RuntimeError("Could not resolve the authenticated Skport user")
        try:
            all_data = await get_all(
                session,
                cred=user.cred,
                sign_token=user.sign_token,
                uid=user.uid,
                skport_id=user.skport_id,
                server_id=user.server_id
            )
            characters= all_data.get("detail", {}).get("chars", [])
            allc=[]
            for char in characters:
                cd=char.get("charData", {})
                allc.append(Character(
                    char_id=char.get("id"),
                    name=cd.get("name", "Unknown"),
                    level=int(char.get("level", 0)),
                    owned_at=int(char.get("ownTs", 0)),
                    square_icon=cd.get("avatarSqUrl", ""),
                    rect_icon=cd.get("avatarRtUrl", ""),
                    splash_icon=cd.get("illustrationUrl", ""),
                    proffesion=proffesion_map.get(cd.get("profession",{}).get("value", "Unknown"), "Unknown"),
                    element=element_map.get(cd.get("property",{}).get("value", "Unknown"), "Unknown"),
                    rarity=int(cd.get("rarity", {}).get("value", 0)),
                    potential_level=int(char.get("potentialLevel", 0)),
                    evolve_phase=int(char.get("evolvePhase", 0))
                ))
            return AllCharacters(characters=allc, total=len(allc))
        except Exception as e:
            logger.error(f"Error fetching all characters: {e}")
            return None
        
    async def get_char(
        self,
        session: aiohttp.ClientSession,
        token: str,
        char_id: str
    )-> dict | None:
        user = self.user_cache.get(token)
        if not user:
            user = await self.verify_user(token, session)
            if not user:
                return None
            self.user_cache.set(token, user, ttl=300)  # Cache for 5 minutes
        if not user:
            raise RuntimeError("Could not resolve the authenticated Skport user")
        
        char_data = await get_char(
            session,
            cred=user.cred,
            sign_token=user.sign_token,
            uid=user.uid,
            skport_id=user.skport_id,
            server_id=user.server_id,
            char_id=char_id,
            operator_id=char_id
        )
        return char_data