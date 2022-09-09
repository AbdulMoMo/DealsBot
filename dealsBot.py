from queue import Empty
from discord.ext import tasks, commands
import discord, json, logging, praw, asyncio

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

    def add_or_get_sub(self, channel, subreddit, isShow):
        if subreddit != '':
            self.channelToSub[channel] = self.subreddit_hunter(subreddit, self.dealFinder)
        elif not isShow:
            self.channelToSub[channel] = self.subreddit_hunter('GameDeals', self.dealFinder) 
        return self.channelToSub[channel]

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
            resultList = [f"{submission.title} : {submission.url}" for submission in method(limit=count)]
            return resultList

        def _get_game_deals_func(self, method):
            return lambda count : self._get_game_deals(count, method)

        def is_valid_action(self, action: str):
            return action in self.commandToCall.keys()



class reddit_commands(commands.Cog):
    
    rClient = reddit_hunter()

    def __init__(self, bot):
        self.bot = bot

    def _set_or_get_rClient(self, channel, subreddit, isShow):
        return self.rClient.add_or_get_sub(channel, subreddit, isShow)
    
    @commands.command()
    async def currentsub(self, ctx):
        channel: str = ctx.channel
        await ctx.send(f"r/{self.rClient.add_or_get_sub(channel, '', False).subreddit}")

    @commands.command()
    async def select(self, ctx, arg):
        channel: str = ctx.channel
        self._set_or_get_rClient(channel, arg, False)
        await ctx.send(f" The subreddit set is now r/{self.rClient.channelToSub[channel].subreddit}")
    
    @commands.command()
    async def show(self, ctx, type):
        channel: str = ctx.channel
        sub = self._set_or_get_rClient(ctx.channel, '', True)
        try:
            result: list[str] = sub.commandToCall[type](5)
            # print(result)
            for post in result: #type: str
                await ctx.send(post)
        except:
            await ctx.send(f"Please check that r/{self.rClient.channelToSub[channel].subreddit} is spelled correctly and exists. Set again with $select")

discordHandler = logging.FileHandler(filename='./discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

activity = discord.Activity(name='for them dealz', type=discord.ActivityType.watching)
bot = commands.Bot(command_prefix='$', intents=intents, activity=activity)
bot.remove_command('help')

@bot.command()
async def help(ctx):
    await ctx.send("Please note the default subreddit is Game Deals. To set a new subreddit please use !select<subreddit_name>.")

async def add_cog(bot, cog):
    await bot.add_cog(cog)

asyncio.run(add_cog(bot, reddit_commands(bot)))
bot.run(discordToken, log_handler=discordHandler)
