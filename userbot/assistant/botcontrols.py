import asyncio
from datetime import datetime

from telethon.errors import BadRequestError, FloodWaitError, ForbiddenError

from userbot import catub

from ..Config import Config
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..helpers import reply_id, time_formatter
from ..helpers.utils import _format
from ..sql_helper.bot_blacklists import check_is_black_list, get_all_bl_users
from ..sql_helper.bot_starters import del_starter_from_db, get_all_starters
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from . import BOTLOG, BOTLOG_CHATID
from .botmanagers import (
    ban_user_from_bot,
    get_user_and_reason,
    progress_str,
    unban_user_from_bot,
)

LOGS = logging.getLogger(__name__)

plugin_category = "bot"
botusername = Config.TG_BOT_USERNAME
cmhd = Config.COMMAND_HAND_LER


@catub.bot_cmd(pattern="^/help$", from_users=Config.OWNER_ID)
async def bot_help(event):
    await event.reply(
        f"""دستورات موجود در ربات عبارتند از:
**توجه : **__این دستورات فقط در این ربات کار می کنند__ {botusername}

• **دستور : **/uinfo <reply to user message>
• **اطلاعات : **__متوجه شده‌اید که استیکرها/اموجی‌های فوروارد شده دارای برچسب فوروارد نیستند، بنابراین می‌توانید کاربری را که آن پیام‌ها را با این دستور ارسال کرده است شناسایی کنید.__
• **توجه : **__برای همه پیام های فوروارد شده کار می کند. حتی برای کاربرانی که به هیچ کس اجازه ارسال پیام نمی دهند.__

• **دستور : **/ban <reason> or /ban <username/userid> <reason>
• **اطلاعات : **__به یک پیام کاربر با دلیل پاسخ دهید تا از آنجایی که شما از ربات منع شده اید به او اطلاع داده می شود و پیام های او بیشتر برای شما ارسال نمی شود.__
• **توجه : **__بدون ارسال دلیل کار نخواهد کرد __

• **دستور : **/unban <reason(optional)> or /unban <username/userid>
• **اطلاعات : **__به پیام کاربر پاسخ دهید یا نام کاربری/کاربر را برای لغو بن از ربات ارائه دهید.__
• **توجه : **__برای بررسی لیست کاربران بن شده استفاده کنید__ `{cmhd}bblist`.

• **دستور : **/broadcast
• **اطلاعات : **__به یک پیام پاسخ دهید تا برای هر کاربری که ربات شما را راه اندازی کرده است پخش شود. برای دریافت لیست کاربران استفاده کنید__ `{cmhd}bot_users`.
• **توجه : **__اگر کاربر ربات را متوقف/بلاک کرد، از پایگاه داده شما حذف خواهد شد که از لیست bot_starters پاک خواهد شد.__
"""
    )


@catub.bot_cmd(pattern="^/broadcast$", from_users=Config.OWNER_ID)
async def bot_broadcast(event):
    replied = await event.get_reply_message()
    if not replied:
        return await event.reply("ابتدا به پیامی برای پخش پاسخ دهید!")
    start_ = datetime.now()
    br_cast = await replied.reply("Broadcasting ...")
    blocked_users = []
    count = 0
    bot_users_count = len(get_all_starters())
    if bot_users_count == 0:
        return await event.reply("`هنوز کسی ربات شما را راه اندازی نکرده است.`")
    users = get_all_starters()
    if users is None:
        return await event.reply("`هنگام دریافت کاربران خطاهایی رخ داد.`")
    for user in users:
        try:
            await event.client.send_message(
                int(user.user_id), "🔊شما یک پیام **جدید**پخش کرده اید"
            )
            await event.client.send_message(int(user.user_id), replied)
            await asyncio.sleep(0.8)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except (BadRequestError, ValueError, ForbiddenError):
            del_starter_from_db(int(user.user_id))
        except Exception as e:
            LOGS.error(str(e))
            if BOTLOG:
                await event.client.send_message(
                    BOTLOG_CHATID, f"**خطا هنگام پخش❌**\n`{e}`"
                )

        else:
            count += 1
            if count % 5 == 0:
                try:
                    prog_ = (
                        "🔊 Broadcasting ...\n\n"
                        + progress_str(
                            total=bot_users_count,
                            current=count + len(blocked_users),
                        )
                        + f"\n\n• ✔️ **موفق** :  `{count}`\n"
                        + f"• ✖️ **ناموفق** :  `{len(blocked_users)}`"
                    )
                    await br_cast.edit(prog_)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
    end_ = datetime.now()
    b_info = f"🔊 پیام با موفقیت پخش شد ➜  <b>{count} users.</b>"
    if len(blocked_users) != 0:
        b_info += f"\n🚫  <b>{len(blocked_users)} users</b> اخیرا ربات شما را مسدود کرده است، بنابراین حذف شده اند."
    b_info += (
        f"\n⏳  <code>فرآیند انجام شد: {time_formatter((end_ - start_).seconds)}</code>."
    )
    await br_cast.edit(b_info, parse_mode="html")


