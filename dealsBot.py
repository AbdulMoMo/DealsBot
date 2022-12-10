import discord
from discord.ext import commands
import logging
import asyncio
import traceback
import re
import os 
import pprint

import redditClientImpl

# Storing API keys for Discord
discordToken = os.environ.get('DISCORD_TOKEN')

# Class to encapsulate discord bot commands that interact with the reddit client (as a child of a Cog for discord.ext)
class reddit_commands(commands.Cog):
    
    rClient = redditClientImpl.reddit_hunter()

    # Allow list to reduce invocations of rClient.sub_exists()
    ALLOW_LIST = {
        "gamedeals",
        "buildapcsales",
        "games",
        "hardwareswap",
        "gamedealsmeta",
    }

    DEFAULT_COUNT = 5

    UPPER_COUNT = 10

    BOT_ID = 'DealzBot#1632'

    THREAD_ARCHIVE_DURATION = 60

    # Possible question emojis I could use: 
    # '\u2753', '\u2754', '\u2049\ufe0f'
    QUESTION_EMOJI = '\u2753'

    # Constructor to init reddit_commands
    # Inputs: bot (discord.Ext.bot)
    # Outputs: None 
    # Exceptions None 
    def __init__(self, bot):
        self.bot = bot

    # Function to provide help information on reddit bot commands
    # Inputs: ctx (discord.ext.Commands.Context)
    # Outputs: None
    # Exceptions: None
    @commands.command()
    async def reddithelp(self, ctx):
        # Cursed formatting but this works. Need to fix
        helpRef: dict[str, str] = {
            "$select": '''To select a subreddit. This is set at the channel level. The default subreddit is r/GameDeals.
                          Example usage: `$select buildapcsales`''',
            "$show": '''For listing posts by hot/top/rising/controversial by n number of posts.
                        Example usage: 
                        ```
                        $show topdeals 
                        $show controversialdeals
                        $show risingdeals
                        $show hotdeals
                        $show 4 hotdeals```
                        *The default number of posts to be output is 5.
                    ''',
            f"{self.QUESTION_EMOJI}": '''React to one of DealzBot's $show replies with the above emoji to get additional
                                         information on the given reddit post. DealzBot will react to every valid message
                                         with this emoji to indicate when this feature can be used.''',
            "$search": '''For searching a subreddit based on a given time range and query.
                        Valid time ranges are: 'all', 'day', 'hour', 'month', 'week' or 'year'. Default is 'all'
                        Example usage: 
                        ```
                        $search week destiny 
                        $search aoc
                        $search hour minecraft```
                        *The current (hard) limit for search results is 5.
                    '''
        }
        embed: discord.Embed = self._create_field_embed(helpRef, "DealzBot User Guide", "https://github.com/AbdulMoMo/DealsBot/blob/main/README.md")
        await ctx.reply(embed=embed)

    # Function to trigger post breakdown msg when user reacts to a bot post
    # Inputs: reaction (discord.Emoji), user (discord.User)
    # Outputs: None
    # Exceptions: None
    # Note: Client doesn't have to have access to messages in the channel before it was
    # instanatiated. That means the internal message cache is only valid for n messages,
    # up to 1000, from the point in time the discord client was up. 
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Used below statement to get unicode escape sequence for question mark
        # emojis.
        # reactionSeq = reaction.emoji.encode('unicode-escape').decode('ASCII')

        # Check if: 1) Message author is not DealzBot or 2) If the reaction author is Dealzbot
        # 
        # In case #1, this would mean DealzBot would try, and fail, to search for a reddit post
        # on ANY reaction on a message in the server. So not good. 
        # 
        # In case #2, this would invoke additional coroutines that bog down 
        # execution time for the show command, and also it looks bad. So we don't want
        # that.
        if str(reaction.message.author) != self.BOT_ID or str(user) == self.BOT_ID:
            return

        # Check for emoji equality then query for post to get breakdown insights
        if reaction.message.embeds:
            em = reaction.message.embeds[0]
            if reaction.emoji == self.QUESTION_EMOJI:
                result = '''Sorry! I could not pull this post's details from Reddit!
                    Try again or give up! :)'''
                id : str = re.search(r"\[([A-Za-z0-9_]+)\]", em.description).group(1)
                result : dict[str, str] = self.rClient.get_post_details_from_id(id)
                if result: 
                    embed: discord.Embed = self._create_field_embed(result, "Deal Breakdown (Link)", em.url)
                    await reaction.message.reply(embed=embed)
                    return                    
                await reaction.message.reply(result)
            else:
                return

    # Function to reply to user with the current subreddit for a channel
    # Inputs: ctx (discord.ext.commands.Context)
    # Outputs: None
    # Exceptions None
    @commands.command()
    async def currentsub(self, ctx):
        channel: str = ctx.channel
        await ctx.reply(f"r/{self.rClient.add_or_get_sub(channel, '').subreddit}")

    # Function to select a subreddit for the discord channel
    # Inputs: ctx (discord.ext.Commands.Context), arg (str) - command keyword argument
    # Ouputs: None
    # Exceptions: None
    @commands.command()
    async def select(self, ctx, arg):
        channel: str = ctx.channel
        userInput: str = arg.lower()
        if userInput not in self.ALLOW_LIST and not self.rClient.sub_exists(userInput):
            await ctx.reply('''Sorry! Either the subreddit is marked as NSFW (Over 18) or it does not exist!''')
        else:
            # Cache subreddit not already included in ALLOW_LIST to reduce rClient.sub_exists() calls
            self.ALLOW_LIST.add(userInput)
            self.rClient.add_or_get_sub(channel, arg)
            await ctx.reply(f"The subreddit set is now r/{self.rClient.channelToSub[channel].subreddit}")

    # Function to pull post results based on top/hot/rising/controversial
    # Inputs: ctx (discord.ext.Commands.Context), args (List[str])
    # Outputs: None
    # Exceptions TBD
    @commands.command()
    async def show(self, ctx, *args):
        channel: str = ctx.channel
        sub: redditClientImpl.reddit_hunter.subreddit_hunter = self.rClient.add_or_get_sub(channel, '')
        # Questionable boolean zen below??? TODO: Review this conditional sequence
        # for optimizations.
        try:
            # For show expect one or two args:
            # $show 5 hotdeals
            # $show hotdeals
            # args[0] = number OR commandToCall value
            # args[1] (if exists) = commandToCall value
            countOrCommand: str = args[0]
            isNumInput: bool = countOrCommand.isdigit()

            # Should correspond to commandToCall value
            if len(args) > 1:
                subFilter = args[1]

            if isNumInput and int(countOrCommand) <= self.UPPER_COUNT:
                result : dict[str, str] = sub.commandToCall[subFilter](int(countOrCommand))
            elif isNumInput and int(countOrCommand) > self.UPPER_COUNT:
                await ctx.reply(f"Please pick an output amount <= {self.UPPER_COUNT}!")
                return
            else:
                result : dict[str, str] = sub.commandToCall[countOrCommand](self.DEFAULT_COUNT)
            # Relic before thread, holding here for now in case there is a breaking change with threads I missed    
            # await ctx.reply(f'r/{sub.subreddit} deals:')
            # for post in result.keys():
            #     embed = self._create_general_embed(post, result)
            #     await ctx.send(embed=embed)
            await self._make_deals_thread(result, ctx.message, sub, True)
        except:
            await ctx.reply(f"Please check that your chosen subreddit is spelled correctly and exists. Set again with $select")
            traceback.print_exc()
    
    # Function to search a subreddit based on a query and time range
    # Inputs: ctx (discord.ext.Commands.Context), args (List[str])
    # Outputs: None
    # Exceptions: None
    @commands.command()
    async def search(self, ctx, *args):
        channel: str = ctx.channel
        sub: redditClientImpl.reddit_hunter.subreddit_hunter = self.rClient.add_or_get_sub(channel, '')
        if len(args) > 1:
            result = sub.search_sub(args[0], args[1])
        else:
            result = sub.search_sub("day", args[0])
        if result:
            await self._make_deals_thread(result, ctx.message, sub, True)
        else:
            await ctx.reply("No results in this time range! Try a different one")

    # Function to create a general discord embed for a bot message
    # Inputs: post (str) - post title, result (dict) - varies
    # Outputs: embed (discord.Embed)
    # Exceptions: None
    def _create_general_embed(self, post, result) -> discord.Embed:
        embed: discord.Embed = discord.Embed(
            color=discord.Colour.dark_magenta(),
            url=f'{result[post]}'
        )
        embed.description = f'[{post}]({result[post]})'
        return embed

    # Function to create a general discord embed for a bot message
    # Inputs: post (str) - post title, result (dict) - varies
    # Outputs: embed (discord.Embed)
    # Exceptions: None
    def _create_field_embed(self, result, title, url) -> discord.Embed:
        embed: discord.Embed = discord.Embed(
            color=discord.Colour.brand_green(),
            title=title,
            url=url
        )
        for field in result.keys():
            embed.add_field(name=f"**{field}**", value=f"{result[field]}", inline=False)
        return embed

    # Function to create thread (ex. $search and $show) for reddit deals
    # Inputs: result - dict[str, str], message - discord.Message, sub - redditClientImpl.reddit_hunter.subreddit_hunter
    # Outputs: None
    # Exceptions: None
    async def _make_deals_thread(self, 
                                 result: dict[str, str], 
                                 message: discord.Message, 
                                 sub: redditClientImpl.reddit_hunter.subreddit_hunter,
                                 isBasic: bool):
        try: 
            dealsThread: discord.Thread = await message.create_thread(name=f'{sub.subreddit} Deals:', auto_archive_duration=self.THREAD_ARCHIVE_DURATION)
        except discord.HTTPException: 
            # Could not create thread in this case. TODO: when I add logging need to emit error here
            return
        for post in result.keys():
            embed: discord.Embed = self._create_general_embed(post, result)
            threadMessage: discord.Message = await dealsThread.send(embed=embed)
            if isBasic: 
                await threadMessage.add_reaction(self.QUESTION_EMOJI)

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
async def add_cog(bot, cog):
    await bot.add_cog(cog)

# Need asyncio to add cog 
asyncio.run(add_cog(bot, reddit_commands(bot)))
bot.run(discordToken, log_handler=discordHandler)