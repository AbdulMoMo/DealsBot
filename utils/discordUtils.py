import discord
import clients.redditClientImpl as redditClientImpl

THREAD_ARCHIVE_DURATION: int = 60

# Possible question emojis I could use: 
# '\u2753', '\u2754', '\u2049\ufe0f'
QUESTION_EMOJI = '\u2753'

# Function to create a general discord embed for a bot message
# Inputs: post (str) - post title, result (dict) - varies
# Outputs: embed (discord.Embed)
# Exceptions: None
def create_general_embed(post, result) -> discord.Embed:
    embed: discord.Embed = discord.Embed(
        color=discord.Colour.dark_magenta(),
        url=f'{result[post]}'
    )
    embed.description = f'[{post}]({result[post]})'
    return embed

# Function to create a general discord embed for a bot message
# Inputs: post (str) - post title, result (dict) - varies
# Outputs: embed (discord.Embed)
# Exceptions: None
def create_field_embed(result, title, url) -> discord.Embed:
    embed: discord.Embed = discord.Embed(
        color=discord.Colour.brand_green(),
        title=title,
        url=url
    )
    for field in result.keys():
        embed.add_field(name=f"**{field}**", value=f"{result[field]}", inline=False)
    return embed

def set_embed_image(embed: discord.Embed, url):
    # * means it will only accept kwargs https://github.com/Rapptz/discord.py/issues/647
    embed.set_image(url=url)
    return

# Function to create thread (ex. $search and $show) for reddit deals
# Inputs: result - dict[str, str], message - discord.Message, name - str
# Outputs: None
# Exceptions: None
async def make_thread(result: dict[str, str], 
                            message: discord.Message, 
                            threadName: str,
                            isBasic: bool):
    try: 
        thread: discord.Thread = await message.create_thread(name=threadName, auto_archive_duration=THREAD_ARCHIVE_DURATION)
    except discord.HTTPException: 
        # Could not create thread in this case. TODO: when I add logging need to emit error here
        return
    for post in result.keys():
        embed: discord.Embed = create_general_embed(post, result)
        threadMessage: discord.Message = await thread.send(embed=embed)
        if isBasic: 
            await threadMessage.add_reaction(QUESTION_EMOJI)