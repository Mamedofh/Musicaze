# Daisyxmusic (Telegram bot project)
# Copyright (C) 2021  Inukaasith
# Copyright (C) 2021  TheHamkerCat (Python_ARQ)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import json
import os
from os import path
from typing import Callable

import aiofiles
import aiohttp
import ffmpeg
import requests
import wget
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Voice
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from Python_ARQ import ARQ
from youtube_search import YoutubeSearch

from DaisyXMusic.config import ARQ_API_KEY
from DaisyXMusic.config import BOT_NAME as bn
from DaisyXMusic.config import DURATION_LIMIT
from DaisyXMusic.config import UPDATES_CHANNEL as updateschannel
from DaisyXMusic.config import que
from DaisyXMusic.function.admins import admins as a
from DaisyXMusic.helpers.admins import get_administrators
from DaisyXMusic.helpers.channelmusic import get_chat_id
from DaisyXMusic.helpers.errors import DurationLimitError
from DaisyXMusic.helpers.decorators import errors
from DaisyXMusic.helpers.decorators import authorized_users_only
from DaisyXMusic.helpers.filters import command, other_filters
from DaisyXMusic.helpers.gets import get_file_name
from DaisyXMusic.services.callsmusic import callsmusic, queues
from DaisyXMusic.services.callsmusic.callsmusic import client as USER
from DaisyXMusic.services.converter.converter import convert
from DaisyXMusic.services.downloaders import youtube

aiohttpsession = aiohttp.ClientSession()
chat_id = None
arq = ARQ("https://thearq.tech", ARQ_API_KEY, aiohttpsession)


def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        else:
            await cb.answer("??caz?? verilmir!", show_alert=True)
            return

    return decorator


def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw", format="s16le", acodec="pcm_s16le", ac=2, ar="48k"
    ).overwrite_output().run()
    os.remove(filename)


# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    image1 = Image.open("./background.png")
    image2 = Image.open("./etc/foreground.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/font.otf", 32)
    draw.text((205, 550), f"Ba??l??q: {title}", (51, 215, 255), font=font)
    draw.text((205, 590), f"M??dd??t: {duration}", (255, 255, 255), font=font)
    draw.text((205, 630), f"??zl??nm??: {views}", (255, 255, 255), font=font)
    draw.text(
        (205, 670),
        f"Added By: {requested_by}",
        (255, 255, 255),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(filters.command("playlist") & filters.group & ~filters.edited)
async def playlist(client, message):
    global que
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("??stiad????i Bo??tur")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "**??ndi Oxuyur** in {}".format(message.chat.title)
    msg += "\n- " + now_playing
    msg += "\n- T??r??find??n: " + by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "**N??vb??**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n- {name}"
            msg += f"\n- T??r??find??n: {usr}\n"
    await message.reply_text(msg)


# ============================= Settings =========================================


def updated_stats(chat, queue, vol=100):
    if chat.id in callsmusic.pytgcalls.active_calls:
        # if chat.id in active_chats:
        stats = "A **{}**".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "S??s S??viy??si : {}%\n".format(vol)
            stats += "S??radak?? musiqi : `{}`\n".format(len(que))
            stats += "??ndi Oxuyur : **{}**\n".format(queue[0][0])
            stats += "??st??y??n istifad????i : {}".format(queue[0][1].mention)
    else:
        stats = None
    return stats


def r_ply(type_):
    if type_ == "play":
        pass
    else:
        pass
    mar = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("???", "leave"),
                InlineKeyboardButton("???", "puse"),
                InlineKeyboardButton("??????", "resume"),
                InlineKeyboardButton("???", "skip"),
            ],
            [
                InlineKeyboardButton("Musiqi Siyah??s?? ????", "playlist"),
            ],
            [InlineKeyboardButton("??? Ba??la", "cls")],
        ]
    )
    return mar


@Client.on_message(filters.command("2current") & filters.group & ~filters.edited)
async def ee(client, message):
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        await message.reply(stats)
    else:
        await message.reply("Bu s??hb??td?? ??al????an S??sli S??hb??t yoxdur")


