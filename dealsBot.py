from queue import Empty
import discord, json, logging, praw

tokenJson = open('../tokens.json')
tokenData = json.load(tokenJson)
discordToken = tokenData['discord']
rClientId = tokenData['reddit']['client_id']
rClientSecret = tokenData['reddit']['client_secret']
rUserAgent = tokenData['reddit']['user_agent']

class discord_listener(discord.Client):

    rClient = None

    async def on_ready(self):
        self.rClient = reddit_hunter("GameDeals")

    async def on_message(self, message):
        raw_message: str = message.content

        if raw_message == "!helpDealzBot" or raw_message.startswith("!help"):
            await message.channel.send("Please note the default subreddit is Game Deals. To set a new subreddit please use !select<subreddit_name>.")

        if raw_message == "!currentsub":
            await message.channel.send(f"r/{self.rClient.subreddit}")

        if raw_message.startswith("!select"):
            self._set_rClient(raw_message.split("!select", 1)[1])
           
        
        command = None
        count = 5

        if raw_message[0] == "!" and raw_message[1].isdigit():
            command = raw_message[:1] + raw_message[2:]
            count = int(raw_message[1])
        else:
            command: str = raw_message

        if not self.rClient.is_valid_action(command):
            return
        
        try:
            result: list[str] = self.rClient.commandToCall[command](count)
        except:
            await message.channel.send(f"Please check that r/{self.rClient.subreddit} is spelled correctly and exists. Set again with !select")

        for post in result: #type: str
            await message.channel.send(post)
    
    def _set_rClient(self, subreddit):
        self.rClient = reddit_hunter(subreddit)
        

# Reddit client to decouple deal-hunting logic
class reddit_hunter:

    dealFinder = praw.Reddit(client_id=rClientId,
                                  client_secret=rClientSecret,
                                  user_agent=rUserAgent)
    commandToCall = None

    subreddit = None

    def __init__(self, subreddit):
        self.subreddit = subreddit
        sub: praw.models.Subreddit = self.dealFinder.subreddit(subreddit)
        self.commandToCall = {
            "!hotdeals": self._get_game_deals_func(sub.hot),
            "!risingdeals": self._get_game_deals_func(sub.rising),
            "!topdeals": self._get_game_deals_func(sub.top),
            "!controversialdeals": self._get_game_deals_func(sub.controversial)
        }

    def _get_game_deals(self, count: int, method) -> list[str]:
        resultList = [f"{submission.title} : {submission.url}" for submission in method(limit=count)]
        return resultList

    def _get_game_deals_func(self, method):
        return lambda count : self._get_game_deals(count, method)

    def is_valid_action(self, action: str):
        return action in self.commandToCall.keys()


discordHandler = logging.FileHandler(filename='./discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

activity = discord.Activity(name='for them dealz', type=discord.ActivityType.watching)
client = discord_listener(intents=intents, activity=activity)
client.run(discordToken, log_handler=discordHandler)