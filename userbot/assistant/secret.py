import json
import os
import re

from telethon.events import CallbackQuery

from userbot import catub


@catub.tgbot.on(CallbackQuery(data=re.compile(b"secret_(.*)")))
async def on_plug_in_callback_query_handler(event):
    timestamp = int(event.pattern_match.group(1).decode("UTF-8"))
    if os.path.exists("./userbot/secrets.txt"):
        jsondata = json.load(open("./userbot/secrets.txt"))
        try:
            message = jsondata[f"{timestamp}"]
            userid = message["userid"]
            ids = [userid, catub.uid]
            if event.query.user_id in ids:
                encrypted_tcxt = message["text"]
                reply_pop_up_alert = encrypted_tcxt
            else:
                reply_pop_up_alert = "جناپ چرا سعی داری به این پیام نگاه کنی برو به کار زشتت فکر کن"
        except KeyError:
            reply_pop_up_alert = "این پیام دیگر در سرور وجود ندارد"
    else:
        reply_pop_up_alert = "این پیام دیگر وجود ندارد"
    await event.answer(reply_pop_up_alert, cache_time=0, alert=True)
