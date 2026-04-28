from endfield import Endfield

async def main():
    async with Endfield() as client:
        await client.update_assets()
        data=await client.get_showcase(4225399080)
        print(data.profile.name)
        with open(f"showcase_4225399080.json","w") as f:
            f.write(data.model_dump_json(indent=2))
        
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())