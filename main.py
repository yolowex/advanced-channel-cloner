import asyncio
import logging
import os
from rich import print
import typer
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto

# Environment variables
load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
source_channel_list = os.getenv("SOURCE_CHANNEL_LIST")
target_channel = os.getenv("TARGET_CHANNEL")

if not api_id or not api_hash or not source_channel_list or not target_channel:
    typer.echo("Please set the environment variables")
    # exit on pressing enter
    try:
        typer.confirm("Press enter to exit", abort=True)
        exit(1)
    except typer.Abort:
        exit(1)
else:
    try:
        source_channel_list = [int(i) for i in source_channel_list.split("_")]
        target_channel = int(target_channel)
    except TypeError:
        typer.echo("Please set the environment variables correctly")
        try:
            # exit on pressing enter
            typer.confirm("Press enter to exit", abort=True)
        except typer.Abort:
            exit(1)

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


async def handle_media(message):
    """
    This function handles different types of media in a message and forwards them to the source channel.

    :param message: The message containing the media
     :type message: pyrogram.types.Message
    """
    message_text = message.text if message.text is not None else ""
    print(message_text)

    # if message.poll:

    # if message.sticker:

    if message.video:
        video = await app.download_media(message, in_memory=True)
        await app.send_video(target_channel, video, caption=message_text, caption_entities=message.entities, )
        return

    # if message.audio:

    # if message.voice:

    # if message.animation:

    # if message.document:

    # if message.contact:

    # if message.location:

    # if message.venue:

    # if message.game:

    # if message.video_note:

    # if message.dice:

    if message.photo:
        logging.info("Downloading media")
        photo = await app.download_media(message, in_memory=True)
        logging.info("Sending media")
        await app.send_photo(target_channel, photo, caption=message_text, caption_entities=message.entities,)
        return


@app.on_message(filters.chat(source_channel_list))
async def hello(client, message):
    if message.media:
        logging.info("Media detected")
        await handle_media(message)

    else:
        await app.send_message(target_channel, message.text)


app.run()
