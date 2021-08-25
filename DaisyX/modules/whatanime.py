import html
import json
import re
import textwrap
from io import BytesIO, StringIO
import aiohttp
import bs4
import pendulum
import requests
from telethon.errors.rpcerrorlist import FilePartsInvalidError
from telethon.tl.types import (
    DocumentAttributeAnimated,
    DocumentAttributeFilename,
    MessageMediaDocument,
)
from telethon.utils import is_image, is_video
from DaisyX import telethn as tbot
from DaisyX.events import register

session = aiohttp.ClientSession()
progress_callback_data = {}


def format_bytes(size):
    size = int(size)
    # 2**10 = 1024
    power = 1024
    n = 0
    power_labels = {0: "", 1: "K", 2: "M", 3: "G", 4: "T"}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]+'B'}"


def return_progress_string(current, total):
    filled_length = int(30 * current // total)
    return "[" + "=" * filled_length + " " * (30 - filled_length) + "]"


def calculate_eta(current, total, start_time):
    if not current:
        return "00:00:00"
    end_time = time.time()
    elapsed_time = end_time - start_time
    seconds = (elapsed_time * (total / current)) - elapsed_time
    thing = "".join(str(timedelta(seconds=seconds)).split(".")[:-1]).split(", ")
    thing[-1] = thing[-1].rjust(8, "0")
    return ", ".join(thing)


@register(pattern="^/whatanime ?(.*)")
async def whatanime(e):
    media = e.media
    if not media:
        r = await e.get_reply_message()
        media = getattr(r, "media", None)
    if not media:
        await e.reply("`Media required`")
        return
    ig = is_gif(media) or is_video(media)
    if not is_image(media) and not ig:
        await e.reply("`Media must be an image or gif or video`")
        return
    filename = "file.jpg"
    if not ig and isinstance(media, MessageMediaDocument):
        attribs = media.document.attributes
        for i in attribs:
            if isinstance(i, DocumentAttributeFilename):
                filename = i.file_name
                break
    kontol = await e.reply("`Downloading image..`")
    content = await tbot.download_media(media, bytes, thumb=-1 if ig else None)
    await kontol.edit("`Searching for result..`")
    file = memory_file(filename, content)
    async with aiohttp.ClientSession() as session:
        url = "https://api.trace.moe/search?anilistInfo"
        async with session.post(url, data={"image": file}) as raw_resp0:
            resp0 = await raw_resp0.json()
        js0 = resp0.get("result")
        if not js0:
            await e.reply("`No results found.`")
            return
        js0 = js0[0]
        text = f'<b>{html.escape(js0["anilist"]["title"]["romaji"])}'
        if js0["anilist"]["title"]["native"]:
            text += f' ({html.escape(js0["anilist"]["title"]["native"])})'
        text += "</b>\n"
        if js0["episode"]:
            text += f'<b>Episode:</b> {html.escape(str(js0["episode"]))}\n'
        percent = round(js0["similarity"] * 100, 2)
        text += f"<b>Similarity:</b> {percent}%\n"
        at = re.findall(r"t=(.+)&", js0["video"])[0]
        dt = pendulum.from_timestamp(float(at))
        text += f"<b>At:</b> {html.escape(dt.to_time_string())}"
        await kontol.edit(text, parse_mode="html")
        dt0 = pendulum.from_timestamp(js0["from"])
        dt1 = pendulum.from_timestamp(js0["to"])
        ctext = (
            f"{html.escape(dt0.to_time_string())} - {html.escape(dt1.to_time_string())}"
        )
        async with session.get(js0["video"]) as raw_resp1:
            file = memory_file("preview.mp4", await raw_resp1.read())
        try:
            await e.reply(ctext, file=file, parse_mode="html")
        except FilePartsInvalidError:
            await e.reply("`Cannot send preview.`")


def memory_file(name=None, contents=None, *, _bytes=True):
    if isinstance(contents, str) and _bytes:
        contents = contents.encode()
    file = BytesIO() if _bytes else StringIO()
    if name:
        file.name = name
    if contents:
        file.write(contents)
        file.seek(0)
    return file


def is_gif(file):
    # ngl this should be fixed, telethon.utils.is_gif but working
    # lazy to go to github and make an issue kek
    if not is_video(file):
        return False
    return DocumentAttributeAnimated() in getattr(file, "document", file).attributes
