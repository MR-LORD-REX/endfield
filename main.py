from endfield import Endfield
import asyncio
import json

uid=4225399080

async def main():
    async with Endfield(debug=True) as ef:
        data = await ef.get_showcase(uid)
        with open(f"showcase_{uid}.json", "w") as f:
            f.write(data.model_dump_json(indent=2))
        for char in data.characters:
            print(f"{char.name}")
            print(f"{char.weapon}")
            for stat in char.stats:
                print(stat)
            print("\n")
            
if __name__ == "__main__":
    asyncio.run(main())