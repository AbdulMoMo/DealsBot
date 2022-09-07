from queue import Empty
import discord, json, logging, praw, datetime

tokenJson = open('../tokens.json')
tokenData = json.load(tokenJson)
discordToken = tokenData['discord']
rClientId = tokenData['reddit']['client_id']
rClientSecret = tokenData['reddit']['client_secret']
rUserAgent = tokenData['reddit']['user_agent']

class discord_listener(discord.Client):

    rClient = None

    async def on_ready(self):
        channel = self.get_channel(1012892793582129213)
        #await channel.send("!hotdeals")
        #await channel.send(datetime.datetime.now())
        self.rClient = reddit_hunter("GameDeals")
        await channel.send("Please note the default subreddit is Game Deals. To set a new subreddit please use !select<subreddit_name>")

    async def on_message(self, message):
        raw_message: str = message.content

        if raw_message.startswith("!select"):
            self._set_rClient(raw_message.split("!select", 1)[1])

        if not self.rClient.is_valid_action(raw_message):
            return

        result: list[str] = self.rClient.commandToCall[message.content](5)

        for post in result: #type: str
            await message.channel.send(post)
    
    def _set_rClient(self, subreddit):
        self.rClient = reddit_hunter(subreddit)

# Reddit client to decouple deal-hunting logic (WIP)
class reddit_hunter:

    dealFinder = praw.Reddit(client_id=rClientId,
                                  client_secret=rClientSecret,
                                  user_agent=rUserAgent)
    commandToCall = None

    def __init__(self, subreddit):
        sub: praw.models.SubredditHelper = self.dealFinder.subreddit(subreddit)
        self.commandToCall = {
            "!hotdeals": self._get_game_deals_func(sub.hot),
            "!risingdeals": self._get_game_deals_func(sub.rising),
            "!topdeals": self._get_game_deals_func(sub.top),
            "!controversialdeals": self._get_game_deals_func(sub.controversial)
        }

    def _get_game_deals(self, count: int, method) -> list[str]:
        #print("This method was actually called")
        resultList = [f"{submission.title} : {submission.url}" for submission in method(limit=count)]
        #print(resultList)
        return resultList

    def _get_game_deals_func(self, method):
        return lambda count : self._get_game_deals(count, method)

    def is_valid_action(self, action: str):
        return action in self.commandToCall.keys()


discordHandler = logging.FileHandler(filename='./discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

client = discord_listener(intents=intents)
client.run(discordToken, log_handler=discordHandler)



