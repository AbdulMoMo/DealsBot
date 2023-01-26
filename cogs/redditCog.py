import discord
from discord.ext import commands
from discord.ext import tasks
import logging
import asyncio
import traceback
import re
import pprint

import clients.redditClientImpl as redditClientImpl
import utils.discordUtils as discordUtils

# Class to encapsulate discord bot commands that interact with the reddit client (as a child of a Cog for discord.ext)
class reddit_commands(commands.Cog):
    
    rClient = redditClientImpl.reddit_hunter()

    # Allow list to reduce invocations of rClient.sub_exists()
    ALLOW_LIST: set[str] = {
        "gamedeals",
        "buildapcsales",
        "games",
        "hardwareswap",
        "gamedealsmeta",
    }

    ID_TO_GUILD = dict()

    LOOP_SUBS: set[str] = {
        "gamedeals",
        "buildapcsales"
    }

    DEFAULT_COUNT: int = 5

    UPPER_COUNT: int = 10

    BOT_ID: str = 'DealzBot#1632'

    DEALS_REPORT_INTERNAL_LOOP_COUNT: int = -1

    LOOP_INTERVAL: float = 8.0

    # Possible question emojis I could use: 
    # '\u2753', '\u2754', '\u2049\ufe0f'
    QUESTION_EMOJI = '\u2753'

    # Constructor to init reddit_commands
    # Inputs: bot (discord.Ext.bot)
    # Outputs: None 
    # Exceptions None 
    def __init__(self, bot):
        self.bot = bot

    async def cog_unload(self):
        self.deals_report.cancel()
        try: 
            await self.deals_report()
        except asyncio.CancelledError:
            print("Report task successfully cancelled.")

    @commands.command()
    async def reddithelp(self, ctx):
        """Function to provide help information on reddit bot commands

        Args:
            ctx (discord.ext.Commands.Context): required arg for command
        Exceptions:
            None
        """
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
                        Valid time ranges are: `all`, `day`, `hour`, `month`, `week` or `year`. Default is `day`
                        Example usage: 
                        ```
                        $search week destiny 
                        $search aoc
                        $search hour minecraft```
                        *The current (hard) limit for search results is 5.
                    ''',
            "$currentsub": '''Displays the current subreddit for the channel.''',
            "$notifyenable": f'''Enables notifications for the current channel. DealzBot will send notifications on a regular interval every 
                            {self.LOOP_INTERVAL} hours from deals oriented subreddits. This setting is set at the channel level.''',
            "$notifydisable": f'''Disables notifications for the current channel. This setting is set at the channel level.''',

        }
        embed: discord.Embed = discordUtils.create_field_embed(helpRef, "DealzBot User Guide", "https://github.com/AbdulMoMo/DealsBot/blob/main/README.md")
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
            em: discord.Embed = reaction.message.embeds[0]
            if reaction.emoji == self.QUESTION_EMOJI:
                result: str = '''Sorry! I could not pull this post's details from Reddit!
                    Try again or give up! :)'''
                id: str = re.search(r"\[([A-Za-z0-9_]+)\]", em.description).group(1)
                result: dict[str, str] = self.rClient.get_post_details_from_id(id)
                if result: 
                    embed: discord.Embed = discordUtils.create_field_embed(result, "Deal Breakdown (Link)", em.url)
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
            await ctx.reply("Sorry! Either the subreddit is marked as NSFW (Over 18) or it does not exist!")
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
            # For show expect one or two args in 'happy' cases:
            # $show 5 hotdeals
            # $show hotdeals
            # args[0] = number OR commandToCall value
            # args[1] (if exists) = commandToCall value
            countOrCommand: str = args[0]
            isNumInput: bool = countOrCommand.isdigit()

            # Should correspond to commandToCall value
            if len(args) > 1:
                subFilter: str = args[1]

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
            #     embed = discordUtils.create_general_embed(post, result)
            #     await ctx.send(embed=embed)
            await discordUtils.make_thread(result, ctx.message, f'{sub.subreddit} Deals', True)
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
        # For search expect one or two args in 'happy' cases:
        # $search day game
        # $search game
        # args[0] = time_filter OR search query
        # args[1] (if exists) = search query
        timeFilterOrQuery: str = args[0]
        if len(args) > 1:
            query: str = args[1]
            result: dict[str, str] = sub.search_sub(timeFilterOrQuery, query)
        else:
            result: dict[str, str] = sub.search_sub("day", timeFilterOrQuery)
        if result:
            await discordUtils.make_thread(result, ctx.message, f'{sub.subreddit} Deals', True)
        else:
            await ctx.reply("No results in this time range! Double check your usage with $reddithelp or try a different query.")
    
    # Parent function for enabling/disabling notifications on a given discord channel
    # Inputs: ctx (discord.ext.Commands.Context)
    # Outputs: None
    # Exceptions: None
    @commands.group()
    async def notify(self, ctx):
        # Check if one of the subcommands was invoked
        if ctx.invoked_subcommand is None:
            await ctx.reply(
                "Use either `$notify enable` to enable notifications for this channel or `$notify disable` to disable notifications for this channel.")
        pass 

    # Child function for enabling notifications on a given discord channel
    # Inputs: ctx (discord.ext.Commands.Context)
    # Outputs: None
    # Exceptions: None
    @notify.command()
    async def enable(self, ctx):
        channel_id: int = ctx.channel.id
        guild: discord.Guild = ctx.guild 
        self.ID_TO_GUILD[channel_id] = guild
        await ctx.reply(f"Notifications for {ctx.channel.name} enabled.")

    # Child function for disabling notifications on a given discord channel
    # Inputs: ctx (discord.ext.Commands.Context)
    # Outputs: None
    # Exceptions: None
    @notify.command()
    async def disable(self, ctx):
        current_itr: int = self.deals_report.current_loop
        # Edge case check. If these two ints dont match that means the loop just hit a new iteration
        # but deals_report hasn't finished notifying on all the channels in self.ID_TO_GUILD.
        # current_loop appears to be incremented right when a new iteration begins. So in edge case
        # where user tries to remove notifications during fresh iteration block them.
        if current_itr != self.DEALS_REPORT_INTERNAL_LOOP_COUNT:
            await ctx.reply(f"Notifications are currently in progress. Please try again in a few minutes.")
        else: 
            channel_id: int = ctx.channel.id
            # This will lead to a runtime warning if invoked during deals_report task execution
            # e.g dict size changed during iteration
            if channel_id in self.ID_TO_GUILD:
                self.ID_TO_GUILD.pop(channel_id)
                await ctx.reply(f"Notifications for {ctx.channel.name} disabled.")
            else:
                await ctx.reply("This channel does not have notifications enabled!")

    # Function to implement the asyncio task that will trigger every LOOP_INTERVAL hours to send 
    # deals reports to all channels in ID_TO_GUILD.
    # 
    # Note: 
    # In my hacky form of testing I would just CTRL + C to raise a KeyboardInterrupt exception and kill the 
    # the process. With an asyncio task this also seems to trigger a new iteration of deals_report. This will
    # result in a deals_report to a 'few' channels, since they're sequential notifications.
    @tasks.loop(hours=LOOP_INTERVAL, reconnect=True)
    async def deals_report(self): 
        for id in self.ID_TO_GUILD:
            guild: discord.Guild = self.ID_TO_GUILD[id]
            channel: discord.abc.GuildChannel = guild.get_channel(id)
            for sub_name in self.LOOP_SUBS: 
                sub: redditClientImpl.reddit_hunter.subreddit_hunter = self.rClient.add_or_get_sub(channel, sub_name)
                for command in sub.commandToCall: 
                    result : dict[str, str] = sub.commandToCall[command](self.DEFAULT_COUNT)
                    # Send message to channel 
                    msg: discord.Message = await channel.send(f"{command} report incoming for r/{sub_name}!")
                    await discordUtils.make_thread(result, msg, f'{sub.subreddit} Deals', True)
                    # Sleep because might get throttled for this and don't like msg spam
                    await asyncio.sleep(5.0)
        self.DEALS_REPORT_INTERNAL_LOOP_COUNT += 1; 

    # Function to override on_ready event listener to set up bot
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.deals_report.is_running():
            task: asyncio.Task = self.deals_report.start()