import random

from telethon.utils import get_display_name

from userbot import catub

from ..core.managers import edit_delete, edit_or_reply
from ..helpers import get_user_from_event, rs_client
from ..sql_helper.chatbot_sql import (
    addai,
    get_all_users,
    get_users,
    is_added,
    remove_ai,
    remove_all_users,
    remove_users,
)
from ..sql_helper.globals import gvarstatus

plugin_category = "fun"

tired_response = [
    "کیرم تو کص مادرت ولد زنا",
    "ریدم دهنه مادرت کیری ننه زیر خواب",
    "تف تو لا  ممه های مادرت😔",
    "زجه بزن ننه کاندومی",
    "انقد زجه بزن تا مادرت حمله بشه",
    "کیر عربی تو کص ننت داش خخخ",
    "ننتو محوی گاییدم تو الان مادرتو نمیبینی گاییده شده ولی من دارم میبینم  ",
    "کص خارت تیز باش عع",
    "ای کص ناموست ننه زیر",
    "ننت زیر چیکار میکنه داش",
    "آبجیتو همینجا حامله کردم",
    "مادرت چه ممه هایی داره بزارم لا ممه هاش🤤",
    "بیا برو تو کص ننت درم ببند باوو",
    "حرص میخوری که چی تخم خر آخرش ننت ماله خودمه:)",
    "صیک کن تو کص خارت نبینمت حرومی",
    "کیرمو کردم لا ممه های آبجیت",
    "الان انقد ننتو گاییدم خسته نشدی؟خخ😂",
    "کصکش من باباتم به پدرت احترام بزار ننتو گاییدم ",
]


@catub.cat_cmd(
    pattern="addai$",
    command=("addai", plugin_category),
    info={
        "header": "به کاربر پاسخ دهید تا انمی فعال شود",
        "usage": "{tr}addai <reply>",
    },
)
async def add_chatbot(event):
    "To enable ai for the replied person"
    if event.reply_to_msg_id is None:
        return await edit_or_reply(
            event, "`به کاربر پاسخ دهید تا انمی فعال شود`"
        )
    catevent = await edit_or_reply(event, "`درحال افزودن انمی...`")
    user, rank = await get_user_from_event(event, catevent, nogroup=True)
    if not user:
        return
    reply_msg = await event.get_reply_message()
    chat_id = event.chat_id
    user_id = reply_msg.sender_id
    if event.is_private:
        chat_name = user.first_name
        chat_type = "Personal"
    else:
        chat_name = get_display_name(await event.get_chat())
        chat_type = "Group"
    user_name = user.first_name
    user_username = user.username
    if is_added(chat_id, user_id):
        return await edit_or_reply(event, "`قبلا برای کاربر انمی فعال شده است`")
    try:
        addai(chat_id, user_id, chat_name, user_name, user_username, chat_type)
    except Exception as e:
        await edit_delete(catevent, f"**Error:**\n`{e}`")
    else:
        await edit_or_reply(catevent, "گاییده شدن کص ننت فعال شد")


@catub.cat_cmd(
    pattern="rmai$",
    command=("rmai", plugin_category),
    info={
        "header": "To stop ai for that user messages.",
        "usage": "{tr}rmai <reply>",
    },
)
async def remove_chatbot(event):
    "To stop ai for that user"
    if event.reply_to_msg_id is None:
        return await edit_or_reply(
            event, "به پیام یک کاربر پاسخ دهید تا انمی متوقف شود"
        )
    reply_msg = await event.get_reply_message()
    user_id = reply_msg.sender_id
    chat_id = event.chat_id
    if is_added(chat_id, user_id):
        try:
            remove_ai(chat_id, user_id)
        except Exception as e:
            await edit_delete(catevent, f"**Error:**\n`{e}`")
        else:
            await edit_or_reply(event, "انمی برای کاربر متوقف شد")
    else:
        await edit_or_reply(event, "برای کاربر انمی فعال نمیشود")


