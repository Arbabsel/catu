import random
import re
from datetime import datetime

from telethon import Button, functions
from telethon.events import CallbackQuery
from telethon.utils import get_display_name

from userbot import catub
from userbot.core.logger import logging

from ..Config import Config
from ..core.managers import edit_delete, edit_or_reply
from ..helpers.utils import _format, get_user_from_event, reply_id
from ..sql_helper import global_collectionjson as sql
from ..sql_helper import global_list as sqllist
from ..sql_helper import pmpermit_sql
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from . import mention

plugin_category = "utils"
LOGS = logging.getLogger(__name__)
cmdhd = Config.COMMAND_HAND_LER


async def do_pm_permit_action(event, chat):  # sourcery no-metrics
    reply_to_id = await reply_id(event)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    me = await event.client.get_me()
    mention = f"[{chat.first_name}](tg://user?id={chat.id})"
    my_mention = f"[{me.first_name}](tg://user?id={me.id})"
    first = chat.first_name
    last = chat.last_name
    fullname = f"{first} {last}" if last else first
    username = f"@{chat.username}" if chat.username else mention
    userid = chat.id
    my_first = me.first_name
    my_last = me.last_name
    my_fullname = f"{my_first} {my_last}" if my_last else my_first
    my_username = f"@{me.username}" if me.username else my_mention
    if str(chat.id) not in PM_WARNS:
        PM_WARNS[str(chat.id)] = 0
    try:
        MAX_FLOOD_IN_PMS = int(gvarstatus("MAX_FLOOD_IN_PMS") or 6)
    except (ValueError, TypeError):
        MAX_FLOOD_IN_PMS = 6
    totalwarns = MAX_FLOOD_IN_PMS + 1
    warns = PM_WARNS[str(chat.id)] + 1
    remwarns = totalwarns - warns
    if PM_WARNS[str(chat.id)] >= MAX_FLOOD_IN_PMS:
        try:
            if str(chat.id) in PMMESSAGE_CACHE:
                await event.client.delete_messages(
                    chat.id, PMMESSAGE_CACHE[str(chat.id)]
                )
                del PMMESSAGE_CACHE[str(chat.id)]
        except Exception as e:
            LOGS.info(str(e))
        custompmblock = gvarstatus("pmblock") or None
        if custompmblock is not None:
            USER_BOT_WARN_ZERO = custompmblock.format(
                mention=mention,
                first=first,
                last=last,
                fullname=fullname,
                username=username,
                userid=userid,
                my_first=my_first,
                my_last=my_last,
                my_fullname=my_fullname,
                my_username=my_username,
                my_mention=my_mention,
                totalwarns=totalwarns,
                warns=warns,
                remwarns=remwarns,
            )
        else:
            USER_BOT_WARN_ZERO = f"**شما اسپم میکردید** {my_mention}**به دلیل اسپم بلاک شدین❌**"
        msg = await event.reply(USER_BOT_WARN_ZERO)
        await event.client(functions.contacts.BlockRequest(chat.id))
        the_message = f"#BLOCKED_PM\
                            \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                            \n**Message Count:** {PM_WARNS[str(chat.id)]}"
        del PM_WARNS[str(chat.id)]
        sql.del_collection("pmwarns")
        sql.del_collection("pmmessagecache")
        sql.add_collection("pmwarns", PM_WARNS, {})
        sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
        try:
            return await event.client.send_message(
                BOTLOG_CHATID,
                the_message,
            )
        except BaseException:
            return
    custompmpermit = gvarstatus("pmpermit_txt") or None
    if custompmpermit is not None:
        USER_BOT_NO_WARN = custompmpermit.format(
            mention=mention,
            first=first,
            last=last,
            fullname=fullname,
            username=username,
            userid=userid,
            my_first=my_first,
            my_last=my_last,
            my_fullname=my_fullname,
            my_username=my_username,
            my_mention=my_mention,
            totalwarns=totalwarns,
            warns=warns,
            remwarns=remwarns,
        )
    elif gvarstatus("pmmenu") is None:
        USER_BOT_NO_WARN = f"""__جناپ__ {mention}__ من هنوز شمارا برای پیام شخصی تایید نکردم 

😐 {warns}/{totalwarns} هشدار میدم تا زمانی که ربات بلاکت نکرده

یکی از گزینه های زیر را انتخاب کنید تا دلیل پیام خود را مشخص کنید و منتظر بمانید تا آن را بررسی کنم. __⬇️"""
    else:
        USER_BOT_NO_WARN = f"""__جناپ__ {mention}__من هنوز شمارا برای پیام شخصی تایید نکردم

😐 {warns}/{totalwarns} هشدار بهت میدم تا زمانی که ربات بلاکت نکرده.

پیویمو اسپم نکن.دلیل بگو و منتظر جواب باش__"""
    addgvar("pmpermit_text", USER_BOT_NO_WARN)
    PM_WARNS[str(chat.id)] += 1
    try:
        if gvarstatus("pmmenu") is None:
            results = await event.client.inline_query(
                Config.TG_BOT_USERNAME, "pmpermit"
            )
            msg = await results[0].click(chat.id, reply_to=reply_to_id, hide_via=True)
        else:
            PM_PIC = gvarstatus("pmpermit_pic")
            if PM_PIC:
                CAT = [x for x in PM_PIC.split()]
                PIC = list(CAT)
                CAT_IMG = random.choice(PIC)
            else:
                CAT_IMG = None
            if CAT_IMG is not None:
                msg = await event.client.send_file(
                    chat.id,
                    CAT_IMG,
                    caption=USER_BOT_NO_WARN,
                    reply_to=reply_to_id,
                    force_document=False,
                )
            else:
                msg = await event.client.send_message(
                    chat.id, USER_BOT_NO_WARN, reply_to=reply_to_id
                )
    except Exception as e:
        LOGS.error(e)
        msg = await event.reply(USER_BOT_NO_WARN)
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    PMMESSAGE_CACHE[str(chat.id)] = msg.id
    sql.del_collection("pmwarns")
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmwarns", PM_WARNS, {})
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})