@catub.cat_cmd(
    pattern="bot_users$",
    command=("bot_users", plugin_category),
    info={
        "header": "To get users list who started bot.",
        "description": "To get compelete list of users who started your bot",
        "usage": "{tr}bot_users",
    },
)
async def ban_starters(event):
    "To get list of users who started bot."
    ulist = get_all_starters()
    if len(ulist) == 0:
        return await edit_delete(event, "`هنوز کسی ربات شما را راه اندازی نکرده است.`")
    msg = "**The list of users who started your bot are :\n\n**"
    for user in ulist:
        msg += f"• 👤 {_format.mentionuser(user.first_name , user.user_id)}\n**ایدی:** `{user.user_id}`\n**نام:** @{user.username}\n**تاریخ: **__{user.date}__\n\n"
    await edit_or_reply(event, msg)


@catub.bot_cmd(pattern="^/ban\\s+([\\s\\S]*)", from_users=Config.OWNER_ID)
async def ban_botpms(event):
    user_id, reason = await get_user_and_reason(event)
    reply_to = await reply_id(event)
    if not user_id:
        return await event.client.send_message(
            event.chat_id, "`من نمی توانم کاربری برای بن پیدا کنم`", reply_to=reply_to
        )
    if not reason:
        return await event.client.send_message(
            event.chat_id, "`برای بن کردن کاربر ابتدا دلیل ارائه کنید`", reply_to=reply_to
        )
    try:
        user = await event.client.get_entity(user_id)
        user_id = user.id
    except Exception as e:
        return await event.reply(f"**Error:**\n`{e}`")
    if user_id == Config.OWNER_ID:
        return await event.reply("من نمی توانم شما را ممنوع کنم استاد")
    check = check_is_black_list(user.id)
    if check:
        return await event.client.send_message(
            event.chat_id,
            f"#Already_banned\
            \nکاربر از قبل در لیست کاربران بن وجود دارد.\
            \n**دلیل بن کردن ربات:** `{check.reason}`\
            \n**تاریخ:** `{check.date}`.",
        )
    msg = await ban_user_from_bot(user, reason, reply_to)
    await event.reply(msg)


@catub.bot_cmd(pattern="^/unban(?:\\s|$)([\\s\\S]*)", from_users=Config.OWNER_ID)
async def ban_botpms(event):
    user_id, reason = await get_user_and_reason(event)
    reply_to = await reply_id(event)
    if not user_id:
        return await event.client.send_message(
            event.chat_id, "`من نمی توانم کاربری برای لغو بن پیدا کنم`", reply_to=reply_to
        )
    try:
        user = await event.client.get_entity(user_id)
        user_id = user.id
    except Exception as e:
        return await event.reply(f"**Error:**\n`{e}`")
    check = check_is_black_list(user.id)
    if not check:
        return await event.client.send_message(
            event.chat_id,
            f"#User_Not_Banned\
            \n👤 {_format.mentionuser(user.first_name , user.id)} در لیست کاربران بن وجود ندارد.",
        )
    msg = await unban_user_from_bot(user, reason, reply_to)
    await event.reply(msg)


@catub.cat_cmd(
    pattern="bblist$",
    command=("bblist", plugin_category),
    info={
        "header": "To get users list who are banned in bot.",
        "description": "To get list of users who are banned in bot.",
        "usage": "{tr}bblist",
    },
)
async def ban_starters(event):
    "To get list of users who are banned in bot."
    ulist = get_all_bl_users()
    if len(ulist) == 0:
        return await edit_delete(event, "`هنوز کسی در ربات شما بن نشده است.`")
    msg = "**لیست کاربرانی که در ربات شما بن شده اند عبارتند از:\n\n**"
    for user in ulist:
        msg += f"• 👤 {_format.mentionuser(user.first_name , user.chat_id)}\n**ایدی:** `{user.chat_id}`\n**نام:** @{user.username}\n**تاریخ: **__{user.date}__\n**دلیل:** __{user.reason}__\n\n"
    await edit_or_reply(event, msg)


@catub.cat_cmd(
    pattern="bot_antif (on|off)$",
    command=("bot_antif", plugin_category),
    info={
        "header": "To enable or disable bot antiflood.",
        "description": "if it was turned on then after 10 messages or 10 edits of same messages in less time then your bot auto loacks them.",
        "usage": [
            "{tr}bot_antif on",
            "{tr}bot_antif off",
        ],
    },
)
async def ban_antiflood(event):
    "To enable or disable bot antiflood."
    input_str = event.pattern_match.group(1)
    if input_str == "on":
        if gvarstatus("bot_antif") is not None:
            return await edit_delete(event, "`قبلا آنتی اسپم فعال شده است`")
        addgvar("bot_antif", True)
        await edit_delete(event, "`آنتی اسپم فعال شد`")
    elif input_str == "off":
        if gvarstatus("bot_antif") is None:
            return await edit_delete(event, "`قبلا آنتی اسپم غیرفعال شده است`")
        delgvar("bot_antif")
        await edit_delete(event, "`آنتی اسپم غیرفعال شد`")
