import asyncio
import hashlib
import hmac
import json
import os
import random
import time
from urllib import parse
import logging

import aiohttp

logger = logging.getLogger(__name__)

REQUEST_DELAY_MIN = 2
REQUEST_DELAY_MAX = 4
ACCOUNT_DELAY_MIN = 8
ACCOUNT_DELAY_MAX = 15
SIGN_DELAY_MIN = 2
SIGN_DELAY_MAX = 5

USER_AGENTS = [
    'Skland/1.0.0 (com.skland.grass; Android; SDK_INT 33; Build/TQ3A.230901.001)',
    'Skland/1.0.0 (com.skland.grass; Android; SDK_INT 34; Build/UP1A.231005.004)',
    'Skland/1.0.0 (com.skland.grass; Android; SDK_INT 35; Build/AP2A.240405.002)',
    'Skland/1.0.1 (skport; Android; SDK_INT 33; Build/TQ3A.230901.001)',
    'Skland/1.0.1 (skport; Android; SDK_INT 34; Build/UP1A.231005.004)',
]

PLATFORM = '3'
VNAME = '1.0.0'

SERVER_CONFIG = {
    "cn": {
        "name": "China Server",
        "APP_CODE": "4ca99fa6b56cc2ba",
        "GRANT_URL": "https://as.hypergryph.com/user/oauth2/v2/grant",
        "CRED_URL": "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code",
        "BIND_URL": "https://zonai.skland.com/api/v1/game/player/binding",
        "SIGN_URL": "https://zonai.skland.com/api/v1/game/endfield/attendance",
    },
    "global": {
        "name": "Global Server",
        "APP_CODE": "6eb76d4e13aa36e6",
        "GRANT_URL": "https://as.gryphline.com/user/oauth2/v2/grant",
        "CRED_URL": "https://zonai.skport.com/web/v1/user/auth/generate_cred_by_code",
        "BIND_URL": "https://zonai.skport.com/api/v1/game/player/binding",
        "SIGN_URL": "https://zonai.skport.com/web/v1/game/endfield/attendance",
    }
}

def get_random_headers() -> dict:
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Encoding': 'gzip',
        'Connection': 'keep-alive',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
async def random_delay(min_sec: float = REQUEST_DELAY_MIN, max_sec: float = REQUEST_DELAY_MAX):
    await asyncio.sleep(random.uniform(min_sec, max_sec))
    