@catub.cat_cmd(
    pattern="delai( -a)?",
    command=("delai", plugin_category),
    info={
        "header": "To delete ai in this chat.",
        "description": "To stop ai for all enabled users in this chat only..",
        "flags": {"a": "To stop in all chats"},
        "usage": [
            "{tr}delai",
            "{tr}delai -a",
        ],
    },
)
async def delete_chatbot(event):
    "To delete ai in this chat."
    input_str = event.pattern_match.group(1)
    if input_str:
        lecho = get_all_users()
        if len(lecho) == 0:
            return await edit_delete(
                event, "انمی برای کاربران در هیچ چتی فعال نکرده اید"
            )
        try:
            remove_all_users()
        except Exception as e:
            await edit_delete(event, f"**Error:**\n`{str(e)}`", 10)
        else:
            await edit_or_reply(event, "انمی برای کاربر حذف و متوقف شد")
    else:
        lecho = get_users(event.chat_id)
        if len(lecho) == 0:
            return await edit_delete(
                event, "شما انمی را برای یک کاربر در این چت فعال نکرده اید"
            )
        try:
            remove_users(event.chat_id)
        except Exception as e:
            await edit_delete(event, f"**Error:**\n`{e}`", 10)
        else:
            await edit_or_reply(event, "انمی برای کاربر حذف و متوقف شد")


@catub.cat_cmd(
    pattern="listai( -a)?$",
    command=("listai", plugin_category),
    info={
        "header": "shows the list of users for whom you enabled ai",
        "flags": {
            "a": "To list ai enabled users in all chats",
        },
        "usage": [
            "{tr}listai",
            "{tr}listai -a",
        ],
    },
)
async def list_chatbot(event):  # sourcery no-metrics
    "To list all users on who you enabled ai."
    input_str = event.pattern_match.group(1)
    private_chats = ""
    output_str = "**انمی فعال برای کاربران در این چت:**\n\n"
    if input_str:
        lsts = get_all_users()
        group_chats = ""
        if len(lsts) <= 0:
            return await edit_or_reply(event, "انمی فعال برای هیچ کاربری وجود ندارد")
        for echos in lsts:
            if echos.chat_type == "Personal":
                if echos.user_username:
                    private_chats += (
                        f"☞ [{echos.user_name}](https://t.me/{echos.user_username})\n"
                    )
                else:
                    private_chats += (
                        f"☞ [{echos.user_name}](tg://user?id={echos.user_id})\n"
                    )
            elif echos.user_username:
                group_chats += f"☞ [{echos.user_name}](https://t.me/{echos.user_username}) در چت {echos.chat_name} شناسه چت `{echos.chat_id}`\n"
            else:
                group_chats += f"☞ [{echos.user_name}](tg://user?id={echos.user_id}) در چت {echos.chat_name} شناسه چت `{echos.chat_id}`\n"

        if private_chats != "":
            output_str += "**چت های خصوصی**\n" + private_chats + "\n\n"
        if group_chats != "":
            output_str += "**چت های گروهی**\n" + group_chats
    else:
        lsts = get_users(event.chat_id)
        if len(lsts) <= 0:
            return await edit_or_reply(
                event, "انمی فعال برای هیچ کاربری وجود ندارد"
            )
        for echos in lsts:
            if echos.user_username:
                private_chats += (
                    f"☞ [{echos.user_name}](https://t.me/{echos.user_username})\n"
                )
            else:
                private_chats += (
                    f"☞ [{echos.user_name}](tg://user?id={echos.user_id})\n"
                )
        output_str = "**انمی فعال برای کاربران در این چت:**\n" + private_chats
    await edit_or_reply(event, output_str)


@catub.cat_cmd(incoming=True, edited=False)
async def ai_reply(event):
    if is_added(event.chat_id, event.sender_id) and (event.message.text):
        AI_LANG = gvarstatus("AI_LANG") or "en"
        master_name = get_display_name(await event.client.get_me())
        try:
            response = await rs_client.get_ai_response(
                message=event.message.text,
                server="primary",
                master="CatUserbot",
                bot=master_name,
                uid=event.client.uid,
                language=AI_LANG,
            )
            await event.reply(response.message)
        except Exception as e:
            LOGS.error(str(e))
            await event.reply(random.choice(tired_response))
