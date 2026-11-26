import logging
import aiomysql
import discord
from discord.ext import commands

import botdb
from helpers import passembed

class CustomRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(aliases=['cr','customrole'],invoke_without_command=True)
    async def crole(self, ctx):
        await ctx.send('hello')

    @crole.command()
    @commands.guild_only()
    async def create(self, ctx, *, name: str):
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
    async def color(self, ctx, colorhex: str):
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
