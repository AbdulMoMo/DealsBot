import discord, json, logging, praw, datetime

tokenJson = open('../tokens.json')
tokenData = json.load(tokenJson)
discordToken = tokenData['discord']
rClientId = tokenData['reddit']['client_id']
rClientSecret = tokenData['reddit']['client_secret']
rUserAgent = tokenData['reddit']['user_agent']

class hunter(discord.Client):

    commandToCall = None
    dealFinder = praw.Reddit(client_id=rClientId,
                                  client_secret=rClientSecret,
                                  user_agent=rUserAgent)

    def __init__(self, *, intents, **options) -> None:
        super().__init__(intents=intents, **options)
        sub: praw.models.SubredditHelper = self.dealFinder.subreddit("GameDeals")
        self.commandToCall = {
            "!hotdeals": self._get_game_deals_func(sub.hot),
            "!risingdeals": self._get_game_deals_func(sub.rising),
            "!topdeals": self._get_game_deals_func(sub.top),
            "!controversialdeals": self._get_game_deals_func(sub.controversial)
        }

    def _get_game_deals(self, count: int, method) -> list[str]:
        print("This method was actually called")
        resultList = [f"{submission.title} : {submission.url}" for submission in method(limit=count)]
        print(resultList)
        return resultList

    def _get_game_deals_func(self, method):
        return lambda count : self._get_game_deals(count, method)

    def is_valid_action(self, action: str):
        return action in self.commandToCall.keys()

    async def on_ready(self):
        channel = self.get_channel(1012892793582129213)
        await channel.send("!hotdeals")
        await channel.send(datetime.datetime.now())


    async def on_message(self, message):
        raw_message: str = message.content
        if not self.is_valid_action(raw_message):
            return

        result: list[str] = self.commandToCall[message.content](5)

        for post in result: #type: str
            await message.channel.send(post)


discordHandler = logging.FileHandler(filename='./discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

client = hunter(intents=intents)
client.run(discordToken, log_handler=discordHandler)



