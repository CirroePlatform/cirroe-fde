from src.core.event.poll_discord import dsc_poll_main
import asyncio
from playground import index
from include.constants import VIDEO_DB_ORG_ID
from src.storage.supa import SupaClient
from include.constants import REPO_NAME
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

async def periodic_index():
    while True:
        try:
            logging.info("Starting periodic indexing...")
            # Get repo info from Supabase
            supa = SupaClient(VIDEO_DB_ORG_ID)
            repo_info = supa.get_user_data(
                "org_name", REPO_NAME, "repo_url", "docu_url", debug=True
            )

            # Run indexing
            index(
                VIDEO_DB_ORG_ID,
                repo_info["org_name"],
                repo_info[REPO_NAME],
                repo_info["docu_url"]
            )
            logging.info("Periodic indexing completed successfully")
        except Exception as e:
            logging.error(f"Error during periodic indexing: {e}")
        
        # Wait for 24 hours
        await asyncio.sleep(24 * 60 * 60)  # 24 hours in seconds

async def main():
    # Create tasks for both Discord bot and periodic indexing
    discord_task = asyncio.create_task(dsc_poll_main())
    index_task = asyncio.create_task(periodic_index())
    
    # Wait for both tasks indefinitely
    await asyncio.gather(discord_task, index_task)

if __name__ == "__main__":
    asyncio.run(main())