async def do_pm_options_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = "__⚠از پیام بالا گزینه را انتخاب کنید و منتظر بمانید. پیویمو اسپم نکن، این آخرین هشدار شماست.__"
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = "**اگر درست یادم باشد در پیام قبلی خود اشاره کردم که اینجا مکان مناسبی برای اسپم کردن شما نیست.\\\x1fگرچه شما آن پیام را نادیده گرفتید. بنابراین، من به سادگی شما را مسدود کردم.\\\x1fحالا نمی‌توانید کاری انجام دهید، مگر اینکه استاد من آنلاین شود و شما را رفع انسداد کند.**"

    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                            \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                            \n**دلیل:** __او هیچ یک از گزینه های ارائه شده را انتخاب نکرد و به پیام دادن ادامه داد__"
    sqllist.rm_from_list("pmoptions", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_enquire_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = """__هی! کمی صبر داشته باش 😅 استاد من هنوز پیام شما را ندیده است.  \
__اگر او بخواهد، وقتی او آنلاین شود، استاد من پاسخ خواهد داد__
**🤖 لطفا از اسپم خودداری کنید مگر اینکه بخواهید بلاک و گزارش شوید 🤖**"""
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = "**🤖 اگر درست یادم باشد در پیام قبلی خود اشاره کردم که اینجا مکان مناسبی برای اسپم کردن شما نیست.\\\x1fاگرچه شما آن پیام را نادیده گرفتید. بنابراین، من به سادگی شما را بلاک کردم. \\\x1fحالا کاری نمیتونی بکنی مگر اینکه استاد من انلاین بشه و رفع بلاکت کنه😌**"

    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                \n**دلیل:** __او گزینه استعلام را انتخاب کرد، اما پس از آن که به او گفته شد صبر نکرد و همچنان به پیام ادامه داد و مسدود شد__"
    sqllist.rm_from_list("pmenquire", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_request_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = """__هی صبر داشته باش 🙂 استاد من هنوز پیام شما را ندیده است. \
استاد من معمولاً به مردم پاسخ می‌دهد، هرچند در مورد برخی از کاربران استثنایی نمی‌داند.__
**🤖لطفاً از ارسال هرزنامه خودداری کنید مگر اینکه بخواهید بلاک و گزارش شوید🤖**"""
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = "**اگر درست یادم باشد در پیام قبلی خود اشاره کردم که اینجا مکان مناسبی برای اسپم کردن شما نیست. \\\x1fهرچند تو به من توجه نکردی و به من پیام دادی. بنابراین، من به سادگی شما را بلاک کردم. \\\x1fحالا کاری نمیتونی بکنی مگر اینکه استاد من انلاین بشه و تو رو انبلاک کنه.**"

    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                \n**دلیل:** __او گزینه درخواست را انتخاب کرد اما پس از اینکه به او گفته شد که مسدود شده است منتظر ماند.__"
    sqllist.rm_from_list("pmrequest", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_chat_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = """__هی! من در حال حاضر مشغول هستم، قبلاً از شما خواسته بودم که منتظر بمانید. بعد از تموم شدن کارم\
ما می توانیم صحبت کنیم اما درست نمی دانیم. امیدوارم متوجه شده باشی.__
__استاد من اگر بخواهد وقتی آنلاین شد پاسخ می دهد.__
**لطفاً از ارسال هرزنامه خودداری کنید مگر اینکه بخواهید بلاک و گزارش شوید.**"""
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = "**اگر به درستی یادم باشد در پیام قبلی خود اشاره کردم این مکان مناسبی برای اسپم کردن شما نیست.\\\x1fاگرچه شما آن پیام را نادیده گرفتید. بنابراین، من شما را به سادگی بلاک کردم 😌\\\x1fحالا کاری نمیتونی بکنی مگر اینکه استاد من انلاین بشه و تو رو انبلاک کنه.**"

    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                \n**دلیل:** __او گزینه چت را انتخاب کرد اما پس از اینکه به او گفته شد که مسدود شده است صبر نکرد__"
    sqllist.rm_from_list("pmchat", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_spam_action(event, chat):
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    USER_BOT_WARN_ZERO = "**اگر به درستی یادم باشد در پیام قبلی خود اشاره کردم این مکان مناسبی برای اسپم کردن شما نیست.\\\x1fاگرچه شما آن پیام را نادیده گرفتید. بنابراین، من به سادگی شما را بلاک کردم. \\\x1fحالا کاری نمیتونی بکنی مگر اینکه استاد من انلاین بشه و تو رو انبلاک کنه.**"

    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                            \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                            \n**دلیل:** او گزینه اسپم را انتخاب کرد و دوباره پیام داد"
    sqllist.rm_from_list("pmspam", chat.id)
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


@catub.cat_cmd(incoming=True, func=lambda e: e.is_private, edited=False, forword=None)
async def on_new_private_message(event):
    if gvarstatus("pmpermit") is None:
        return
    chat = await event.get_chat()
    if chat.bot or chat.verified:
        return
    if pmpermit_sql.is_approved(chat.id):
        return
    if str(chat.id) in sqllist.get_collection_list("pmspam"):
        return await do_pm_spam_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmchat"):
        return await do_pm_chat_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmrequest"):
        return await do_pm_request_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmenquire"):
        return await do_pm_enquire_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmoptions"):
        return await do_pm_options_action(event, chat)
    await do_pm_permit_action(event, chat)


@catub.cat_cmd(outgoing=True, func=lambda e: e.is_private, edited=False, forword=None)
async def you_dm_other(event):
    if gvarstatus("pmpermit") is None:
        return
    chat = await event.get_chat()
    if chat.bot or chat.verified:
        return
    if str(chat.id) in sqllist.get_collection_list("pmspam"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmchat"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmrequest"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmenquire"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmoptions"):
        return
    if event.text and event.text.startswith(
        (
            f"{cmdhd}block",
            f"{cmdhd}disapprove",
            f"{cmdhd}a",
            f"{cmdhd}da",
            f"{cmdhd}approve",
        )
    ):
        return
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    start_date = str(datetime.now().strftime("%B %d, %Y"))
    if not pmpermit_sql.is_approved(chat.id) and str(chat.id) not in PM_WARNS:
        pmpermit_sql.approve(
            chat.id, get_display_name(chat), start_date, chat.username, "For Outgoing"
        )
        try:
            PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
        except AttributeError:
            PMMESSAGE_CACHE = {}
        if str(chat.id) in PMMESSAGE_CACHE:
            try:
                await event.client.delete_messages(
                    chat.id, PMMESSAGE_CACHE[str(chat.id)]
                )
            except Exception as e:
                LOGS.info(str(e))
            del PMMESSAGE_CACHE[str(chat.id)]
        sql.del_collection("pmmessagecache")
        sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})


@catub.tgbot.on(CallbackQuery(data=re.compile(rb"show_pmpermit_options")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit these options are for users who messages you, not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = f"""خب، اکنون به منوی استاد من دسترسی دارید, {mention}.
__و بیاید به من بگویید که چرا اینجا هستید__

**یکی از دلایل زیر را برای حضور شما در اینجا انتخاب کنید:**"""
    buttons = [
        (Button.inline(text="پرس و جو کرن چیزی", data="to_enquire_something"),),
        (Button.inline(text="درخواست چیزی", data="to_request_something"),),
        (Button.inline(text="برای چت کردن", data="to_chat_with_my_master"),),
        (
            Button.inline(
                text="اسپم کردن پی وی",
                data="to_spam_my_master_inbox",
            ),
        ),
    ]
    sqllist.add_to_list("pmoptions", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    await event.edit(text, buttons=buttons)


@catub.tgbot.on(CallbackQuery(data=re.compile(rb"to_enquire_something")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit these options for user who messages you. not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = """__باشه. درخواست شما ثبت شد اکنون پی وی من را اسپم نکنید.  \
 استاد من در حال حاضر مشغول است، وقتی استاد من آنلاین شد پیام شما را بررسی می کند و به شما پاسخ میدهد.\
سپس ما می توانیم این گفتگو را بیشتر گسترش دهیم، اما نه در حال حاضر.__"""
    sqllist.add_to_list("pmenquire", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@catub.tgbot.on(CallbackQuery(data=re.compile(rb"to_request_something")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit this options for user who messages you. not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = """__باشه. من به استادم در این مورد اطلاع داده ام. وقتی آنلاین می شود \
 وقتی استاد من آنلاین شود، او به این چت نگاه می کند و به شما پاسخ میدهد تا بتوانیم یک گپ دوستانه داشته باشیم.__\

**🤖اما در حال حاضر لطفا از اسپم خودداری کنید مگر اینکه بخواهید بلاک شوید🤖**"""
    sqllist.add_to_list("pmrequest", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@catub.tgbot.on(CallbackQuery(data=re.compile(rb"to_chat_with_my_master")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit these options are for users who message you. not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = """__بله مطمئنم که ما می توانیم یک چت دوستانه داشته باشیم اما نه در حال حاضر. ما نمی توانیم فعلا چتی داشته باشیم
در حال حاضر کمی سرم شلوغ است. وقتی آنلاین بشم. من به شما پیام خواهم داد، این مطمئناً.__"""
    sqllist.add_to_list("pmchat", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@catub.tgbot.on(CallbackQuery(data=re.compile(rb"to_spam_my_master_inbox")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit these options are for users who message you. not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = "`███████▄▄███████████▄\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓███░░░░░░░░░░░░█\
         \n██████▀▀▀█░░░░██████▀ \
         \n░░░░░░░░░█░░░░█\
         \n░░░░░░░░░░█░░░█\
         \n░░░░░░░░░░░█░░█\
         \n░░░░░░░░░░░█░░█\
         \n░░░░░░░░░░░░▀▀`\
         \n**جناپ اینجا جای کصشعر گفتن نیست برو یجا دیگه \
         \n\nو این آخرین اخطار شماست اگر یک پیام دیگر بفرستید به طور خودکار بلاک خواهید شد🤖**"
    sqllist.add_to_list("pmspam", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmspam").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@catub.cat_cmd(
    pattern="pmguard (on|off)$",
    command=("pmguard", plugin_category),
    info={
        "header": "To turn on or turn off pmpermit.",
        "usage": "{tr}pmguard on/off",
    },
)
async def pmpermit_on(event):
    "Turn on/off pmpermit."
    input_str = event.pattern_match.group(1)
    if input_str == "on":
        if gvarstatus("pmpermit") is None:
            addgvar("pmpermit", "true")
            await edit_delete(
                event, "__👀 Pmpermit has been enabled for your account successfully 👀.__"
            )
        else:
            await edit_delete(event, "__Pmpermit is already enabled for your account__")
    elif gvarstatus("pmpermit") is not None:
        delgvar("pmpermit")
        await edit_delete(
            event, "__🧐 Pmpermit has been disabled for your account successfully 🧐__"
        )
    else:
        await edit_delete(event, "__Pmpermit is already disabled for your account__")


@catub.cat_cmd(
    pattern="pmmenu (on|off)$",
    command=("pmmenu", plugin_category),
    info={
        "header": "To turn on or turn off pmmenu.",
        "usage": "{tr}pmmenu on/off",
    },
)
async def pmpermit_on(event):
    "Turn on/off pmmenu."
    input_str = event.pattern_match.group(1)
    if input_str == "off":
        if gvarstatus("pmmenu") is None:
            addgvar("pmmenu", "false")
            await edit_delete(
                event,
                "__Pmpermit Menu has been disabled for your account successfully.__",
            )
        else:
            await edit_delete(
                event, "__Pmpermit Menu is already disabled for your account__"
            )
    elif gvarstatus("pmmenu") is not None:
        delgvar("pmmenu")
        await edit_delete(
            event, "__Pmpermit Menu has been enabled for your account successfully__"
        )
    else:
        await edit_delete(
            event, "__Pmpermit Menu is already enabled for your account__"
        )


@catub.cat_cmd(
    pattern="(a|approve)(?:\s|$)([\s\S]*)",
    command=("approve", plugin_category),
    info={
        "header": "To approve user to direct message you.",
        "usage": [
            "{tr}a/approve <username/reply reason> in group",
            "{tr}a/approve <reason> in pm",
        ],
    },
)
async def approve_p_m(event):  # sourcery no-metrics
    "To approve user to pm"
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(2)
    else:
        user, reason = await get_user_from_event(event, secondgroup=True)
        if not user:
            return
    if not reason:
        reason = "Not mentioned"
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if not pmpermit_sql.is_approved(user.id):
        if str(user.id) in PM_WARNS:
            del PM_WARNS[str(user.id)]
        start_date = str(datetime.now().strftime("%B %d, %Y"))
        pmpermit_sql.approve(
            user.id, get_display_name(user), start_date, user.username, reason
        )
        chat = user
        if str(chat.id) in sqllist.get_collection_list("pmspam"):
            sqllist.rm_from_list("pmspam", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmchat"):
            sqllist.rm_from_list("pmchat", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmrequest"):
            sqllist.rm_from_list("pmrequest", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmenquire"):
            sqllist.rm_from_list("pmenquire", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmoptions"):
            sqllist.rm_from_list("pmoptions", chat.id)
        await edit_delete(
            event,
            f"__Approved to pm__ [{user.first_name}](tg://user?id={user.id})\n**Reason :** __{reason}__",
        )
        try:
            PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
        except AttributeError:
            PMMESSAGE_CACHE = {}
        if str(user.id) in PMMESSAGE_CACHE:
            try:
                await event.client.delete_messages(
                    user.id, PMMESSAGE_CACHE[str(user.id)]
                )
            except Exception as e:
                LOGS.info(str(e))
            del PMMESSAGE_CACHE[str(user.id)]
        sql.del_collection("pmwarns")
        sql.del_collection("pmmessagecache")
        sql.add_collection("pmwarns", PM_WARNS, {})
        sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    else:
        await edit_delete(
            event,
            f"[{user.first_name}](tg://user?id={user.id}) __is already in approved list__",
        )


@catub.cat_cmd(
    pattern="(da|disapprove)(?:\s|$)([\s\S]*)",
    command=("disapprove", plugin_category),
    info={
        "header": "To disapprove user to direct message you.",
        "note": "This command works only for approved users",
        "options": {"all": "To disapprove all approved users"},
        "usage": [
            "{tr}da/disapprove <username/reply> in group",
            "{tr}da/disapprove in pm",
            "{tr}da/disapprove all - To disapprove all users.",
        ],
    },
)
async def disapprove_p_m(event):
    "To disapprove user to direct message you."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(2)

    else:
        reason = event.pattern_match.group(2)
        if reason != "all":
            user, reason = await get_user_from_event(event, secondgroup=True)
            if not user:
                return
    if reason == "all":
        pmpermit_sql.disapprove_all()
        return await edit_delete(
            event, "__Ok! I have disapproved everyone successfully.__"
        )
    if not reason:
        reason = "Not Mentioned."
    if pmpermit_sql.is_approved(user.id):
        pmpermit_sql.disapprove(user.id)
        await edit_or_reply(
            event,
            f"[{user.first_name}](tg://user?id={user.id}) __is disapproved to personal message me.__\n**Reason:**__ {reason}__",
        )
    else:
        await edit_delete(
            event,
            f"[{user.first_name}](tg://user?id={user.id}) __is not yet approved__",
        )


@catub.cat_cmd(
    pattern="block(?:\s|$)([\s\S]*)",
    command=("block", plugin_category),
    info={
        "header": "To block user to direct message you.",
        "usage": [
            "{tr}block <username/reply reason> in group",
            "{tr}block <reason> in pm",
        ],
    },
)
async def block_p_m(event):
    "To block user to direct message you."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(1)
    else:
        user, reason = await get_user_from_event(event)
        if not user:
            return
    if not reason:
        reason = "Not Mentioned."
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(user.id) in PM_WARNS:
        del PM_WARNS[str(user.id)]
    if str(user.id) in PMMESSAGE_CACHE:
        try:
            await event.client.delete_messages(user.id, PMMESSAGE_CACHE[str(user.id)])
        except Exception as e:
            LOGS.info(str(e))
        del PMMESSAGE_CACHE[str(user.id)]
    if pmpermit_sql.is_approved(user.id):
        pmpermit_sql.disapprove(user.id)
    sql.del_collection("pmwarns")
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmwarns", PM_WARNS, {})
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    await event.client(functions.contacts.BlockRequest(user.id))
    await edit_delete(
        event,
        f"[{user.first_name}](tg://user?id={user.id}) __is blocked, he can no longer personal message you.__\n**Reason:** __{reason}__",
    )


@catub.cat_cmd(
    pattern="unblock(?:\s|$)([\s\S]*)",
    command=("unblock", plugin_category),
    info={
        "header": "To unblock a user.",
        "usage": [
            "{tr}unblock <username/reply reason> in group",
            "{tr}unblock <reason> in pm",
        ],
    },
)
async def unblock_pm(event):
    "To unblock a user."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(1)
    else:
        user, reason = await get_user_from_event(event)
        if not user:
            return
    if not reason:
        reason = "Not Mentioned."
    await event.client(functions.contacts.UnblockRequest(user.id))
    await event.edit(
        f"[{user.first_name}](tg://user?id={user.id}) __is unblocked he/she can personal message you from now on.__\n**Reason:** __{reason}__"
    )


@catub.cat_cmd(
    pattern="l(ist)?a(pproved)?$",
    command=("listapproved", plugin_category),
    info={
        "header": "To see list of approved users.",
        "usage": [
            "{tr}listapproved",
        ],
    },
)
async def approve_p_m(event):
    "To see list of approved users."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __to work this plugin__",
        )
    approved_users = pmpermit_sql.get_all_approved()
    APPROVED_PMs = "**Current Approved PMs**\n\n"
    if len(approved_users) > 0:
        for user in approved_users:
            APPROVED_PMs += f"• 👤 {_format.mentionuser(user.first_name , user.user_id)}\n**ID:** `{user.user_id}`\n**UserName:** @{user.username}\n**Date: **__{user.date}__\n**Reason: **__{user.reason}__\n\n"
    else:
        APPROVED_PMs = "`You haven't approved anyone yet`"
    await edit_or_reply(
        event,
        APPROVED_PMs,
        file_name="approvedpms.txt",
        caption="`Current Approved PMs`",
    )
