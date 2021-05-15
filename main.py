import discord
from discord.ext.commands import Bot
import json
from datetime import datetime
import logging
from os import environ

bot = Bot(command_prefix=".")

def save_boards(board_dict: dict):
    with open("data/boards.json", "w") as f:
        logging.debug("Dumped board")
        json.dump(board_dict, f)

def load_boards() -> dict:
    with open("data/boards.json", "r") as f:
        logging.debug("Read board")
        return json.load(f)

@bot.event
async def on_ready():
    logging.info("Bot is Ready")
    await bot.change_presence(activity=discord.Streaming(name="Gaming", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

@bot.command()
async def create_board(ctx, emote, channel_id):
    """
    Sets board chat; Format: emote, channel_id
    """
    if emote == "😂":
       await ctx.send("No.") 
    else:
        try:
            board_dict = load_boards()
        except FileNotFoundError:
            board_dict = {}
        board_dict[emote] = channel_id
        save_boards(board_dict)
        await ctx.send("Board successfully set")


@bot.event
async def on_raw_reaction_add(payload):
    # Load data containing board channel info
    bd_dict = load_boards()

    # Check if reaction added is a "board" reaction
    if str(payload.emoji) in bd_dict:
        # Fetch channel react was added in and corresponding board channel
        board_channel = bot.get_channel(int(bd_dict[str(payload.emoji)]))
        input_channel = bot.get_channel(payload.channel_id)
        # Fetch message react was added to
        message = await input_channel.fetch_message(payload.message_id)
        
        # Open JSON containing data of all pinned messages
        try:
            with open(f"data/{board_channel.name}.json", "r") as f:
                pinned_messages = json.load(f)
        except FileNotFoundError:
            pinned_messages = {}
            logging.warn("Board Channel JSON not yet created")

        # Determine number of reactions
        react_count = 0
        for reaction in message.reactions:
            if str(reaction.emoji).find(payload.emoji.name) != -1:
                react_count = reaction.count

        # Create new embed if this is the first reaction and the message has not already been pinned in the correct channel
        if react_count == 1 and str(message.id) not in pinned_messages:
            # Create and format embed
            pin = discord.Embed(
                    description=message.content,
                    color=0x66FF99,
            )
            pin.set_author(name=message.author.name, icon_url=message.author.avatar_url)
            try:
                pin.set_image(url=message.attachments[0].url)
            except IndexError:
                pass
            # Date time for footer
            current_time = datetime.now()
            time_str = current_time.strftime("%d/%m/%Y %H:%M:%S")
            footer_msg = f"{message.id}  •  {time_str}"
            pin.set_footer(text=footer_msg)
            # Jump! hyperlink
            message_link = f"[Jump!](https://discord.com/channels/{message.guild.id}/{input_channel.id}/{message.id})"
            pin.add_field(name="Source", value=message_link, inline=False)
             
            pin_msg = await board_channel.send(content=f"{payload.emoji} **1** <#{input_channel.id}>", embed=pin)

            # Save message info
            with open("data/" + board_channel.name + ".json","w") as f:
                json.dump({message.id: pin_msg.id}, f)
        # Update react count in message if not first react
        elif react_count > 1:
            pin_msg = await board_channel.fetch_message(int(pinned_messages[str(message.id)]))
            await pin_msg.edit(content=f"{payload.emoji} **{reaction.count}** <#{input_channel.id}>")




bot.run(environ["DISCORD_API_TOKEN"])

