from ast import alias
from operator import add

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

class rrDraft():
    def __init__(self, title:str):
        self.title = title
        self.pairs: dict[str, int] = {}

drafts: dict[tuple[int, int], rrDraft] = {}

bot = RoleBot(command_prefix='~', intents=intents)

@bot.group(aliases=['cr','customrole'],invoke_without_command=True)
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

    existing_id = await botdb.crGetRole(guild.id, author.id)
    if existing_id is not None:
        role = guild.get_role(existing_id)
        if role is not None:
            embed = await passembed(False, "Role Creation", f"You already have {role.mention}")
            embed.set_footer(text='~crole create')
            return await ctx.send(embed=embed)
        await botdb.crDeleteRole(guild.id, author.id)

    new_role = None
    saved = False
    try:
        new_role = await guild.create_role(name=name, mentionable = True)
        await author.add_roles(new_role)
        await botdb.crSaveRole(guild.id, author.id, new_role.id)
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
    role_id = await botdb.crGetRole(guild.id, author.id)
    if role_id is not None:
        role = guild.get_role(role_id)
        if role is None:
            await botdb.crDeleteRole(guild.id, author.id)

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



@bot.group(aliases=['rr','reactionrole'],invoke_without_command=True)
@commands.has_permissions(manage_roles=True)
async def rrole(ctx):
    await ctx.send("hi")

@rrole.command(aliases=['draft'])
@commands.guild_only()
async def create(ctx, *, name: str):
    author = ctx.author
    guild = ctx.guild

    if len(name) > 256:
        embed = await passembed(False, "Reaction Role Create", "Embed titles can be at most 256 characters.")
        embed.set_footer(text="~rrole create")
        return await ctx.send(embed=embed)
    key = (guild.id, author.id)

    if key in drafts:
        embed = await passembed(False,"Reaction Role Drafting","You already have a draft.\nPost or cancel it first.")
        embed.set_footer(text="~rrole create")
        return await ctx.send(embed=embed)
    drafts[key] = rrDraft(name)
    embed = await passembed(True, "Reaction Role Drafting", f"Draft '{name}' started.")
    embed.set_footer(text="~rrole create")
    await ctx.send(embed=embed)

@rrole.command(aliases=['delete'])
@commands.guild_only()
async def cancel(ctx):
    key = (ctx.guild.id, ctx.author.id)
    removed = drafts.pop(key, None)
    if removed is None:
        embed = await passembed(False, "Reaction Role Drafting", "You do not have a draft.")
        embed.set_footer(text="~rrole cancel")
        return await ctx.send(embed=embed)
    embed = await passembed(True, "Reaction Role Drafting", f"Draft '{removed.title}' cancelled.")
    embed.set_footer(text="~rrole cancel")
    await ctx.send(embed=embed)

@rrole.command(aliases=['preview','check'])
@commands.guild_only()
async def view(ctx):
    draft = drafts.get((ctx.guild.id,ctx.author.id))
    if draft is None:
        embed = await passembed(False, "Reaction Role Drafting", "You do not have a draft.")
        embed.set_footer(text="~rrole cancel")
        return await ctx.send(embed=embed)
    embed = rrBuild(ctx.guild, draft.title, draft.pairs.items())
    await ctx.send(embed=embed)


@rrole.command()
@commands.guild_only()
async def add(ctx, emote: discord.PartialEmoji, role: discord.Role):
    draft = drafts.get((ctx.guild.id, ctx.author.id))
    if draft is None:
        embed = await passembed(False,"Reaction Role Drafting", "You do not have a draft.")
        embed.set_footer(text="~rrole add")
        return await ctx.send(embed=embed)
    if len(draft.pairs) >= 20 and emoteKey(emote) not in draft.pairs:
        embed = await passembed(False,"Reaction Role Drafting", "A panel can only hold 20 reactions")
        embed.set_footer(text="~rrol add")
        return await ctx.send(embed=embed)
    draft.pairs[emoteKey(emote)] = role.id
    embed = discord.Embed(title = "Reaction Role Drafting",description=f"Added {emote} as {role.mention} to '{draft.title}")
    embed.set_footer(text="~rrole add")
    await ctx.send(embed=embed)

def renderEmote(key:str):
    if key.isdigit():
        found = bot.get_emoji(int(key))
        return str(found) if found else f"<:_:{key}>"
    return key

def emoteKey(emote: discord.PartialEmoji):
    if emote.id is not None:
        return str(emote.id)
    return emote.name

def rrBuild(guild: discord.Guild, title: str, pairs) -> discord.Embed:
    lines = []
    for key, role_id in pairs:
        role = guild.get_role(role_id)
        if role is None:
            continue
        lines.append(f"{renderEmote(key)}: {role.mention}")
    return discord.Embed(title=title, description="\n".join(lines) or "No roles configured.", color=COLOR,)



bot.run(TOKEN)
