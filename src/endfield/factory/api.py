base="https://rmjxwmsbfgvgjpoqvosg.supabase.co/rest/v1/factory_plans?apikey={key}"

import aiohttp
from pathlib import Path
import json
from datetime import datetime , timedelta , timezone

asset_path=Path(__file__).parent.parent/"assets"

def check_last():
    meta_path=asset_path/"fact_meta.json"
    if not meta_path.exists():
        return False
    with open(meta_path,"r",encoding="utf-8") as f:
        meta_data=json.load(f)
    last_updated=meta_data.get("last_updated",0)
    if datetime.now(timezone.utc).timestamp() - last_updated > 60*60*24*2: # 2 days
        return False
    return True

def get_token():
    meta_path=asset_path/"fact_meta.json"
    if not meta_path.exists():
        return None
    with open(meta_path,"r",encoding="utf-8") as f:
        meta_data=json.load(f)
    return meta_data.get("id",None)

async def get_or_update_blueprints()-> dict:
    path=asset_path/"blueprints.json"
    meta_path=asset_path/"fact_meta.json"
    if not path.exists():
        if not check_last():
            token=get_token()
            if token:
                async with aiohttp.ClientSession() as session:
                    url=base.format(key=token)
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data=await resp.json()
                            with open(path,"w",encoding="utf-8") as f:
                                json.dump(data,f,ensure_ascii=False,indent=2)
                            with open(meta_path,"w",encoding="utf-8") as f:
                                json.dump({"last_updated":datetime.now(timezone.utc).timestamp(),"id":token},f,ensure_ascii=False,indent=2)
                            return data
                        else:
                            print(f"Failed to fetch blueprints: {resp.status}")
                            raise Exception("Failed to fetch blueprints")
            else:
                print("No valid token found for fetching blueprints.")
                raise Exception("No valid token")
    else:
        with open(path,"r",encoding="utf-8") as f:
            return json.load(f)