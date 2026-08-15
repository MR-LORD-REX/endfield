from src.endfield import Endfield
from src.endfield.proxy_pool import ProxyPool
import asyncio
import time


uid = 4572346170
token = ""

p = []


async def main():
    proxies = ProxyPool(proxies=p)

    async with Endfield(debug=True, proxy_pool=proxies) as ef:
        data = await ef.get_showcase(uid)
        print(data.profile.name)
        for char in data.characters:
            print(char.name)
            for stat in char.stats:
                print(f"  {stat[0]}: {stat[1]}")
            print("\n\n")
        with open("data.json", "w", encoding="utf-8") as f:
            f.write(data.model_dump_json(indent=2))

    async with Endfield(debug=True, proxy_pool=proxies) as ef:
        t1=time.time()
        char = await ef.get_all_characters(token)
        t2=time.time()
        print(f"Fetched {len(char.characters)} characters in {t2-t1:.2f} seconds.")
        t=[]
        for c in char.characters:
            t.append(ef.get_game_character(token, c.char_id))
        data= await asyncio.gather(*t)
        t3=time.time()
        print(f"Fetched detailed data for {len(data)} characters in {t3-t2:.2f} seconds.")
        for d in data:
            with open(f"test/{d.name}.json", "w", encoding="utf-8") as f:
                f.write(d.model_dump_json(indent=2))
            
        monument_data = await ef.get_monument(token)
        if monument_data:
            print(monument_data.model_dump_json(indent=2))
            with open("monument.json", "w", encoding="utf-8") as f:
                f.write(monument_data.model_dump_json(indent=2))
                
        stats = await ef.get_game_stats(token, server=3)
        if stats:
            print(stats.sanity_point.model_dump_json(indent=2))
            print(stats.battle_pass.model_dump_json(indent=2))
            print(stats.daily_points.model_dump_json(indent=2))
            print(stats.weekly_points.model_dump_json(indent=2))
            with open("stats.json", "w", encoding="utf-8") as f:
                f.write(stats.model_dump_json(indent=2))
        else:
            print("Failed to fetch game stats.")
            with open("stats.json", "w", encoding="utf-8") as f:
                f.write("{}")

    async with Endfield() as ef:
        blueprints = await ef.get_factory_blueprints(
            region="Asia",
            item="xiranite",
            start=0,
            end=10,
        )
        print(blueprints.model_dump_json(indent=2))
        with open("blueprints.json", "w", encoding="utf-8") as f:
            f.write(blueprints.model_dump_json(indent=2))

    await proxies.close()


if __name__ == "__main__":
    asyncio.run(main())