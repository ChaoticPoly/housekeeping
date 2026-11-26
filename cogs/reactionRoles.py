import discord
from discord.ext import commands

import botdb
from helpers import COLOR, passembed


class rrDraft():
    def __init__(self, title:str):
        self.title = title
        self.pairs: dict[str, int] = {}

def emoteKey(emote: discord.PartialEmoji):
                    if emote.id is not None:
                        return str(emote.id)
                    return emote.name

class ReactionRoles(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.drafts: dict[tuple[int, int,], rrDraft] = {}

    def renderEmote(self, key:str):
            if key.isdigit():
                found = self.bot.get_emoji(int(key))
                return str(found) if found else f"<:_:{key}>"
            return key



    def rrBuild(self, guild: discord.Guild, title: str, pairs) -> discord.Embed:
        lines = []
        for key, role_id in pairs:
            role = guild.get_role(role_id)
            if role is None:
                continue
            lines.append(f"{self.renderEmote(key)}: {role.mention}")
        return discord.Embed(title=title, description="\n".join(lines) or "No roles configured.", color=COLOR,)


    @commands.group(aliases=['rr','reactionrole'],invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def rrole(self, ctx):
        await ctx.send("hi")

    @rrole.command(aliases=['draft'])
    @commands.guild_only()
    async def create(self, ctx, *, name: str):
        if len(name) > 256:
            embed = await passembed(False, "Reaction Role Create", "Embed titles can be at most 256 characters.")
            embed.set_footer(text="~rrole create")
            return await ctx.send(embed=embed)
        key = (ctx.guild.id, ctx.author.id)

        if key in self.drafts:
            embed = await passembed(False,"Reaction Role Drafting","You already have a draft.\nPost or cancel it first.")
            embed.set_footer(text="~rrole create")
            return await ctx.send(embed=embed)
        self.drafts[key] = rrDraft(name)
        embed = await passembed(True, "Reaction Role Drafting", f"Draft '{name}' started.")
        embed.set_footer(text="~rrole create")
        await ctx.send(embed=embed)

    @rrole.command(aliases=['delete'])
    @commands.guild_only()
    async def cancel(self, ctx):
        key = (ctx.guild.id, ctx.author.id)
        removed = self.drafts.pop(key, None)
        if removed is None:
            embed = await passembed(False, "Reaction Role Drafting", "You do not have a draft.")
            embed.set_footer(text="~rrole cancel")
            return await ctx.send(embed=embed)
        embed = await passembed(True, "Reaction Role Drafting", f"Draft '{removed.title}' cancelled.")
        embed.set_footer(text="~rrole cancel")
        await ctx.send(embed=embed)

    @rrole.command(aliases=['preview','check'])
    @commands.guild_only()
    async def view(self, ctx):
        draft = self.drafts.get((ctx.guild.id,ctx.author.id))
        if draft is None:
            embed = await passembed(False, "Reaction Role Drafting", "You do not have a draft.")
            embed.set_footer(text="~rrole cancel")
            return await ctx.send(embed=embed)
        embed = self.rrBuild(ctx.guild, draft.title, draft.pairs.items())
        await ctx.send(embed=embed)


    @rrole.command()
    @commands.guild_only()
    async def add(self, ctx, emote: discord.PartialEmoji, role: discord.Role):
        draft = self.drafts.get((ctx.guild.id, ctx.author.id))
        if draft is None:
            embed = await passembed(False,"Reaction Role Drafting", "You do not have a draft.")
            embed.set_footer(text="~rrole add")
            return await ctx.send(embed=embed)
        if len(draft.pairs) >= 20 and emoteKey(emote) not in draft.pairs:
            embed = await passembed(False,"Reaction Role Drafting", "A panel can only hold 20 reactions")
            embed.set_footer(text="~rrol add")
            return await ctx.send(embed=embed)
        draft.pairs[emoteKey(emote)] = role.id
        embed = await passembed(True, "Reaction Role Drafting", f"Added {emote} as {role.mention} to '{draft.title}")
        embed.set_footer(text="~rrole add")
        await ctx.send(embed=embed)
