import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('TOKEN')
COLOR = int(os.getenv('COLOR'), 16)
PASSED = 0x12FF79 
FAILED = 0xba0009

intents = discord.Intents.default()
intents.message_content = True  
intents.reactions = True
bot = commands.Bot(command_prefix='~', intents=intents)

@bot.group(invoke_without_command=True)
async def crole(ctx):
    await ctx.send('hello')
@crole.command()
async def create(ctx, name: str):
    author = ctx.author
    guild = ctx.guild
    existing_role = discord.utils.get(guild.roles, name=name)
    
    if existing_role is not None:
        embed = await passembed(0, "Role Creation", f"{existing_role.mention} already exists.")
        embed.set_footer(text="~crole create")
        return await ctx.send(embed=embed)
    try:
        new_role = await ctx.guild.create_role(
            name=name, 
            mentionable=True
        )
        embed = await passembed(1, "Role Creation", f"{new_role.mention} created successfully.")
        await author.add_roles(new_role)

    except discord.Forbidden:
        embed = await passembed(0, "Role Creation", "Error: Permission Denied.")
    except Exception as e:
        embed = await passembed(0, "Role Creation", f"Error: {e}")
    embed.set_footer(text="~crole create")
    await ctx.send(embed=embed) 

@crole.command()
async def color(ctx, rolename: str, colorhex):
    guild = ctx.guild

    if rolename.startswith('<@&') and rolename.endswith('>'):
        role = guild.get_role(int(rolename[3:-1]))
    else:
        role = discord.utils.get(guild.roles, name=rolename)
    if role is not None:
        try:
            color_int = int(colorhex, 16) 
            await role.edit(color=color_int)
            embed = await passembed(1,"Role Color", f"Role {role.mention} updated.")
        except ValueError:
            embed = await passembed(0, "Role Color", "Invalid Hex.")
        except discord.Forbidden:
            embed = await passembed(0, "Role Color", "Error: Permission Denied.")
        except Exception as e:
            embed = await passembed(0, "Role Color", f"Error: {e}")
    else: 
        embed = await passembed(0, "Role Color", f"Error: '{rolename}' does not exist.")
    embed.set_footer(text="~crole color")
    await ctx.send(embed=embed) 

async def passembed(embedType: bool, title: str, desc: str):
    if embedType == 1:
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