@Client.on_message(filters.command("2player") & filters.group & ~filters.edited)
@authorized_users_only
async def settings(client, message):
    playing = None
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        playing = True
    queue = que.get(chat_id)
    stats = updated_stats(message.chat, queue)
    if stats:
        if playing:
            await message.reply(stats, reply_markup=r_ply("pause"))

        else:
            await message.reply(stats, reply_markup=r_ply("play"))
    else:
        await message.reply("Bu s??hb??td?? ??al????an S??sli S??hb??t yoxdur")


@Client.on_callback_query(filters.regex(pattern=r"^(2playlist)$"))
async def p_cb(b, cb):
    global que
    que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("Player is idle")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**Now Playing** in {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- Req by " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**Queue**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- {name}"
                msg += f"\n- T??r??find??n {usr}\n"
        await cb.message.edit(msg)


@Client.on_callback_query(
    filters.regex(pattern=r"^(2play|2pause|2skip|2leave|2puse|2resume|2menu|2cls)$")
)
@cb_admin_check
async def m_cb(b, cb):
    global que
    if (
        cb.message.chat.title.startswith("Channel Music: ")
        and chat.title[14:].isnumeric()
    ):
        chet_id = int(chat.title[13:])
    else:
        chet_id = cb.message.chat.id
    qeue = que.get(chet_id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    m_chat = cb.message.chat

    the_data = cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "pause":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "paused"
        ):
            await cb.answer("S??hb??t ba??lanmay??b!", show_alert=True)
        else:
            callsmusic.pytgcalls.pause_stream(chet_id)

            await cb.answer("Musiqi Dayand??!")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("play")
            )

    elif type_ == "play":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "playing"
        ):
            await cb.answer("S??hb??t ba??lanmay??b!", show_alert=True)
        else:
            callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("Musiqiy?? D??vam Edilir!")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("pause")
            )

    elif type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("??stifad????i Bo??tur")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**??ndi Oxuyur** in {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- T??r??find??n " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**N??vb??**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- {name}"
                msg += f"\n- T??r??find??n {usr}\n"
        await cb.message.edit(msg)

    elif type_ == "resume":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "playing"
        ):
            await cb.answer("S??hb??t ba??l?? deyil v?? ya Haz??rda musiqi oxuyur", show_alert=True)
        else:
            callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("Musiqiy?? d??vam edilir!")
    elif type_ == "puse":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "paused"
        ):
            await cb.answer("S??hb??t ba??lanmay??b v?? ya art??q dayand??r??l??b", show_alert=True)
        else:
            callsmusic.pytgcalls.pause_stream(chet_id)

            await cb.answer("Musiqi Dayand??r??ld??!")
    elif type_ == "cls":
        await cb.answer("Menyu Ba??land??")
        await cb.message.delete()

    elif type_ == "menu":
        stats = updated_stats(cb.message.chat, qeue)
        await cb.answer("Menyu A????ld??")
        marr = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("???", "leave"),
                    InlineKeyboardButton("???", "puse"),
                    InlineKeyboardButton("??????", "resume"),
                    InlineKeyboardButton("???", "skip"),
                ],
                [
                    InlineKeyboardButton("Musiqi Siyah??s?? ????", "playlist"),
                ],
                [InlineKeyboardButton("??? Ba??la", "cls")],
            ]
        )
        await cb.message.edit(stats, reply_markup=marr)
    elif type_ == "skip":
        if qeue:
            qeue.pop(0)
        if chet_id not in callsmusic.pytgcalls.active_calls:
            await cb.answer("S??hb??t ba??lanmay??b!", show_alert=True)
        else:
            callsmusic.queues.task_done(chet_id)

            if callsmusic.queues.is_empty(chet_id):
                callsmusic.pytgcalls.leave_group_call(chet_id)

                await cb.message.edit("- Art??q pleylist yoxdur..\n- S??sli S??hb??t T??rk edilir!")
            else:
                callsmusic.pytgcalls.change_stream(
                    chet_id, callsmusic.queues.get(chet_id)["file"]
                )
                await cb.answer("Ke??ildi")
                await cb.message.edit((m_chat, qeue), reply_markup=r_ply(the_data))
                await cb.message.reply_text(
                    f"- Ke??il??n Par??a\n- ??ndi Oxuyur: **{qeue[0][0]}**"
                )

    else:
        if chet_id in callsmusic.pytgcalls.active_calls:
            try:
                callsmusic.queues.clear(chet_id)
            except QueueEmpty:
                pass

            callsmusic.pytgcalls.leave_group_call(chet_id)
            await cb.message.edit("SS??hb??ti u??urla t??rk etdi!")
        else:
            await cb.answer("S??hb??t ba??lanmay??b!", show_alert=True)


