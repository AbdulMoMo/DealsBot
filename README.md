# DealzBot

# Table of Contents

1. [Changelog](#changelog-new)
2. [Introduction](#introduction)
2. [Why Reddit?](#why-reddit)
3. [Reddit Commands](#reddit-commands)
4. [Future Releases](#future-releases)
5. [Steam Commands](#steam-commands-tbd)
6. [DealzBot Design and Thoughts](#dealzbot-design-and-thougts)
7. [Bug Reporting](#bug-reporting)

## Changelog (NEW)

To try and keep up with the pace of of my own changes to DealzBot. I will now be adding a changelog at the top of the README to keep up with latest changes. Ideally this oldest updates will be cleared out and incorporated into the README itself. 

1/25/2023
- Added a new feature for automatic notifications! This consists of two commands:
  - `$notifyenable` for enabling notifications at the channel level 
  - `$notifydisable` for disabling notifications at the channel level 
  - Use `$reddithelp` for more details
- HowLongToBeat integration! Now you can use the command `$hltb <game_name>` to have DealzBot return you the HowLongToBeat information on a given game. 
  - For multi-word queries use `""` to enclose the search query
- A refactoring of the DealzBot project to improve readibility and reduce code redundancy. (It had also proved simpler to implement HowLongToBeat functionality after cleaning up the project structure)
  - Still pending changes  in the `operations` space are: 
    - ~~Updates to all comments in Python docstrings format~~
      - 1/26 all current classes now are commented in doc strings format!
    - Revamped logging for easier debugging

---

## Introduction

A bot for learning about game deals! Have you ever wanted to find out information regarding Technically, this bot is a glorified Reddit scraper, but DealzBot is a more  tantalizing title and this project was inspired by a desire for game deals ***without*** having to go on Reddit.

---

## Why Reddit?

In my own experience, I specifically found `r/buildapcsales` and `r/GameDeals` to be great sources of information on video game/hardware related deals if you kept your eye regularly on those subreddits. The issue I found is that I don't always want to have to go on Reddit itself to get that information. I want it easily displayed me to through a means of communications I regularly use---Discord! Hence, DealzBot was born.

---

## Reddit Commands

For usage information and a description on the reddit commands, please use `$reddithelp` in a server where the bot is a member and is online. See below for a quick reference of the available commands and their possible configurations.

---

### Command: `$select [subreddit_name]`

Usage Examples:

- `$select buildapcsales`
- `$select hardwareswap`
- `$select tifu`

Notes:

- A valid input is a subreddit that exists and is not banned or quarantined on Reddit

---

### Command: `$show`

***The subreddit queried in this command is based on what is set in the channel with `$select`.***

Usage Examples:

- `$show topdeals`
- `$show risingdeals`
- `$show controversialdeals`
- `$show hotdeals`
- `$show n hot deals`
  - `Where n can be any positive number`

Notes:

- Negative numbers would not work for any of you anarchists out there

---

### Command: `$search [(OPTIONAL) time_filter] [query]`

Possible time filters:

- `all`,`day`,`hour`,`month`,`week` or`year`

Usage Examples:

- `$search day destiny`
- `$search 3080`

Notes:

- The hard limit set for this command is 5 posts. Otherwise Discord would yell at DealzBot.

---

Command: `Question Mark Emojis` (see `$reddithelp` for emoji reference and usage example)

Notes:

- DealzBot is a stateless bot, nothing is persisted. So there are (hacky) solutions to make sure DealzBot gets everything it needs based on the invocation context for a given command.

---

## Future Releases

- Besides any big feature addition such as a new command suite, a nice QOL feature I've considered is DealzBot giving alerts on deals (i.e posts) pulled from Reddit on regular intervals defined by the user (TBD)

---

## Steam Commands (TBD)

Now that the core functionality is there for interacting with Reddit, the next feature I wanted to explore would be interaction with Steam using this [package](https://pypi.org/project/steam/)

Updates on those commands, when they come up, will be detailed here and as a new `$help` command for the bot

---

## DealzBot Design and Thougts

(Accurate as of 12/10/2022) 

The project consists of:

`dealsBot.py` (For encapsulating the Discord logic)

`redditClientImpl.py` (For encapsulating the Reddit logic)

Within the above there are three objects:

`reddit_commands` in `dealsBot.py`

`reddit_hunter` in `redditClientImpl.py`

`subreddit_hunter` in `redditClientImpl.py`

Below you can find a word vomit of my thought process when fleshing out these classes:

`reddit_commands`

- An earlier, barebones, implementation used only what was necessary from[`DiscordPy`](https://discordpy.readthedocs.io/en/stable/) to get a bot that could respond to basic commands
  - Then I realized that the[`discord.ext.commands`](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html#quick-example) framework allowed for a clean encapsulation of commmands within a class (known as a Cog within the context of`discord.ext.commands`)
- This class contains all of the bot commands a user can invoke to interact with the Reddit client and pull submission info
  - There are also a few helper methods for constructing those fancy***embeds*** you see DealzBot replying with
- You may notice that the embed format for`$show` or`$search` is different than`$reddithelp` or reacting with a`question mark`
  - This then led to two different functions, as I thought a larger function split with if conditionals and additional parameters sounded...undesirable
  - Why did I split the formatting logic? Simply because I found that for longer Reddit post titles, such as those found within`r/GameDeals`, Discord would throw`InvalidFormBody` exceptions when an embed's`title` field was > 256 characters
    - But it didn't yell at me when I put the post title as the description field ;)
- You may also notice the (seemingly) random string appended to all`$show` and`$search` results
  - For every reddit post defined in the path of its corresponding URL is 6 digit string that appears to be a direct reference to a reddit post (e.g`https://www.reddit.com/r/GameDeals/comments/z7rz9q/gamersgate_king_arthur_knights_tale_51_2193_2193/`)
  - This was my naive attempt to easily retrieve a reference to the submission since DealzBot does not persist any data locally
    - So, based on the message the user reacts to, DealzBot checkes the message related to the reaction to see if it can find an encapsulated id within`[]`
      - If an id is found, DealzBot will query the reddit client for that submission and return additional information on the submission

`reddit_hunter` and `subreddit_hunter`

- A difficult question I faced early on was how to encapsulate the interactions with the Reddit client in a way that felt intuitive and easy to build off of
  - At first I had planned on integrating the Reddit interactions, and specifically instanatiate the Reddit client, within`reddit_commands`
  - As I started thinking of methods and all of the logic I'd define for these commands it felt like too much for just one class. Enter`reddit_hunter` and`subreddit_hunter`
- The two are related in the sense`subreddit_hunter` os a child of`reddit_hunter`
  - At first, the parent was marely supposed to be a means of storing references to the subreddit set for the specific discord channel, see`add_or_get_sub()`, and when the subreddit reference was retrieved for a channel it was actually just a reference to the child`subreddit_hunter`
  - The first kink, and I imagine not the last, in this plan was that retrieving submission details did not require an instance of`Praw.models.Subreddit`, which is the underlying object that`subreddit_hunter` interacts with
    - Enter`get_post_details_from_id()`, which just directly leverages the Reddit client,`dealFinder`, to query for the submission by the id
  - Ultimately the original purpose of`subreddit_hunter`, to encapsulate any and all interactions with instances of`Praw.models.Subreddit` still applies. I'm just not 100% content with the current implementation
- Besides that internal drama, a nifty feature within`subreddit_hunter` is that all variants of the`$show` command are encapsulated with the`commmandToCall` dict that is actually a nestled lambda invocation with the trigger being the integer you pass along, for the`limit` value for the top/hot/controversial/rising method call on the underlying`Praw.models.subreddit` object, when accessing commandToCall (shoutout to`jcortezzo` for showing me this)

---

## Known Issues

- ~~While you ***can*** (this might change in the future), define a high pagination limit for the `$show` commands, Discord will [rate limit](https://discord.com/developers/docs/topics/rate-limits) DealzBot~~
  - 11/30/22 Update: To stay on the safer side, I've restricted the max output to 10
- As of 12/10, DealzBot now makes threads for results from`$show` and`$search` invocations
  - If you were to invoke one of those two commands in a thread made by DealzBot, that request goes into the void
    - Another situation where logging will give me more insight, though I also need to see if I can identify whether a message belongs to a thread
- With certain`$show` invocations, I've found that the fifth result (when using the default of 5) takes slightly longer to be sent than the preceding four. Once I implement proper logging for DealzBot I'll look into why that's the case as, to my memory, this was not an issue in previous iterations of DealzBot (pre-embed message era)
  - In testing with larger list amounts (>5), there is a delay in the submission results. I assume it's a limitation/feature of PRAW but have not researched enough on this yet
- Even though, in principle, DealzBot should be able to process a question mark request on any valid `$show` output in a channel, it does not (12/10/2022) work that way based on DealzBot's uptime
  - I believe this is due the internal message cache accessible to the Discord client. Once the client has been instanatied, the cache will start populating with messages from the server that DealzBot effectivel process. That means that two variables can impact DealzBot's ability to act on a question mark: 
    - Whether the message is far enough back that the message was cleared from the cache (e.g if the message was 1001 messages ago in the server but the Discord client only caches up to 1000)
    - Whether the bot's currently active session is within the same as when the ***original*** `$show` or `$search` command was invoked
  - TL;DR When in doubt, just run `$show` or `$search` again to get new messages to react to for DealzBot's sake

---

## Bug Reporting

This project sure isn't perfect! In your use, if you encounter any quirky behavior or error message that is not explained in this README or through the help messages please create a [new issue!](https://github.com/AbdulMoMo/DealsBot/issues)

To help me out even more in troubleshooting the issue, if possible, please provide the command sequence and/or screenshots so I can replicate on my end.

---
