import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
import os
import botdb
import aiomysql
import logging

loaded = load_dotenv()
if not loaded:
    raise RuntimeError(".env file not found or empty")

TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise RuntimeError("bot token not found")

COLOR = int(os.getenv('COLOR', '757cff'), 16)
PASSED = 0x12FF79
FAILED = 0xba0009

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

class RoleBot(commands.Bot):
    async def setup_hook(self):
        await botdb.init_pool()

    async def close(self):
        await botdb.close_pool()
        await super().close()

bot = RoleBot(command_prefix='~', intents=intents)

@bot.group(invoke_without_command=True)
async def crole(ctx):
    await ctx.send('hello')
@crole.command()
@commands.guild_only()
async def create(ctx, *, name: str):
    guild = ctx.guild
    author = ctx.author

    if len(name) > 100:
        embed = await passembed(False, "Role Creation", "Role names can be at most 100 characters.")
        embed.set_footer(text='~crole create')
        return await ctx.send(embed=embed)

    existing_id = await botdb.dbGetRole(guild.id, author.id)
    if existing_id is not None:
        role = guild.get_role(existing_id)
        if role is not None:
            embed = await passembed(False, "Role Creation", f"You already have {role.mention}")
            embed.set_footer(text='~crole create')
            return await ctx.send(embed=embed)
        await botdb.dbDeleteRole(guild.id, author.id)

    new_role = None
    saved = False
    try:
        new_role = await guild.create_role(name=name, mentionable = True)
        await author.add_roles(new_role)
        await botdb.dbSaveRole(guild.id, author.id, new_role.id)
        saved = True
        embed = await passembed(True, "Role Creation", f"{new_role.mention} created successfully.")
    except discord.Forbidden:
        embed = await passembed(False, "Role Creation", "Error: Permission Denied.")
    except aiomysql.IntegrityError:
        embed = await passembed(False, "Role Creation", "You already have a custom role")
    except Exception:
        logging.exception("crole create failure")
        embed = await passembed(False, "Role Creation", "Something broke.")

    if new_role is not None and not saved:
        try:
            await new_role.delete()
        except discord.HTTPException:
            logging.exception("could not clean up role %s", new_role.id)

    embed.set_footer(text = "~crole create")
    await ctx.send(embed=embed)

@crole.command()
@commands.guild_only()
async def color(ctx, colorhex: str):
    guild = ctx.guild
    author = ctx.author

    role = None
    role_id = await botdb.dbGetRole(guild.id, author.id)
    if role_id is not None:
        role = guild.get_role(role_id)
        if role is None:
            await botdb.dbDeleteRole(guild.id, author.id)

    if role is None:
        embed = await passembed(False, "Role Color", "Create a role with ~crole create")
    else:
        try:
            colorhex = colorhex.strip().removeprefix('#')
            if len(colorhex) != 6:
                raise ValueError("Hex color must be 6 characters")
            color_int = int(colorhex, 16)
            if not 0 <= color_int <= 0xFFFFFF:
                raise ValueError("Color out of range")
            await role.edit(color=color_int)
            embed = await passembed(True, "Role Color", f"Role {role.mention} updated.")
        except ValueError:
            embed = await passembed(False, "Role Color", "Invalid Hex Color.")
        except discord.Forbidden:
            embed = await passembed(False, "Role Color", "Error: Permission Denied.")
        except Exception:
            logging.exception("crole color failure")
            embed = await passembed(False, "Role Color", "Something broke.")

    embed.set_footer(text="~crole color")
    await ctx.send(embed=embed)


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


REACTION_ROLES = {
    "<:utd:1467987437996347402>": 1467988190970253334,
    "<:tt:1467988022342713464>": 1467988265310093397,
}
@bot.command()
@commands.has_permissions(manage_roles=True)
async def rr(ctx):
    desc_lines = []
    for emoji, role_id in REACTION_ROLES.items():
        role = ctx.guild.get_role(role_id)
        if role:
            desc_lines.append(f"{emoji} → {role.mention}")
    description = "\n".join(desc_lines) or "No roles configured."

    embed = discord.Embed(
        title="Reaction Roles",
        description=description,
        color=COLOR
    )
    msg = await ctx.send(embed=embed)

    for emoji in REACTION_ROLES.keys():
        await msg.add_reaction(emoji)

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    emoji = str(payload.emoji)
    if emoji not in REACTION_ROLES:
        return

    role_id = REACTION_ROLES[emoji]
    role = guild.get_role(role_id)
    if role is None:
        return

    member = guild.get_member(payload.user_id)
    if member is None:
        member = await guild.fetch_member(payload.user_id)

    try:
        await member.add_roles(role, reason="Reaction role add")
    except discord.Forbidden:
        pass

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    emoji = str(payload.emoji)
    if emoji not in REACTION_ROLES:
        return

    role_id = REACTION_ROLES[emoji]
    role = guild.get_role(role_id)
    if role is None:
        return

    member = guild.get_member(payload.user_id)
    if member is None:
        member = await guild.fetch_member(payload.user_id)

    try:
        await member.remove_roles(role, reason="Reaction role remove")
    except discord.Forbidden:
        pass

bot.run(TOKEN)
