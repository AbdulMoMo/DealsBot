import discord, json, logging, praw, asyncio, datetime

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

    def cleanGameDeals(self, count, method):
        print("This method was actually called")
        resultList = []
        for submission in method(limit=count):
            result = f"{submission.title} : {submission.url}"
            print(result)
            resultList.append(result)
        return resultList

    def getCleanGameDealsFunc(self, method):
        return lambda count : self.cleanGameDeals(count, method)

    async def createMap(self): 
        sub = self.dealFinder.subreddit("GameDeals")
        self.commandToCall = {
            "!hotdeals": self.getCleanGameDealsFunc(sub.hot),
            "!risingdeals": self.getCleanGameDealsFunc(sub.rising),
            "!topdeals": self.getCleanGameDealsFunc(sub.top),
            "!controversialdeals": self.getCleanGameDealsFunc(sub.controversial)
        }
    
    # def getFunction(self):
    #     lambda count : self.cleanGameDeals(count, sub.hot)

    async def on_ready(self):
        channel = self.get_channel(1012892793582129213)
        await channel.send("!hotdeals")
        await channel.send(datetime.datetime.now())


    async def on_message(self, message):
        if message.content not in self.commandToCall:
            return

        result = self.commandToCall[message.content](5)

        for post in result:
            await message.channel.send(post)


discordHandler = logging.FileHandler(filename='./discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

client = hunter(intents=intents)
asyncio.run(client.createMap())
client.run(discordToken, log_handler=discordHandler)



