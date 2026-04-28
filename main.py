from endfield import Endfield

async def main():
    async with Endfield() as client:
        # await client.update_assets()
        data=await client.get_showcase(4225399080)
        for char in data.characters:
            for stat in char.stats:
                print(stat)
        
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())