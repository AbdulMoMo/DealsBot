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

# Function to give help information
# Inputs: ctx (discord.ext.Commands.Context)
# Outputs: None
# Exceptions: None
# TODO: Make a proper help function within the reddit_commands class that replies to user with commands guide
@bot.command()
async def help(ctx):
    await ctx.reply("Please note the default subreddit is r/GameDeals. For reddit specific commands, use `$reddithelp` to get more information!")

# Function to say hello to user
# Inputs: ctx (discord.ext.Commands.Context)
# Outputs: None
# Exceptions: None
@bot.command()
async def hello(ctx):
    await ctx.reply(f"Are ya ready for some deals {ctx.author}?")

# Function to add cog to discord bot 
# Inputs: bot (discord.Bot)
# Outputs: None
# Exceptions: None 
async def add_cogs(bot):
    await bot.add_cog(redditCog.reddit_commands(bot))
    await bot.add_cog(hltbCog.hltb_commands(bot))

# Need asyncio to add cog 
asyncio.run(add_cogs(bot))
bot.run(discordToken, log_handler=discordHandler)