import discord, json, logging, asyncpraw, asyncio

tokenJson = open('../tokens.json')
tokenData = json.load(tokenJson)
discordToken = tokenData['discord']
rClientId = tokenData['reddit']['client_id']
rClientSecret = tokenData['reddit']['client_secret']
rUserAgent = tokenData['reddit']['user_agent']



class hunter(discord.Client):

    commandToCall = None
    dealFinder = asyncpraw.Reddit(client_id=rClientId,
                    client_secret=rClientSecret,
                    user_agent=rUserAgent)

    async def cleanGameDeals(self, count, method):
        print("This method was actually called")
        async for submission in method(limit=count):
            return f"{submission.title} : {submission.url}"

    async def createMap(self): 
        sub = await self.dealFinder.subreddit("GameDeals")
        self.commandToCall = {
            "!hotdeals": lambda : self.cleanGameDeals(5, sub.hot),
            "!risingdeals": lambda : self.cleanGameDeals(5, sub.rising),
            "!topdeals": self.cleanGameDeals(5, sub.top),
            "!controversialdeals": self.cleanGameDeals(5, sub.controversial)
        }
    
    # def getFunction(self):
    #     lambda count : self.cleanGameDeals(count, sub.hot)

    async def on_ready(self):
        channel = self.get_channel(1012892793582129213)
        await channel.send("!hotdeals")


    async def on_message(self, message):
        if message.content not in self.commandToCall:
            await message.channel.send("Command does not exist!")

        result = await self.commandToCall[message.content]()
        await message.channel.send(result)


discordHandler = logging.FileHandler(filename='../discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

client = hunter(intents=intents)
asyncio.run(client.createMap())
client.run(discordToken, log_handler=discordHandler)



