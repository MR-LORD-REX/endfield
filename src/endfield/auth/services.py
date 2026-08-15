from urllib import parse
import aiohttp
from typing import Any


from .auth import (
    login, get_endfield_roles, generate_sign, random_delay, VNAME, PLATFORM ,
    SIGN_DELAY_MIN, SIGN_DELAY_MAX, get_random_headers , ANDROID_USER_AGENT
)


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
    
async def get_monument_data(
    session: aiohttp.ClientSession,
    cred: str,
    sign_token: str,
    uid: int,
    skport_id: int,
    server_id: int = 2
) -> dict | None:
    """Fetch monument data for a user."""
    try:
        path = "/api/v1/game/endfield/card/indie-hard"
        params = {
            "roleId": str(uid),
            "serverId": str(server_id),
            "userId": str(skport_id),
        }
        query = parse.urlencode(params)
        request_url = f"https://zonai.skport.com{path}?{query}"
        sign, sign_header = generate_sign(sign_token, path, query)
        
        headers = {
            "cred": cred,
            "sk-language": "en",
            "timestamp": sign_header["timestamp"],
            "sign": sign,
            "vname": VNAME,
            "sec-ch-ua-platform": '"Android"',
            "sec-ch-ua": (
                '"Android WebView";v="149", "Chromium";v="149", '
                '"Not)A;Brand";v="24"'
            ),
            "sec-ch-ua-mobile": "?1",
            "user-agent": ANDROID_USER_AGENT,
            "content-type": "application/json",
            "platform": PLATFORM,
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://game.skport.com",
            "x-requested-with": "com.gryphline.skport",
            "referer": "https://game.skport.com/",
        }
        
        async with session.get(request_url, headers=headers) as response:
            data = await response.json(content_type=None)
            if data.get("code") == 0:
                return data.get("data")
            else:
                print(f"Failed to fetch monument data: {data.get('message', 'Unknown error')}")
                return None
    except Exception as e:
        print(f"Error fetching monument data: {str(e)}")
        return None
    
async def get_all(
    session: aiohttp.ClientSession,
    cred: str,
    sign_token: str,
    uid: int,
    skport_id: int,
    server_id: int = 2
)-> dict[str, Any] | None:
    """Fetch all data """
    try: 
        path="/api/v1/game/endfield/card/detail"
        params={
            "roleId": str(uid),
            "serverId": str(server_id),
            "userId": str(skport_id),
        }
        query=parse.urlencode(params)
        request_url=f"https://zonai.skport.com{path}?{query}"
        sign,sign_header=generate_sign(sign_token,path,query)
        headers = {
            "cred": cred,
            "sk-language": "en",
            "timestamp": sign_header["timestamp"],
            "sign": sign,
            "vname": VNAME,
            "sec-ch-ua-platform": '"Android"',
            "sec-ch-ua": (
                '"Android WebView";v="149", "Chromium";v="149", '
                '"Not)A;Brand";v="24"'
            ),
            "sec-ch-ua-mobile": "?1",
            "user-agent": ANDROID_USER_AGENT,
            "content-type": "application/json",
            "platform": PLATFORM,
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://game.skport.com",
            "x-requested-with": "com.gryphline.skport",
            "referer": "https://game.skport.com/",
        }
        async with session.get(request_url, headers=headers) as response:
            data = await response.json(content_type=None)
            if data.get("code") == 0:
                return data.get("data")
            else:
                print(f"Failed to fetch all data: {data.get('message', 'Unknown error')}")
                return None
    except Exception as e:
        print(f"Error fetching all data: {str(e)}")
        return None
    
async def get_char(
    session: aiohttp.ClientSession,
    cred: str,
    sign_token: str,
    uid: int,
    skport_id: int,
    server_id: int = 2,
    operator_id: str = "0",
    char_id: str = "0"
)-> dict[str, Any] | None:
    """Fetch character data """
    try: 
        path="/api/v1/game/endfield/card/char"
        params={
            "roleId": str(uid),
            "serverId": str(server_id),
            "userId": str(skport_id),
            "operatorId": operator_id,
            "charId": char_id
        }
        query=parse.urlencode(params)
        request_url=f"https://zonai.skport.com{path}?{query}"
        sign,sign_header=generate_sign(sign_token,path,query)
        headers = {
            "cred": cred,
            "sk-language": "en",
            "timestamp": sign_header["timestamp"],
            "sign": sign,
            "vname": VNAME,
            "sec-ch-ua-platform": '"Android"',
            "sec-ch-ua": (
                '"Android WebView";v="149", "Chromium";v="149", '
                '"Not)A;Brand";v="24"'
            ),
            "sec-ch-ua-mobile": "?1",
            "user-agent": ANDROID_USER_AGENT,
            "content-type": "application/json",
            "platform": PLATFORM,
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://game.skport.com",
            "x-requested-with": "com.gryphline.skport",
            "referer": "https://game.skport.com/",
        }
        async with session.get(request_url, headers=headers) as response:
            data = await response.json(content_type=None)
            if data.get("code") == 0:
                return data.get("data").get("detail")
            else:
                print(f"Failed to fetch character data: {data.get('message', 'Unknown error')}")
                return None
    except Exception as e:
        print(f"Error fetching character data: {str(e)}")
        return None