from endfield import Endfield
import asyncio

async def main():
    async with Endfield() as client:
        data=await client.get_showcase(4225399080)
        for char in data.characters:
            print(f"Character: {char.name}")
            for stat in char.stats:
                print(stat)
            print("\n")
if __name__ == "__main__":
    asyncio.run(main())