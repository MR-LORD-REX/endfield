from endfield import Endfield
import asyncio

async def main():
    async with Endfield() as client:
        data=await client.get_showcase(4225399080)
        with open("showcase.json", "w") as f:
            f.write(data.model_dump_json(indent=2))
        for char in data.characters:
            print(f"Character: {char.name}")
            print(f"weapon: {char.weapon.name}")
            for stat in char.stats:
                print(stat)
            print("\n")
            
if __name__ == "__main__":
    asyncio.run(main())