import os
import traceback
from typing import List, Dict, Set
from include.constants import VIDEO_DB_ORG_ID
import discord
from src.model.issue import DiscordMessage
from discord.ext import commands
from discord.message import Attachment
from src.core.event.tool_actions.handle_discord_message import DiscordMessageHandler
import logging
import asyncio

BOT_NAME = "ask-cirroe"

# Configure logging
logging.basicConfig(level=logging.INFO)


class CirroeDiscordBot(commands.Bot):
    def __init__(self, intents, org_id: str):
        super().__init__(command_prefix="!", intents=intents)
        self.post_channel_id = None  # Will be set during setup
        self.org_id = org_id
        self.discord_msg_handler = DiscordMessageHandler(org_id)
        self.processing_threads: Dict[int, asyncio.Event] = (
            {}
        )  # Track threads being processed
        self.pending_messages: Dict[int, List[discord.Message]] = (
            {}
        )  # Store pending messages per thread
        self.processed_messages: Set[int] = set()  # Track processed message IDs

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
            if message.id not in self.processed_messages:
                messages.append(f"{message.author.display_name}: {message.content}")

        # Add any pending messages for this thread that haven't been processed
        if thread.id in self.pending_messages:
            for msg in self.pending_messages[thread.id]:
                if msg.id not in self.processed_messages:
                    messages.append(f"{msg.author.display_name}: {msg.content}")

        return "\n".join(messages)  # Join messages with newlines for better readability

    async def handle_thread_response(self, thread, message):
        """Handle responses in a thread"""
        thread_id = thread.id

        # If message was already processed, ignore it
        if message.id in self.processed_messages:
            return

        # Check if thread is already being processed
        if thread_id in self.processing_threads:
            # Add message to pending messages if not already processed
            if thread_id not in self.pending_messages:
                self.pending_messages[thread_id] = []
            if message.id not in self.processed_messages:
                self.pending_messages[thread_id].append(message)
                logging.info(f"Added message to pending queue for thread {thread_id}")
            return

        # Create processing lock for this thread
        self.processing_threads[thread_id] = asyncio.Event()

        try:
            # Start typing indicator
            async with thread.typing():
                messages = await self.__construct_thread_messages(thread)

                # If no unprocessed messages, return
                if not messages.strip():
                    return

                # Generate AI response
                response = await self.generate_ai_response(
                    messages, message.author.display_name, message.attachments
                )

                # Check for empty response
                if not response:
                    await thread.send(
                        "I apologize, but I couldn't generate a response. Please try rephrasing your question."
                    )
                    return

                # Send response in the thread
                await thread.send(response)

                # Mark all pending messages as processed
                if thread_id in self.pending_messages:
                    for msg in self.pending_messages[thread_id]:
                        self.processed_messages.add(msg.id)
                self.processed_messages.add(message.id)

        except Exception as e:
            traceback.print_exc()
            logging.error(f"Error in thread response: {e}")
            try:
                await thread.send(
                    "I encountered an error processing your request. Please try again."
                )
            except Exception:
                pass

        finally:
            # Clean up
            if thread_id in self.pending_messages:
                del self.pending_messages[thread_id]
            if thread_id in self.processing_threads:
                del self.processing_threads[thread_id]

    async def handle_post_channel_response(self, message):
        """Handle responses in the designated post channel"""
        try:
            # Start typing indicator
            async with message.channel.typing():
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
            return

        # Handle messages in threads
        if isinstance(message.channel, discord.Thread):
            # Only respond if the thread was created by the bot
            if message.channel.owner_id == self.user.id:
                # Check if bot is mentioned or if it's a direct reply in the bot's thread
                if self.user.mentioned_in(message) or not message.reference:
                    await self.handle_thread_response(message.channel, message)
            return

        # Handle direct bot mentions in non-thread channels
        if self.user.mentioned_in(message):
            thread = await message.create_thread(
                name=f"Question from {message.author.display_name}"
            )
            logging.info("creating thread for initial message")
            await self.handle_thread_response(thread, message)


def dsc_poll_main():
    # Set up intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    intents.guilds = True
    intents.members = True

    # Initialize bot
    bot = CirroeDiscordBot(intents=intents, org_id=VIDEO_DB_ORG_ID)

    # Run the bot
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
