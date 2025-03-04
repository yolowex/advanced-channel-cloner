import asyncio
import logging
import os

import pyrogram.types
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
replacement_link = os.getenv("REPLACEMENT_LINK")
replacement_username = os.getenv("REPLACEMENT_USERNAME")

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


def modify_entities(entities: list[pyrogram.types.MessageEntity]):
    nl = []
    for entity in entities:
        ne = entity
        if ne.url:
            ne.url = replacement_link
        if ne.user:
            ne.user.username = replacement_username
        nl.append(ne)

    return nl



def modify_text(text: str):
    def fun(v:str):
        if v.startswith("@"):
            v = "@"+replacement_username
        return v

    x = [fun(i) for i in text.split(" ")]
    return " ".join(x)


async def handle_media(message):
    """
    This function handles different types of media in a message and forwards them to the source channel.

    :param message: The message containing the media
     :type message: pyrogram.types.Message
    """
    message_caption = message.caption if message.caption is not None else ""

    if message.video:
        video = await app.download_media(message, in_memory=True)
        await app.send_video(target_channel, video, caption=modify_text(message_caption, ),
                             caption_entities=modify_entities(message.caption_entities), )
        return

    elif message.photo:
        logging.info("Downloading media")
        photo = await app.download_media(message, in_memory=True)
        logging.info("Sending media")
        await app.send_photo(target_channel, photo, caption=modify_text(message_caption, ),
                             caption_entities=modify_entities(message.caption_entities), )
        return

    else:
        logging.warning(f"undistinguished message type thrown to else!")
        await app.send_message(target_channel, modify_text(message.text, ), entities=modify_entities(message.entities))
        return


@app.on_message(filters.chat(source_channel_list))
async def hello(client, message):
    if message.media:
        logging.info("Media detected")
        await handle_media(message)

    else:
        await app.send_message(target_channel, modify_text(message.text, ),
                               entities=modify_entities(message.entities, ))


app.run()
