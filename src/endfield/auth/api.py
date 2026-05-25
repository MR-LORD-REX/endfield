from typing import List
import aiohttp
import logging
from datetime import datetime, timezone

from ..models.auth.game_stats import (
    GameStats , Regions , Region , 
    Settlement , FactoryMoney , WeeklyPoints , 
    DailyPoints , BattlePass , SanityPoint
)

logger = logging.getLogger(__name__)

from .auth import (do_daily_sign , 
get_skport_roles , get_game_stats,
login , SERVER_CONFIG)

cfg=SERVER_CONFIG["global"]

async def perform_daily_sign(
    session: aiohttp.ClientSession, 
    token: str) -> str:
    
    msg=await do_daily_sign(session, token, cfg)
    return msg

async def game_stats(
    session: aiohttp.ClientSession,
    token: str,
    server: int=3
) -> GameStats | None:
    
    # all time is in js timestamp in sec , convert to datetime in pydantic model
    
    cred,sign=await login(session,token,cfg)
    if not cred:
        return None
    role=await get_skport_roles(session,cred,sign,cfg,server)
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
