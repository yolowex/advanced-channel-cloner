import asyncio
import logging
import os
from rich import print
import typer
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup

# Environment variables
load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
target_channel = os.getenv("TARGET_CHANNEL")

if not api_id or not api_hash or not target_channel:
    typer.echo("Please set the environment variables")
    # exit on pressing enter
    try:
        typer.confirm("Press enter to exit", abort=True)
        exit(1)
    except typer.Abort:
        exit(1)

SENT_MEDIA_GROUP = []
media_group_locks = {}

in_memory = False

if os.path.exists("tb_session.session"):
    typer.echo("Session file already exists, delete it if you want to create a new session")
else:
    store = typer.confirm("Do you want to store the session file?", abort=False)

    if not store:
        in_memory = True
    else:
        in_memory = False

logging.basicConfig(level=logging.INFO)
app = Client("tb_session", api_id, api_hash, in_memory=in_memory)

# Global variable to store source channel list
source_channel_list = []


async def forward_media_group(message):
    """
    This function forwards a media group from one channel to another.
    It assumes all channels have forwarding restricted and copies the content of the media group to the monitoring channel.

    :param message: The message containing the media group
    :type message: pyrogram.types.Message
    """
    # If there's no lock for this media group, create one
    if message.media_group_id not in media_group_locks:
        media_group_locks[message.media_group_id] = asyncio.Lock()

    # Acquire the lock for this media group
    async with media_group_locks[message.media_group_id]:
        if message.media_group_id in SENT_MEDIA_GROUP:
            return

        SENT_MEDIA_GROUP.append(message.media_group_id)  # Because it was sent repeatedly for some reason
        media_group = await app.get_media_group(message.chat.id, message.id)
        v_media_group = []
        for message in media_group:
            logging.info("Downloading media")
            photo = await app.download_media(message, in_memory=True)
            photo_obj = InputMediaPhoto(photo)
            v_media_group.append(photo_obj)
        logging.info("Sending media group")
        await app.send_media_group(target_channel, v_media_group)
        print("Sent media group")
        v_media_group.clear()


async def handle_media(message):
    """
    This function handles different types of media in a message and forwards them to the source channel.

    :param message: The message containing the media
     :type message: pyrogram.types.Message
    """
    if message.poll:
        options = []

        # is it anonymous?
        if message.poll.is_anonymous:
            is_anonymous = True
        else:
            is_anonymous = False

        for option in message.poll.options:
            options.append(option.text)
        await app.send_poll(target_channel, question=message.poll.question, options=options, is_anonymous=is_anonymous)
        return

    if message.sticker:
        sticker = await app.download_media(message, in_memory=True)
        await app.send_sticker(target_channel, sticker)
        return

    if message.video:
        video = await app.download_media(message, in_memory=True)
        await app.send_video(target_channel, video)
        return

    if message.audio:
        audio = await app.download_media(message, in_memory=True)
        await app.send_audio(target_channel, audio)
        return

    if message.voice:
        voice = await app.download_media(message, in_memory=True)
        await app.send_voice(target_channel, voice)
        return

    if message.animation:
        animation = await app.download_media(message, in_memory=True)
        await app.send_animation(target_channel, animation)
        return

    if message.document:
        document = await app.download_media(message, in_memory=True)
        await app.send_document(target_channel, document)
        return

    if message.contact:
        await app.send_contact(target_channel, message.contact.phone_number, message.contact.first_name)
        return

    if message.location:
        await app.send_location(target_channel, message.location.latitude, message.location.longitude)
        return

    if message.venue:
        await app.send_venue(target_channel, message.venue.location.latitude, message.venue.location.longitude,
                             message.venue.title, message.venue.address)
        return

    if message.game:
        await app.send_game(target_channel, message.game.title)
        return

    if message.video_note:
        video_note = await app.download_media(message, in_memory=True)
        await app.send_video_note(target_channel, video_note)
        return

    if message.dice:
        await app.send_dice(target_channel, message.dice.emoji)
        return

    if message.photo:
        logging.info("Downloading media")
        photo = await app.download_media(message, in_memory=True)
        logging.info("Sending media")
        await app.send_photo(target_channel, photo)
        return


@app.on_message(filters.chat(source_channel_list))
async def hello(client, message):
    if message.media_group_id:
        logging.info("Media group detected")
        await forward_media_group(message)

    elif message.media:
        logging.info("Media detected")
        await handle_media(message)

    else:
        await app.send_message(target_channel, message.text)

@app.on_message(filters.user("dev1962") & filters.command("set_source"))
async def set_source_channel(client, message):
    global source_channel_list
    # Extract the channel list from the message
    new_source_list = message.text.split(maxsplit=1)
    if len(new_source_list) < 2:
        await message.reply("Please provide a source channel list separated by underscores.")
        return

    source_channel_list = [int(i) for i in new_source_list[1].split("_")]
    await message.reply(f"Source channel list updated to: {source_channel_list}")

@app.on_message(filters.user("dev1962") & filters.command("show_source"))
async def show_source_channel(client, message):
    await message.reply(f"Current source channel list: {source_channel_list}")

@app.on_message(filters.user("dev1962") & filters.command("reboot"))
async def reboot_script(client, message):
    await message.reply("Rebooting the script...")
    os.execv(__file__, ['python'] + [__file__])  # Restart the script

@app.on_message(filters.user("dev1962") & filters.command("menu"))
async def menu(client, message):
    keyboard = [
        [InlineKeyboardButton("Set Source Channel List", callback_data="set_source"),
         InlineKeyboardButton("Show Source Channel List", callback_data="show_source")
         ],
        [InlineKeyboardButton("Reboot Script", callback_data="reboot_script")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply("Choose an option:", reply_markup=reply_markup)

@app.on_callback_query(filters.user("dev1962"))
async def callback_query_handler(client, callback_query):
    if callback_query.data == "set_source":
        await callback_query.message.reply("Please send the command `/set_source` followed by the channel list.")
    elif callback_query.data == "show_source":
        await callback_query.message.reply(f"Current source channel list: {source_channel_list}")
    elif callback_query.data == "reboot_script":
        await callback_query.message.reply("Rebooting the script...")
        os.execv(__file__, ['python'] + [__file__])  # Restart the script

app.run()
