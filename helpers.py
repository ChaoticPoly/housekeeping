import discord
import os

COLOR = int(os.getenv('COLOR', '757cff'), 16)
PASSED = 0x12FF79
FAILED = 0xba0009

async def passembed(embedType: bool, title: str, desc: str):
    if embedType == True:
        embed = discord.Embed(
        title=title,
        description=desc,
        color = PASSED
        )
    else:
        embed = discord.Embed(
        title=title,
        description=desc,
        color = FAILED
        )
    return embed