@Client.on_message(command("2play") & other_filters)
async def play(_, message: Message):
    global que
    lel = await message.reply("???? **Proses Gedir**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "helper"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Kanal??n??za Asistan?? ??lav?? etm??yi unutmay??n</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>??vv??lc?? m??ni qrupunuzun admini kimi ??lav?? edin</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "S??sli S??hb??tt??-d?? musiqi oxumaq ??????n bu qrupa qo??uldum"
                    )
                    await lel.edit(
                        "<b>Asistan S??hb??t?? Daxil oldu</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>???? Flood X??tas?? ???? \n??stifad????i {user.first_name} userbot ??????n a????r ist??kl??r s??b??bind??n qrupunuza qo??ula bilm??di! ??stifad????inin qrupda qada??an olunmad??????ndan ??min olun."
                        "\n\nV?? ya Manuel olaraq qrupunuza Asistan ??lav?? edin v?? yenid??n c??hd edin</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} ??stifad????i bu s??hb??td?? deyil, Admind??n ilk d??f?? /play komandas??n?? i??l??tm??sini v?? ya manuel olaraq {user.first_name} ??lav?? etm??sini ist??yin</i>"
        )
        return
    message.from_user.id
    message.from_user.first_name
    text_links=None
    await lel.edit("???? **Axtar??l??r...**")
    message.from_user.id
    if message.reply_to_message:
        entities = []
        toxt = message.reply_to_message.text or message.reply_to_message.caption
        if message.reply_to_message.entities:
            entities = message.reply_to_message.entities + entities
        elif message.reply_to_message.caption_entities:
            entities = message.reply_to_message.entities + entities
        urls = [entity for entity in entities if entity.type == 'url']
        text_links = [
            entity for entity in entities if entity.type == 'text_link'
        ]
    else:
        urls=None
    if text_links:
        urls = True
    user_id = message.from_user.id
    message.from_user.first_name
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"??? Video normaldan uzundu {DURATION_LIMIT} d??qiq??l??r s??hb??td?? icaz?? verilmir!"
            )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("???? Musiqi Siyah??s??", callback_data="playlist"),
                    InlineKeyboardButton("Menyu ??? ", callback_data="menu"),
                ],
                [InlineKeyboardButton(text="??? Ba??la", callback_data="cls")],
            ]
        )
        file_name = get_file_name(audio)
        title = file_name
        thumb_name = "https://telegra.ph/file/f6086f8909fbfeb0844f2.png"
        thumbnail = thumb_name
        duration = round(audio.duration / 60)
        views = "Lokal olaraq ??lav?? olundu"
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name))
            else file_name
        )
    elif urls:
        query = toxt
        await lel.edit("???? **Proses Gedir**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"][:40]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"thumb{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            results[0]["url_suffix"]
            views = results[0]["views"]

        except Exception as e:
            await lel.edit(
                "Musiqi tap??lmad??.Ba??qa bir mahn??n?? s??nay??n v?? ya d??zg??n yazd??????n??zdan ??min olun."
            )
            print(str(e))
            return
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("???? Musiqi Siyah??s??", callback_data="playlist"),
                    InlineKeyboardButton("Menyu ??? ", callback_data="menu"),
                ],
                [
                    InlineKeyboardButton(text="???? YouTube-da izl??", url=f"{url}"),
                    InlineKeyboardButton(text="Y??kl?? ????", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="??? Ba??la", callback_data="cls")],
            ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))        
    else:
        query = ""
        for i in message.command[1:]:
            query += " " + str(i)
        print(query)
        await lel.edit("???? **Proses Gedir**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"][:40]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"thumb{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            results[0]["url_suffix"]
            views = results[0]["views"]

        except Exception as e:
            await lel.edit(
                "Musiqi tap??lmad??.Ba??qa bir mahn??n?? s??nay??n v?? ya d??zg??n yazd??????n??zdan ??min olun."
            )
            print(str(e))
            return
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("???? Musiqi Siyah??s??", callback_data="playlist"),
                    InlineKeyboardButton("Menyu ??? ", callback_data="menu"),
                ],
                [
                    InlineKeyboardButton(text="???? YouTube-da ??zl??yin", url=f"{url}"),
                    InlineKeyboardButton(text="Y??kl?? ????", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="??? Ba??la", callback_data="cls")],
            ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption=f"#??? Sizin ist??diyiniz musiqi **N??vb??y??d??di** N??vb??si: {position}!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        return await lel.delete()
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            message.reply("Qrup z??ngi a????q deyil v?? ya m??n qo??ula bilmir??m")
            return
        await message.reply_photo(
            photo="final.png",
            reply_markup=keyboard,
            caption="?????? **Oxuyur** burada Music Aze vasit??sil?? {} t??r??find??n t??l??b olunan mahn?? ????".format(
                message.from_user.mention()
            ),
        )
        os.remove("final.png")
        return await lel.delete()