def generate_sign(token: str, path: str, body: str) -> tuple[str, dict]:
    t = str(int(time.time()))
    sign_header = {
        "platform": PLATFORM,
        "timestamp": t,
        "dId": "",
        "vName": VNAME
    }
    sign_header_str = json.dumps(sign_header, separators=(',', ':'))
    sign_str = path + body + t + sign_header_str
    hmac_hex = hmac.new(
        token.encode('utf-8'),
        sign_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    md5_sign = hashlib.md5(hmac_hex.encode('utf-8')).hexdigest()
    return md5_sign, sign_header

async def get_grant_code(session: aiohttp.ClientSession, token: str, cfg: dict) -> str:
    await random_delay(1, 3)
    try:
        t = json.loads(token)
        token = t['data']['content']
    except (json.JSONDecodeError, KeyError):
        pass

    async with session.post(
        cfg["GRANT_URL"],
        json={'appCode': cfg["APP_CODE"], 'token': token, 'type': 0},
        headers=get_random_headers()
    ) as resp:
        data = await resp.json(content_type=None)

    if data.get('status') != 0:
        raise Exception(f"Failed to get grant code: {data.get('msg', data.get('message'))}")
    return data['data']['code']

async def get_cred(session: aiohttp.ClientSession, grant_code: str, cfg: dict) -> tuple[str, str]:
    """Returns (cred, sign_token)"""
    await random_delay(1, 3)
    async with session.post(
        cfg["CRED_URL"],
        json={'code': grant_code, 'kind': 1},
        headers=get_random_headers()
    ) as resp:
        data = await resp.json(content_type=None)

    if data['code'] != 0:
        raise Exception(f"Failed to get cred: {data['message']}")
    return data['data']['cred'], data['data']['token']

async def login(session: aiohttp.ClientSession, token: str, cfg: dict) -> tuple[str, str]:
    """Returns (cred, sign_token)"""
    try:
        grant = await get_grant_code(session, token, cfg)
        cred, sign_token = await get_cred(session, grant, cfg)
        return cred, sign_token
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise

async def get_endfield_roles(
    session: aiohttp.ClientSession,
    cred: str,
    sign_token: str,
    cfg: dict
) -> dict:
    """Returns the first bound Endfield role, or raises an exception if none found."""
    await random_delay(2, 5)
    parsed = parse.urlparse(cfg["BIND_URL"])
    sign, sign_header = generate_sign(sign_token, parsed.path, '')

    headers = {
        **get_random_headers(),
        'cred': cred,
        'platform': PLATFORM,
        'vName': VNAME,
        'timestamp': sign_header['timestamp'],
        'sign': sign,
        'Content-Type': 'application/json',
    }
    
    async with session.get(cfg["BIND_URL"], headers=headers) as resp:
        data = await resp.json(content_type=None)

    if data['code'] != 0:
        raise Exception(f"Failed to get roles: {data['message']}")

    for app in data['data']['list']:
        if app.get('appCode') == 'endfield' and app.get('bindingList'):
            return app['bindingList'][0]

    raise Exception('No Endfield role bound')

async def get_skport_roles(
    session: aiohttp.ClientSession,
    cred: str,
    sign_token: str,
    cfg: dict,
    server: int = 3
    ) -> str:
    roles=await get_endfield_roles(session, cred, sign_token, cfg)
    role = roles.get('defaultRole') or (roles.get('roles') and roles['roles'][0])
    sk_game_role = f"{server}_{role['roleId']}_{role['serverId']}"
    return sk_game_role
    

async def get_skport_user(
    session: aiohttp.ClientSession,
    cred: str,
    sign_token: str
) -> dict | None:
    
    await random_delay(1, 3)
    path = "/web/v1/wiki/me"
    sign, sign_header = generate_sign(sign_token, path, '')

    headers = {
        'cred': cred,
        'timestamp': sign_header['timestamp'],
        'vname': VNAME,
        'sign': sign,
        'sk-language': 'en',
        'platform': PLATFORM,
        'accept': '*/*',
        'content-type': 'application/json',
        'User-Agent': random.choice(USER_AGENTS),
    }

    try:
        async with session.get(
            "https://zonai.skport.com/web/v1/wiki/me",
            headers=headers
        ) as resp:
            data = await resp.json(content_type=None)

        if data.get('code') == 0 and data.get('data', {}).get('user'):
            user = data['data']['user']
            print(f"    Success!")
            print(f"   - Nickname : {user.get('nickname', 'N/A')}")
            print(f"   - User ID  : {user.get('userId', 'N/A')}")
            return user
        else:
            print(f"  Failed: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None
    
async def get_game_stats(
    session: aiohttp.ClientSession,
    cred: str,
    sign_token: str,
    sk_game_role: str
) -> dict | None:
    
    path = "/api/v1/game/endfield/card/detail"
    sign, sign_header = generate_sign(sign_token, path, '')

    headers = {
        'cred': cred,
        'timestamp': sign_header['timestamp'],
        'vname': VNAME,
        'sign': sign,
        'sk-language': 'en',
        'sk-game-role': sk_game_role,
        'platform': PLATFORM,
        'accept': '*/*',
        'content-type': 'application/json',
        'User-Agent': 'Skport/0.7.0 (com.gryphline.skport; build:700089; Android 33;) Okhttp/5.1.0',
    }

    try:
        async with session.get(
            "https://zonai.skport.com/api/v1/game/endfield/card/detail",
            headers=headers
        ) as resp:
            data = await resp.json(content_type=None)

        if data.get('code') == 0 and data.get('data', {}).get('detail'):
            detail = data['data']['detail']
            return detail
        else:
            print(f"   Failed: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None

async def get_user_game_data(
    session: aiohttp.ClientSession,
    cred: str,
    sign_token: str,
    sk_game_role: str
) -> dict | None:

    await random_delay(1, 3)
    path = "/web/v1/game/endfield/team/user-game-data"
    sign, sign_header = generate_sign(sign_token, path, '')

    headers = {
        'cred': cred,
        'timestamp': sign_header['timestamp'],
        'vname': VNAME,
        'sign': sign,
        'sk-language': 'en',
        'sk-game-role': sk_game_role,
        'platform': PLATFORM,
        'accept': '*/*',
        'content-type': 'application/json',
        'Referer': 'https://game.skport.com/',
        'Origin': 'https://game.skport.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    }

    try:
        async with session.get(
            "https://zonai.skport.com/web/v1/game/endfield/team/user-game-data",
            headers=headers
        ) as resp:
            data = await resp.json(content_type=None)

        if data.get('code') == 0:
            user_game = data.get('data', {}).get('userGameData', {})
            if user_game:
                print(f"   - User Characters  : {len(user_game.get('userChars', {}))}")
                print(f"   - User Weapons     : {len(user_game.get('userWeapons', {}))}")
                print(f"   - User Equipments  : {len(user_game.get('userEquipments', {}))}")
            return data.get('data')
        else:
            print(f"  Failed: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None
    
async def do_daily_sign(
    session: aiohttp.ClientSession,
    token: str,
    cfg: dict
) -> str:
    """Full sign-in flow for one account. Returns result message."""
    try:
        cred, sign_token = await login(session, token, cfg)
        roles = await get_endfield_roles(session, cred, sign_token, cfg)

        role = roles.get('defaultRole') or (roles.get('roles') and roles['roles'][0])
        role_str = f"3_{role['roleId']}_{role['serverId']}"
        role_name = roles.get('defaultRole', {}).get('nickname', 'Unknown Role')
        channel = roles.get('defaultRole', {}).get('serverName', 'Unknown Server')

        await random_delay(SIGN_DELAY_MIN, SIGN_DELAY_MAX)

        parsed = parse.urlparse(cfg["SIGN_URL"])
        sign, sign_header = generate_sign(sign_token, parsed.path, '')

        headers = {
            'cred': cred,
            'platform': PLATFORM,
            'vName': VNAME,
            'timestamp': sign_header['timestamp'],
            'sign': sign,
            'sk-game-role': role_str,
            'Content-Type': 'application/json',
        }

        async with session.post(cfg["SIGN_URL"], headers=headers, json=None) as resp:
            data = await resp.json(content_type=None)

        if data['code'] == 0:
            award_ids = data['data'].get('awardIds', [])
            resource_map = data['data'].get('resourceInfoMap', {})
            award_text = [
                f"{resource_map[a['id']]['name']}x{resource_map[a['id']].get('count', 1)}"
                for a in award_ids
                if a.get('id') in resource_map
            ]
            rewards = "、".join(award_text) if award_text else "no reward info"
            return f"{role_name}({channel}) - Sign-in successful! Rewards: {rewards}"
        else:
            error_msg = data.get("message", "Unknown error")
            if "请勿重复签到" in error_msg or "Please do not sign in again!" in error_msg:
                return f" {role_name}({channel}) - Already signed in today"
            return f"{role_name}({channel}) - Sign-in failed: {error_msg}"

    except Exception as e:
        return f"[Account Failed: {str(e)}"
    
    