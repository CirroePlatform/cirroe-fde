import os
from include.constants import MEM0AI_ORG_ID
import discord
from src.model.issue import DiscordMessage
from discord.ext import commands
from src.core.event.user_actions.handle_discord_message import DiscordMessageHandler
import asyncio
import aiohttp
import logging

BOT_NAME = "cirroe-bot-token"

# Configure logging
logging.basicConfig(level=logging.INFO)

class CirroeDiscordBot(commands.Bot):
    def __init__(self, intents, org_id: str):
        super().__init__(command_prefix='!', intents=intents)
        self.post_channel_id = None  # Will be set during setup
        self.org_id = org_id
        self.discord_msg_handler = DiscordMessageHandler(org_id)

    async def setup_hook(self):
        """Set up any background tasks or initial configurations"""
        logging.info("Bot is setting up...")

    async def generate_ai_response(self, content: str, author: str):
        """
        Generate AI response using an AI service API
        Replace with your preferred AI service (OpenAI, Anthropic, etc.)
        """
        response = self.discord_msg_handler.handle_discord_message(DiscordMessage(content=content, author=author))

        return response["response"]

    async def handle_thread_response(self, thread, message):
        """Handle responses in a thread"""
        try:
            # Generate AI response
            response = await self.generate_ai_response(
                message.content, 
                message.author.display_name
            )

            # Send response in the thread
            await thread.send(response)
        except Exception as e:
            logging.error(f"Error in thread response: {e}")

    async def handle_post_channel_response(self, message):
        """Handle responses in the designated post channel"""
        try:
            # Generate AI response
            response = await self.generate_ai_response(
                message.content, 
                message.attachments[0].url if message.attachments else None
            )
            
            # Create a thread for the response
            thread = await message.create_thread(name=f"Discussion: {message.content[:50]}")
            await thread.send(response)
        except Exception as e:
            logging.error(f"Error in post channel response: {e}")

    async def on_ready(self):
        """Bot startup confirmation"""
        logging.info(f'Logged in as {self.user.name}')
        
        # You'll need to manually set the post channel ID during bot setup
        if not self.post_channel_id:
            logging.warning("Post channel ID not set! Use set_post_channel method.")

    async def on_message(self, message: discord.Message):
        """Handle different message scenarios"""
        # Ignore messages from the bot itself
        if message.author.display_name == BOT_NAME:
            return

        # Handle bot mentions
        if self.user.mentioned_in(message):
            # Create or use existing thread
            thread = message.thread or await message.create_thread(name=f"Question from {message.author.display_name}")
            await self.handle_thread_response(thread, message)
            return

        # Handle messages in designated post channel
        if message.channel.id == self.post_channel_id:
            await self.handle_post_channel_response(message)

def dsc_poll_main():
    # Set up intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    intents.guilds = True
    intents.members = True

    # Initialize bot
    bot = CirroeDiscordBot(intents=intents, org_id=MEM0AI_ORG_ID)

    # Run the bot
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))