from discord.ext import commands
from howlongtobeatpy import HowLongToBeat

import clients.hltbClientImpl as hltbClientImpl
import utils.discordUtils as discordUtils

class hltb_commands(commands.Cog):

    hltbClient = hltbClientImpl.hltb_hunter()

    # Constructor to init hltb_commands
    # Inputs: bot (discord.Ext.bot)
    # Outputs: None 
    # Exceptions None 
    def __init__(self, bot):
        self.bot = bot

    @commands.command
    async def hltb(self, ctx, arg):
        result: HowLongToBeat = self.hltbClient.search(arg)
        if result is None: 
            await ctx.reply("Sorry! I found no results for this game.")
        await discordUtils.make_htlb_thread(result, ctx.message)
        