import discord
from discord.ext import commands
import json
import logging
import praw
import asyncio
import pprint
import traceback
import re
from datetime import datetime
from prawcore import NotFound

# logging.basicConfig(filename="botLogger.log",
#                     format='%(asctime)s %(message)s',
#                     filemode='w')
# blogger = logging.getLogger()
# blogger.setLevel(logging.DEBUG)

# Storing API keys for Discord and Reddit 
tokenJson = open('../tokens.json')
tokenData = json.load(tokenJson)
discordToken = tokenData['discord']
rClientId = tokenData['reddit']['client_id']
rClientSecret = tokenData['reddit']['client_secret']
rUserAgent = tokenData['reddit']['user_agent']    

# Class to encapsulate interaction with the Reddit client (PRAW)
class reddit_hunter:

    # Reddit client object
    dealFinder = praw.Reddit(client_id=rClientId,
                             client_secret=rClientSecret,
                             user_agent=rUserAgent)

    # Constructor for reddit_hunter
    # Inputs: None
    # Outputs: None
    # Exceptions: None
    def __init__(self) -> None:
        self.channelToSub = {}

    # Function to check if a subreddit exists before invoking add_or_get_sub
    # Inputs: subreddit (str) to search for
    # Outputs: True/False
    # Exceptions: NotFound (expected when subreddit is not found)
    def sub_exists(self, subreddit):
        exists = True
        try:
            self.dealFinder.subreddits.search_by_name(subreddit, exact=True)
        except NotFound:
            exists = False
        return exists

    # Function to pull a subreddit_hunter for the given discord channel
    # Inputs: Channel (str) - Discord Channel Id, Subreddit (str) - Subreddit name
    # Outputs: Subreddit Hunter (subreddit_hunter)
    # Exceptions: None 
    def add_or_get_sub(self, channel: str, subreddit: str):
        if subreddit != '':
            self.channelToSub[channel] = self.subreddit_hunter(subreddit, self.dealFinder)
        return self.channelToSub.setdefault(channel, self.subreddit_hunter('GameDeals', self.dealFinder))

    # Function to provide detailed information on a specific Reddit submission 
    # Inputs: id (str) for a reddit submission
    # Outputs: Submission details (dict)
    # Exceptions: None (an invalid id will return an empty result)
    def get_post_details_from_id(self, id: str) -> str:
        try: 
            submission = self.dealFinder.submission(id=id)
            # To get available attributes of a submission,
            # see https://praw.readthedocs.io/en/latest/getting_started/quick_start.html#determine-available-attributes-of-an-object
            # pprint.pprint(vars(submission))
        except:
            traceback.print_exc()
            return None
        # Datetime conversion seems to slow down this func proc time
        return {'Title': f'{str(submission.title)}', 
                'Spoiler': f'{str(submission.spoiler)}',
                'Upvote Ratio': f'{str(submission.upvote_ratio * 100)}%', 
                'Flair': f'{str(submission.link_flair_text)}',
                'OP': f'{str(submission.author)}', 
                'Total Awards': f'{str(submission.total_awards_received)}',
                'Created on (UTC)': f'{str(datetime.fromtimestamp(submission.created))}'
                }

    # Child class to encpasulate specific subreddit operations
    class subreddit_hunter():

        # Constructor for subreddit_hunter
        # Inputs: subreddit (str), dealFinder (praw.Reddit)
        # Outputs: None
        # Excpetions: None
        def __init__(self, subreddit, dealFinder) -> None:
            self.subreddit = subreddit
            try:
                self.sub: praw.models.Subreddit = dealFinder.subreddit(subreddit)
            except:
                traceback.print_exc()
            self.commandToCall = {
                "hotdeals": self._get_game_deals_func(self.sub.hot),
                "risingdeals": self._get_game_deals_func(self.sub.rising),
                "topdeals": self._get_game_deals_func(self.sub.top),
                "controversialdeals": self._get_game_deals_func(self.sub.controversial)
            }

        # Function for creating refs of posts + post links
        # Inputs: count (int) -- for # of results, method (praw.models.Subreddit)
        # Outputs: result (dict) of posts + post links
        # Exceptions: None
        def _get_game_deals(self, count: int, method) -> dict[str, str]:
            try: 
                result = [(f"[{submission.id}]{submission.title}", f"https://www.reddit.com{submission.permalink}")
                        for submission in method(limit=count)]
            except: 
                traceback.print_exc()
            return dict(result)

        # Function to trigger _get_game_deals()
        # Inputs: method (praw.models.Subreddit)
        # Outputs: Invocation result of _get_game_deals
        # Exceptions: None
        def _get_game_deals_func(self, method):
            return lambda count : self._get_game_deals(count, method)

        # Function to check if input is a valid subreddit action 
        # Inputs: action (str) - being checked
        # Outputs: True/False (boolean)
        # Excpetions: None 
        def is_valid_action(self, action: str):
            return action in self.commandToCall.keys()

        # Function to search a subreddit based on a given query + time range
        # Inputs: time (str) - time range, query (str) - query to search 
        # Outputs: Reference of posts + post links
        # Exceptions: TBD
        # TODO : Want to see if I can factor this so it can follow call
        # pattern for the dict/lambda invocation
        def search_sub(self, time: str, query: str): 
            try:
                result = [(f"[{submission.id}]{submission.title}", f"https://www.reddit.com{submission.permalink}")
                        for submission in self.sub.search(query=query, time_filter=time, limit=5)]
            except:
                traceback.print_exc()
            return dict(result)
        




