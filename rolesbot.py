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
        embed = discord.Embed(
        title="Role Creation",
        color=FAILED,
        description=f"'{existing_role}' already exists",
        )
        embed.set_footer(text="~crole create")

        return await ctx.send(embed=embed)
        
    try:
        new_role = await ctx.guild.create_role(
            name=name, 
            mentionable=True # Allow the role to be mentioned
        )
        embed = discord.Embed(
        title="Role Creation",
        color=PASSED,
        description=f"'{new_role.name}' created successfully!",
        )
        await author.add_roles(new_role)

    except discord.Forbidden:
        embed = discord.Embed(
        title="Role Creation",
        color=FAILED,
        description="Failed! Permission Denied.",
        )
    except Exception as e:
        embed = discord.Embed(
        title="Role Creation",
        color=FAILED,
        description=f"Failed! {e}",
        )
    embed.set_footer(text="~crole create")
    await ctx.send(embed=embed) 
@crole.command()
async def color(ctx):
    guild = ctx.guild

    existing_role = discord.utils.get(guild.roles, name="yes")
    if existing_role is not None:
        pass
    print("test")


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

    # Add reactions so users can click them
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
        # bot missing permissions or role hierarchy issue
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