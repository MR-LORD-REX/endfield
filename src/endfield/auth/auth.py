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

ANDROID_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 16; 2107113SI Build/BP2A.250805.005; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
    "Chrome/149.0.7827.91 Mobile Safari/537.36; SKPort/1.3.1"
)

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
        "MONUMENT_URL": "https://zonai.skport.com/api/v1/game/endfield/card/indie-hard"
    },
    "global": {
        "name": "Global Server",
        "APP_CODE": "6eb76d4e13aa36e6",
        "GRANT_URL": "https://as.gryphline.com/user/oauth2/v2/grant",
        "CRED_URL": "https://zonai.skport.com/web/v1/user/auth/generate_cred_by_code",
        "BIND_URL": "https://zonai.skport.com/api/v1/game/player/binding",
        "SIGN_URL": "https://zonai.skport.com/web/v1/game/endfield/attendance",
        "MONUMENT_URL": "https://zonai.skport.com/api/v1/game/endfield/card/indie-hard"
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
            return user
        else:
            print(f"  Failed: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None
    



    
    