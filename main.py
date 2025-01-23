from src.core.event.poll_discord import CirroeDiscordBot
import asyncio
from playground import index
from include.constants import VIDEO_DB_ORG_ID
from src.storage.supa import SupaClient
from include.constants import REPO_NAME
import logging
import discord
import os

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
            await index(
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

if __name__ == "__main__":
    # Set up intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    intents.guilds = True
    intents.members = True

    # Initialize bot
    bot = CirroeDiscordBot(intents=intents, org_id=VIDEO_DB_ORG_ID)

    # Add the periodic indexing task to the bot's event loop (removed for now until we solve the zilliz issue)
    # @bot.event
    # async def on_ready():
    #     logging.info(f"Logged in as {bot.user.name}")
    #     bot.loop.create_task(periodic_index())

    # Run the bot
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