# Class to encapsulate discord bot commands that interact with the reddit client (as a child of a Cog for discord.ext)
class reddit_commands(commands.Cog):
    
    rClient = reddit_hunter()

    # Frozenset for O(1) lookup 
    # Used this thread to create a foundational deny list: https://www.reddit.com/r/AskReddit/comments/6rjqmk/what_is_the_worst_subreddit_youve_come_across/
    denyList =frozenset((
        "gonewild",
        "incels",
        "truecels",
        "poop",
        "imgoingtohellforthis",
        "selffuck",
        "oldladiesbakingpies",
        "letsnotmeet"
    ))

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
            "\u2753 or \u2754 or \u2049\ufe0f": '''React to one of DealzBot's messages with the above emojis to get additional
                                                   information on the given reddit post.''',
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
        embed = self._create_field_embed(helpRef, "DealzBot User Guide", "https://github.com/AbdulMoMo/DealsBot/blob/main/README.md")
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
        questionSeqs = {'\u2753', '\u2754', '\u2049\ufe0f'}
        channel = reaction.message.channel
        result = '''Sorry! I could not pull this post's details from Reddit!
                    Try again or give up! :)'''
        # Check for emoji equality then query for post to get breakdown insights
        if reaction.message.embeds:
            em = reaction.message.embeds[0]
            if reaction.emoji in questionSeqs:
                id : str = re.search(r"\[([A-Za-z0-9_]+)\]", em.description).group(1)
                result : dict[str, str] = self.rClient.get_post_details_from_id(id)
                if result: 
                    embed = self._create_field_embed(result, "Deal Breakdown (Link)", em.url)
                    await reaction.message.reply(embed=embed)
                    return                    
        await reaction.message.reply(result)

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
        if userInput in self.denyList:
            await ctx.reply("NO.")
        elif not self.rClient.sub_exists(userInput):
            await ctx.reply('''Sorry! This subreddit does not exist! Or the author of this commit should git gud.''')
        else:
            self.rClient.add_or_get_sub(channel, arg)
            await ctx.reply(f"The subreddit set is now r/{self.rClient.channelToSub[channel].subreddit}")

    # Function to pull post results based on top/hot/rising/controversial
    # Inputs: ctx (discord.ext.Commands.Context), args (List[str])
    # Outputs: None
    # Exceptions TBD
    @commands.command()
    async def show(self, ctx, *args):
        channel: str = ctx.channel
        sub = self.rClient.add_or_get_sub(channel, '')
        # Questionable boolean zen below??? TODO: Review this conditional sequence
        # for optimizations.
        try:
            if args[0].isdigit() and int(args[0]) <= 10:
                result : dict[str, str] = sub.commandToCall[args[1]](int(args[0]))
            elif args[0].isdigit() and int(args[0]) > 10:
                await ctx.reply("Please pick an output amount <= 10!")
                return
            else:
                result : dict[str, str] = sub.commandToCall[args[0]](5)    
            await ctx.reply(f'r/{sub.subreddit} deals:')
            for post in result.keys():
                embed = self._create_general_embed(post, result)
                await ctx.send(embed=embed)
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
        sub = self.rClient.add_or_get_sub(channel, '')
        if len(args) > 1:
            result = sub.search_sub(args[0], args[1])
        else:
            result = sub.search_sub("day", args[0])
        if result:
            for post in result.keys():
                embed = self._create_general_embed(post, result)
                await ctx.reply(embed=embed)
        else:
            await ctx.reply("No results in this time range! Try a different one")

    # Function to create a general discord embed for a bot message
    # Inputs: post (str) - post title, result (dict) - varies
    # Outputs: embed (discord.Embed)
    # Exceptions: None
    def _create_general_embed(self, post, result) -> discord.Embed:
        embed = discord.Embed(
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
        embed = discord.Embed(
            color=discord.Colour.brand_green(),
            title=title,
            url=url
        )
        for field in result.keys():
            embed.add_field(name=f"**{field}**", value=f"{result[field]}", inline=False)
        return embed

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
