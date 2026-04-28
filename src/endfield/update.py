import aiohttp
from pathlib import Path
import os
import json

BASE_URL = "https://raw.githubusercontent.com/MR-LORD-REX/endfield/main/src/endfield/assets/"
assets_path = Path(__file__).parent / "assets"

async def check_update():
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL + "version.json") as response:
            if response.status == 200:
                data = await response.read()
                data = json.loads(data)
                with open(assets_path / "version.json", "r") as f:
                    local_data = json.load(f)
                if data["version"] != local_data["version"]:
                    print(f"New version available: {data['version']}. You are using version: {local_data['version']}")
                    return True
                elif data["version"] == local_data["version"]:
                    print(f"You are using the latest version: {data['version']}")
                    return False
            else:
                print("Failed to check for updates. Status code: " + str(response.status))
                return False
            
async def download_update():
    files=os.listdir(assets_path)
    async with aiohttp.ClientSession() as session:
        for file in files:
            print("Downloading " + file + "...")
            async with session.get(BASE_URL + file) as response:
                if response.status == 200:
                    content = await response.read()
                    content = json.loads(content) 
                    with open(assets_path / file, "w") as f:
                        json.dump(content, f, indent=4)
                else:
                    print("Failed to download " + file + ". Status code: " + str(response.status))
                    continue
    print("Update downloaded successfully.")