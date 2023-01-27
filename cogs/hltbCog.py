import discord
from discord.ext import commands
from howlongtobeatpy import HowLongToBeat

import clients.hltbClientImpl as hltbClientImpl
import utils.discordUtils as discordUtils

class hltb_commands(commands.Cog):

    hltbClient: hltbClientImpl.hltb_hunter = hltbClientImpl.hltb_hunter()

    def __init__(self, bot):
        """Constructor to init hltb_commands

        Args:
            bot (discord.Ext.bot): required arg for child Cog
        Exceptions:
            None
        """
        self.bot = bot

    @commands.command()
    async def hltb(self, ctx, arg):
        """Command to get HowLongToBeat results for a given query

        Args:
            ctx (discord.Context): Discord context for command invocation, arg (str): game search query
        Exceptions:
            None
        """
        result: dict[str, str] = self.hltbClient.search(arg)
        if result: 
            url: str = result.pop('HLTB Link')
            name: str = result.pop('Name')
            image: str = result.pop('Image')
            embed: discord.Embed = discordUtils.create_field_embed(result, f"How Long To Beat {name}", url)
            if url:
                discordUtils.set_embed_image(embed, image)
            await ctx.message.reply(embed=embed)
            return  
        else:
            await ctx.reply("No matches found for this game!")

    @commands.command()
    async def hltbhelp(self, ctx):
        """Command to give help info on `hltb_commands` commands

        Args:
            ctx (discord.Context): Discordpy context for command invocation
        Exceptions:
            None
        """
        helpRef: dict[str, str] = {
            "$hltb <query> | $hltb '<multi-word query>'": "Example usage would be `$hltb \"elden ring\"` or `$hltb halo`"
        }
        embed: discord.Embed = discordUtils.create_field_embed(helpRef, "HowLongToBeat User Guide", "https://github.com/AbdulMoMo/DealsBot/blob/main/README.md")
        await ctx.reply(embed=embed)
        