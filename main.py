from src.endfield import Endfield
from ef_cards import EFCard

from ef_cards.utils.assets.core import asset_manager
import asyncio
uid=4225399080
async def main():
    try:
        ef=Endfield(debug=True)
        ef_c=EFCard(ef=ef)
        card=await ef_c.get_all_characters_card(uid)
        for c in card:
            c.show()
    except Exception as e:
        print(f"Error in main: {e}")
            
    finally:
        await asset_manager.close()
        
if __name__ == "__main__":
    asyncio.run(main())