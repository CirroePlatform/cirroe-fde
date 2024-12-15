import os
import traceback
from typing import List
from include.constants import MEM0AI_ORG_ID
import discord
from src.model.issue import DiscordMessage
from discord.ext import commands
from discord.message import Attachment
from src.core.event.user_actions.handle_discord_message import DiscordMessageHandler
import logging

BOT_NAME = "cirroe-bot-token"

# Configure logging
logging.basicConfig(level=logging.INFO)


class CirroeDiscordBot(commands.Bot):
    def __init__(self, intents, org_id: str):
        super().__init__(command_prefix="!", intents=intents)
        self.post_channel_id = None  # Will be set during setup
        self.org_id = org_id
        self.discord_msg_handler = DiscordMessageHandler(org_id)

    async def setup_hook(self):
        """Set up any background tasks or initial configurations"""
        logging.info("Bot is setting up...")

    async def generate_ai_response(
        self, content: str, author: str, attachments: List[Attachment]
    ):
        """
        Generate AI response using an AI service API
        Replace with your preferred AI service (OpenAI, Anthropic, etc.)
        """
        response = self.discord_msg_handler.handle_discord_message(
            DiscordMessage(
                content=content,
                author=author,
                attachments=[
                    (attachment.url, attachment.content_type)
                    for attachment in attachments
                ],
            )
        )

        return response["response"]

    async def __construct_thread_messages(self, thread) -> str:
        messages = []

        # Use async for to properly iterate over the async iterator
        async for message in thread.history(limit=100, oldest_first=True):
            messages.append(f"{message.author.display_name}: {message.content}")

        return "\n".join(messages)  # Join messages with newlines for better readability

    async def handle_thread_response(self, thread, message):
        """Handle responses in a thread"""

        try:
            messages = await self.__construct_thread_messages(thread)
            messages += f"\n{message.author.display_name}: {message.content}"

            # Generate AI response
            response = await self.generate_ai_response(
                messages, message.author.display_name, message.attachments
            )

            # Send response in the thread
            await thread.send(response)
        except Exception as e:
            traceback.print_exc()
            logging.error(f"Error in thread response: {e}")

    async def handle_post_channel_response(self, message):
        """Handle responses in the designated post channel"""
        try:
            # Generate AI response
            response = await self.generate_ai_response(
                message.content, message.author.display_name, message.attachments
            )

            # Create a thread for the response
            thread = await message.create_thread(
                name=f"Discussion: {message.content[:50]}"
            )
            await thread.send(response)
        except Exception as e:
            logging.error(f"Error in post channel response: {e}")

    async def on_ready(self):
        """Bot startup confirmation"""
        logging.info(f"Logged in as {self.user.name}")

        # You'll need to manually set the post channel ID during bot setup
        if not self.post_channel_id:
            logging.warning("Post channel ID not set! Use set_post_channel method.")

    async def on_message(self, message: discord.Message):
        """Handle different message scenarios"""
        # Ignore messages from the bot itself
        if message.author.display_name == BOT_NAME:
            return

        # Handle messages in designated post channel
        if message.channel.id == self.post_channel_id:
            await self.handle_post_channel_response(message)

        # Handle bot mentions
        if self.user.mentioned_in(message):
            # Create thread for initial message
            thread = await message.create_thread(
                name=f"Question from {message.author.display_name}"
            )
            logging.info("creating thread for initial message")
            await self.handle_thread_response(thread, message)
        elif (message.thread and message.thread.owner == self.user) or (
            message.channel and message.channel.owner == self.user
        ):
            logging.info("handling followup")
            await self.handle_thread_response(message.channel, message)


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
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
