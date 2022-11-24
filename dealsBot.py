from discord.ext import commands
import discord, json, logging, praw, asyncio, pprint, traceback, re

tokenJson = open('../tokens.json')
tokenData = json.load(tokenJson)
discordToken = tokenData['discord']
rClientId = tokenData['reddit']['client_id']
rClientSecret = tokenData['reddit']['client_secret']
rUserAgent = tokenData['reddit']['user_agent']    

# Reddit client to decouple deal-hunting logic
class reddit_hunter:

    dealFinder = praw.Reddit(client_id=rClientId,
                                  client_secret=rClientSecret,
                                  user_agent=rUserAgent)

    def __init__(self) -> None:
        self.channelToSub = {}

    def add_or_get_sub(self, channel, subreddit):
        if subreddit != '':
            self.channelToSub[channel] = self.subreddit_hunter(subreddit, self.dealFinder)
        return self.channelToSub.setdefault(channel, self.subreddit_hunter('GameDeals', self.dealFinder))

    def get_post_details_from_id(self, id: str) -> str:
        print(f"This was called. Id input was {id}")
        try: 
            submission = self.dealFinder.submission(id=id)
        except:
            traceback.print_exc()
        return f'''- Title: {str(submission.title)}
                   - Post Link: https://www.reddit.com{str(submission.permalink)}
                   - Upvote Ratio : {str(submission.upvote_ratio * 100)}%
                   - Flair : {str(submission.link_flair_text)}
                   - OP: {str(submission.author)}
                   - Total Awards: {str(submission.total_awards_received)}'''

    class subreddit_hunter():

        def __init__(self, subreddit, dealFinder) -> None:
            self.subreddit = subreddit
            sub: praw.models.Subreddit = dealFinder.subreddit(subreddit)
            self.commandToCall = {
                "hotdeals": self._get_game_deals_func(sub.hot),
                "risingdeals": self._get_game_deals_func(sub.rising),
                "topdeals": self._get_game_deals_func(sub.top),
                "controversialdeals": self._get_game_deals_func(sub.controversial)
            }

        def _get_game_deals(self, count: int, method) -> list[str]:
            resultList : list[str] = [f"[{submission.id}]{submission.title} : https://www.reddit.com{submission.permalink}" 
                                        for submission in method(limit=count)]
            # To check for available attributes of the submission object 
            # try: 
            #     oneSub = [submission for submission in method(limit=1)]
            #     testSub = oneSub[0]
            #     pprint.pprint(vars(testSub))
            # except: 
            #     traceback.print_exc()
            return resultList

        def _get_game_deals_func(self, method):
            return lambda count : self._get_game_deals(count, method)

        def is_valid_action(self, action: str):
            return action in self.commandToCall.keys()

        # TODO : Search method to build 
        def search_sub(self, query: str, time: str): 
            sub.search(query=query, time_filter=time)




#Cog for commands that require interaction with reddit_hunter
class reddit_commands(commands.Cog):
    
    rClient = reddit_hunter()

    def __init__(self, bot):
        self.bot = bot

    # Bot doesn't seem to have access to messages in the channel before it was
    # instanatiated. That means the internal message cache is only valid for n messages,
    # up to 1000, from the point in time the discord client was successfully
    # connected to. 
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        questionSeqs = {'\u2753', '\u2754', '\u2049\ufe0f'}
        # Thought I was being smart here but unicode-escape comparison against
        # reaction.emoji works so this was scuttled.
        # reactionSeq = reaction.emoji.encode('unicode-escape').decode('ASCII')
        # Check for emoji equality then query for post to get breakdown insights
        if reaction.emoji in questionSeqs:
            id = re.search(r"\[([A-Za-z0-9_]+)\]", reaction.message.content)
            result = self.rClient.get_post_details_from_id(id.group(1))
            channel = reaction.message.channel
            await channel.send(result)


    @commands.command()
    async def currentsub(self, ctx):
        channel: str = ctx.channel
        await ctx.reply(f"r/{self.rClient.add_or_get_sub(channel, '').subreddit}")

    @commands.command()
    async def select(self, ctx, arg):
        channel: str = ctx.channel
        self.rClient.add_or_get_sub(channel, arg)
        await ctx.reply(f" The subreddit set is now r/{self.rClient.channelToSub[channel].subreddit}")

    @commands.command()
    async def show(self, ctx, *args):
        channel: str = ctx.channel
        sub = self.rClient.add_or_get_sub(channel, '')
        try:
            if args[0].isdigit():
                result: list[str] = sub.commandToCall[args[1]](int(args[0]))
            else:
                result: list[str] = sub.commandToCall[args[0]](5)     
            await ctx.reply(f'r/{sub.subreddit} deals:')
            for post in result: #type: str
                titleUrl= post.split(' : ')
                print(titleUrl)
                # This works but breaks the question mark reaction feature
                embed = discord.Embed(
                    color = discord.Colour.dark_magenta()
                )
                embed.description = f'[{titleUrl[0]}]({titleUrl[1]})'
                await ctx.send(embed=embed)
        except:
            await ctx.reply(f"Please check that your chosen subreddit is spelled correctly and exists. Set again with $select")
            traceback.print_exc()
    
    @commands.command()
    async def search(self, ctx, *args):
        channel: str = ctx.channel
        sub = self.rClient.add_or_get-sub(channel, args[0])

discordHandler = logging.FileHandler(filename='./discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

activity = discord.Activity(name='for them dealz', type=discord.ActivityType.watching)
bot = commands.Bot(command_prefix='$', intents=intents, activity=activity)
bot.remove_command('help')

@bot.command()
async def help(ctx):
    await ctx.send("Please note the default subreddit is Game Deals. To set a new subreddit please use $select <subreddit_name> or $show <hotdeals|risingdeals|topdeals|controversialdeals>")

@bot.command()
async def hello(ctx):
    await ctx.reply(f"Are ya ready for some deals {ctx.author}?")

async def add_cog(bot, cog):
    await bot.add_cog(cog)

asyncio.run(add_cog(bot, reddit_commands(bot)))
bot.run(discordToken, log_handler=discordHandler)
