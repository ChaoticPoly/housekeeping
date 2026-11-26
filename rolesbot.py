import discord
from discord.ext import commands

from dotenv import load_dotenv
import os

import botdb


loaded = load_dotenv()
if not loaded:
    raise RuntimeError(".env file not found or empty")

TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise RuntimeError("bot token not found")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

EXTENSIONS = ["cogs.customRoles", "cogs.reactionRoles", "cogs.nativeRoles"]

class RoleBot(commands.Bot):
    async def setup_hook(self):
        await botdb.init_pool()
        for ext in EXTENSIONS:
            await self.load_extension(ext)

    async def close(self):
        await botdb.close_pool()
        await super().close()


bot = RoleBot(command_prefix='~', intents=intents)
bot.run(TOKEN)
