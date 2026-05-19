from src.endfield import Endfield
import asyncio
import json

uid=4225399080

async def main():
    async with Endfield(debug=True) as ef:
        data = await ef.get_showcase(uid)
        print(data.profile.model_dump_json(indent=2))
            
if __name__ == "__main__":
    asyncio.run(main())