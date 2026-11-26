import logging
import discord
from discord.ext import commands

from helpers import passembed

class NativeRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(aliases=['nr','r','role'], invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)

    async def nrole(self, ctx):
        await ctx.send("morning")

    @nrole.command()
    @commands.guild_only()
    async def create(self, ctx, *, name: str):
        if len(name) > 100:
            embed = await passembed(False, "Role Creation", "Role names can be at most 100 characters.")
            embed.set_footer(text="~nrole create")
            return await ctx.send(embed=embed)
        newRole = None
        try:
            newRole = await ctx.guild.creat_role(name=name)
            embed = await passembed(True, "Role Creation", f"{newRole.mention} created.")
        except discord.Forbidden:
            embed = await passembed(False, "Role Creation", "Permission Denied.")
        except Exception:
            logging.exception("basic role creation failure")
            embed = await passembed(False, "Role Creation", "Something mysterious happened.")

        embed.set_footer(text="~role create")
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(NativeRoles(bot))
