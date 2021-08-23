import os

import aiohttp
from pyrogram import filters
from pytube import YouTube
from youtubesearchpython import VideosSearch

from DaisyX import LOGGER, pbot
from DaisyX.utils.ut import get_arg


def yt_search(song):
    videosSearch = VideosSearch(song, limit=1)
    result = videosSearch.result()
    if not result:
        return False
    else:
        video_id = result["result"][0]["id"]
        url = f"https://youtu.be/{video_id}"
        return url


class AioHttp:
    @staticmethod
    async def get_json(link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                return await resp.json()

    @staticmethod
    async def get_text(link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                return await resp.text()

    @staticmethod
    async def get_raw(link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                return await resp.read()


@pbot.on_message(filters.command("song"))
async def song(client, message):
    message.chat.id
    user_id = message.from_user["id"]
    args = get_arg(message) + " " + "song"
    if args.startswith(" "):
        await message.reply("Enter a song name. Check /help")
        return ""
    status = await message.reply("Processing...")
    video_link = yt_search(args)
    if not video_link:
        await status.edit("Song not found.")
        return ""
    yt = YouTube(video_link)
    audio = yt.streams.filter(only_audio=True).first()
    try:
        download = audio.download(filename=f"{str(user_id)}")
    except Exception as ex:
        await status.edit("Failed to download song")
        LOGGER.error(ex)
        return ""
    os.rename(download, f"{str(user_id)}.mp3")
    await pbot.send_chat_action(message.chat.id, "upload_audio")
    await pbot.send_audio(
        chat_id=message.chat.id,
        audio=f"{str(user_id)}.mp3",
        duration=int(yt.length),
        title=str(yt.title),
        performer=str(yt.author),
        reply_to_message_id=message.message_id,
    )
    await status.delete()
    os.remove(f"{str(user_id)}.mp3")


__help__ = """
 *You can either enter just the song name or both the artist and song
  name. *

Holla Welcome to help menu ✨

📌 HOW TO USE CYBER MUSIC GROUP ?

1. First add me to your group.
2. Promote me as admin and give all permission.
3. Then, add @SaitamaHelper to your group or you can type /userbotjoin.
3. Turn on the VCG first before playing music.

📌 Command for all group members:

/play (song title) - play music via youtube
/stream (reply to audio) - play music via reply audio
/playlist - show playlist
/current - shows what is currently playing
/song (song title) - download music via youtube
/search (video name) - search for videos from youtube in detail
/vsong (video name) - download videos from youtube in detail
/vk (song title) - download via inline mode

📌 Commands for admin:

/player - opens the music settings panel
/pause - pause music playback
/resume - resume music playing
/skip - skips the currently playing song
/end - stop music
/userbotjoin - invite assistants to your group
/reload - to update admin list
/cache - to clear admin cache
/musicplayer (on / off) - turn on/off the music player in your group

🎧 Channel streaming commands:

/cplay - listen to music via channel
/cplayer - view playlists
/cpause - pause music player
/cresume - resume paused music
/cskip - skips the currently playing song
/cend - stop the song
/admincache - update admin cache
️ command for sudo users:
/userbotleaveall - remove assistant from all groups
/gcast - send broadcast messages

📌 Commands for fun:

/lyrics - (song title) see lyrics
"""

__mod_name__ = "Music Player"
