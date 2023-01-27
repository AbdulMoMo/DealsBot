import discord
from discord.ext import commands
import logging
import asyncio
import traceback
import re
import os 
import pprint

import cogs.redditCog as redditCog
import cogs.hltbCog as hltbCog

# Storing API keys for Discord
discordToken = os.environ.get('DISCORD_TOKEN')

# Create discord longging handler and intents
discordHandler = logging.FileHandler(filename='./discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

# set bot configuration and activity as well as remove default help to create custom help
activity = discord.Activity(name='for them dealz', type=discord.ActivityType.watching)
bot = commands.Bot(command_prefix='$', intents=intents, activity=activity)
bot.remove_command('help')

@bot.command()
async def help(ctx):
    """Function to give help information

    Args:
        ctx (discord.ext.Commands.Context): Discord context for command invocation
    """
    await ctx.reply("Please note the default subreddit is r/GameDeals. For reddit specific commands, use `$reddithelp` to get more information!")

@bot.command()
async def hello(ctx):
    """Function to say hello to user

    Args:
        ctx (discord.ext.Commands.Context): Discord context for command invocation
    """
    await ctx.reply(f"Are ya ready for some deals {ctx.author}?")

async def add_cogs(bot):
    """Function to add cog to discord bot

    Args:
        bot (discord.Bot)
    Exceptions:
        None
    """
    await bot.add_cog(redditCog.reddit_commands(bot))
    await bot.add_cog(hltbCog.hltb_commands(bot))


# Need asyncio to add cog 
asyncio.run(add_cogs(bot))
bot.run(discordToken, log_handler=discordHandler)