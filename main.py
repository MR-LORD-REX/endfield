from src.endfield import Endfield
import asyncio

uid=4225399080
token=""

async def main():
    async with Endfield() as ef:
        await ef.update_assets()
        data = await ef.get_showcase(uid)
        print(data.profile.model_dump_json(indent=2))
    for char in data.characters:
        print(char.name)
        for stat in char.stats:
            print(f"  {stat[0]}: {stat[1]}")
        print("\n\n")
        
    async with Endfield() as ef:
        stats = await ef.get_game_stats(token, server=3)
        if stats:
            print(stats.sanity_point.model_dump_json(indent=2))
            print(stats.battle_pass.model_dump_json(indent=2))
            print(stats.daily_points.model_dump_json(indent=2))
            print(stats.weekly_points.model_dump_json(indent=2))
        else:
            print("Failed to fetch game stats.")
    async with Endfield() as ef:
        blueprints = await ef.get_factory_blueprints(
            region='Asia',
            item='heavy-xiranite',
            start=0,
            end=10
        )
        print(blueprints.model_dump_json(indent=2))
if __name__ == "__main__":
    asyncio.run(main())