@Client.on_message(filters.command("2dplay") & filters.group & ~filters.edited)
async def deezer(client: Client, message_: Message):
    global que
    lel = await message_.reply("???? **Proses gedir**")
    administrators = await get_administrators(message_.chat)
    chid = message_.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "MusicAzE????????????"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await client.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message_.from_user.id:
                if message_.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Kanal??n??za Asistan ??lav?? etm??yi unutmay??n</b>",
                    )
                    pass
                try:
                    invitelink = await client.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>??vv??lc?? m??ni qrupunuzun admini kimi ??lav?? edin</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message_.chat.id, "S??sli S??hb??tt??-d?? musiqi oxumaq ??????n bu qrupa qo??uldum"
                    )
                    await lel.edit(
                        "<b>Asistan userbot s??hb??tiniz?? qat??ld??</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>???? Flood X??tas?? ???? \n??stifad????i {user.first_name} userbot ??????n a????r ist??kl??r s??b??bind??n qrupunuza qo??ula bilm??di! ??stifad????inin qrupda qada??an olunmad??????ndan ??min olun."
                        "\n\nV?? ya Manuel olaraq qrupunuza Asistan ??lav?? edin v?? yenid??n c??hd edin</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} ??stifad????i bu s??hb??td?? deyil, Admind??n ilk d??f?? /play komandas??n?? i??l??tm??sini v?? ya manuel olaraq {user.first_name} ??lav?? etm??sini ist??yin</i>"
        )
        return
    requested_by = message_.from_user.first_name

    text = message_.text.split(" ", 1)
    queryy = text[1]
    query = queryy
    res = lel
    await res.edit(f"Axtar??l??r ???????? `{queryy}` ??????n deezer-d??")
    try:
        songs = await arq.deezer(query,1)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        title = songs.result[0].title
        url = songs.result[0].url
        artist = songs.result[0].artist
        duration = songs.result[0].duration
        thumbnail = "https://telegra.ph/file/f6086f8909fbfeb0844f2.png"

    except:
        await res.edit("He?? bir ??ey tap??lmad??, ??ngilis dilind?? i??l??m??lis??n!")
        return
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("???? Musiqi Siyah??s??", callback_data="playlist"),
                InlineKeyboardButton("Menyu ??? ", callback_data="menu"),
            ],
            [InlineKeyboardButton(text="Deezer-d?? Qulaq As ????", url=f"{url}")],
            [InlineKeyboardButton(text="??? Ba??la", callback_data="cls")],
        ]
    )
    file_path = await convert(wget.download(url))
    await res.edit("Generating Thumbnail")
    await generate_cover(requested_by, title, artist, duration, thumbnail)
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        await res.edit("adding in queue")
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.edit_text(f"???{bn}???= #?????? N??vb??y?? al??nd?? {position}")
    else:
        await res.edit_text(f"???{bn}???=?????? Oxuyur.....")

        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            res.edit("Qrup z??ngi a????q deyil, ona qo??ula bilmir??m")
            return

    await res.delete()

    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"Oxuyur [{title}]({url}) Deezer t??r??find??n",
    )
    os.remove("final.png")


