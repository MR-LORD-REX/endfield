from endfield import Endfield
import asyncio
import json

uid=4225399080

async def main():
    async with Endfield() as ef:
        data = await ef.get_showcase(uid)
        print(data.profile.model_dump_json(indent=2))
    for char in data.characters:
        print(char.name)
        for stat in char.stats:
            print(f"  {stat[0]}: {stat[1]}")
        print("\n\n")
            
if __name__ == "__main__":
    asyncio.run(main())