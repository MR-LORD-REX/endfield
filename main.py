from src.endfield import Endfield
from src.endfield.proxy_pool import ProxyPool
import asyncio

# uid=6452216126
uid=6580184840
token=""

p=[
  "http://proxy@ip"
]
token=""
async def main():
    proxies=ProxyPool(
    proxies=p
    )
    async with Endfield(debug=True,proxy_pool=proxies) as ef:
        # await ef.update_assets()
        data = await ef.get_showcase(uid)
        print(data.profile.name)
        for char in data.characters:
            print(char.name)
            for stat in char.stats:
                print(f"  {stat[0]}: {stat[1]}")
            print("\n\n")

    # async with Endfield(debug=True,proxy_pool=proxies) as ef:
    #     stats = await ef.get_game_stats(token, server=3)
    #     if stats:
    #         print(stats.sanity_point.model_dump_json(indent=2))
    #         print(stats.battle_pass.model_dump_json(indent=2))
    #         print(stats.daily_points.model_dump_json(indent=2))
    #         print(stats.weekly_points.model_dump_json(indent=2))
    #     else:
    #         print("Failed to fetch game stats.")
    
    # async with Endfield() as ef:
    #     blueprints = await ef.get_factory_blueprints(
    #         region='Asia',
    #         item='xiranite',
    #         start=0,
    #         end=10
    #     )
    #     print(blueprints.model_dump_json(indent=2))
    
    await proxies.close()
if __name__ == "__main__":
    asyncio.run(main())