@Client.on_message(filters.command("2splay") & filters.group & ~filters.edited)
async def jiosaavn(client: Client, message_: Message):
    global que
    lel = await message_.reply("???? **Proses gedir**")
    administrators = await get_administrators(message_.chat)
    chid = message_.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "MusicAzE????????????"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await client.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message_.from_user.id:
                if message_.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Kanal??n??za asistan ??lav?? etm??yi unutmay??n</b>",
                    )
                    pass
                try:
                    invitelink = await client.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>??vv??lc?? m??ni qrupunuzun admin kimi ??lav?? edin</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message_.chat.id, "S??sli S??hb??td??-d?? musiqi oxumaq ??????n bu qrupa qo??uldum"
                    )
                    await lel.edit(
                        "<b>Asistan userbot s??hb??tiniz?? qat??ld??</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>???? Flood X??tas?? ???? \n??stifad????i {user.first_name} userbot ??????n a????r ist??kl??r s??b??bind??n qrupunuza qo??ula bilm??di! ??stifad????inin qrupda qada??an olunmad??????ndan ??min olun."
                        "\n\nV?? ya Manuel olaraq qrupunuza Asistan ??lav?? edin v?? yenid??n c??hd edin</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            "<i> Asistan Userbot Bu s??hb??td?? deyils??, admind??n ilk d??f?? /play komandas??n?? g??nd??rm??sini v?? ya asistan?? manuel ??lav?? etm??sini ist??yin</i>"
        )
        return
    requested_by = message_.from_user.first_name
    chat_id = message_.chat.id
    text = message_.text.split(" ", 1)
    query = text[1]
    res = lel
    await res.edit(f"Axtar??l??r ???????? `{query}` saavn")
    try:
        songs = await arq.saavn(query)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        sname = songs.result[0].song
        slink = songs.result[0].media_url
        ssingers = songs.result[0].singers
        sthumb = songs.result[0].image
        sduration = int(songs.result[0].duration)
    except Exception as e:
        await res.edit("He?? bir ??ey tap??lmad?? !, ??ngilis dilind?? i??l??m??lis??n.")
        print(str(e))
        return
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("???? Musiqi Siyah??s??", callback_data="playlist"),
                InlineKeyboardButton("Menyu ??? ", callback_data="menu"),
            ],
            [
                InlineKeyboardButton(
                    text="Musiqi Kanal??m??z", url=f"https://t.me/{updateschannel}"
                )
            ],
            [InlineKeyboardButton(text="??? Ba??la", callback_data="cls")],
        ]
    )
    file_path = await convert(wget.download(slink))
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.delete()
        m = await client.send_photo(
            chat_id=message_.chat.id,
            reply_markup=keyboard,
            photo="final.png",
            caption=f"???{bn}???=#?????? N??vb??y?? al??nd?? {position}",
        )

    else:
        await res.edit_text(f"{bn}=?????? Oxuyur.....")
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            res.edit("Qrup z??ngi a????q deyil, ona qo??ula bilmir??m")
            return
    await res.edit("Generating Thumbnail.")
    await generate_cover(requested_by, sname, ssingers, sduration, sthumb)
    await res.delete()
    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"Playing {sname} Via Jiosaavn",
    )
    os.remove("final.png")


# Have u read all. If read RESPECT :-)
