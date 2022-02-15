# corona virus stats for catuserbot
from covid import Covid

from . import catub, covidindia, edit_delete, edit_or_reply

plugin_category = "extra"


@catub.cat_cmd(
    pattern="covid(?:\s|$)([\s\S]*)",
    command=("covid", plugin_category),
    info={
        "header": "To get latest information about covid-19.",
        "description": "Get information about covid-19 data in the given country/state(only Indian States).",
        "usage": "{tr}covid <state_name/country_name>",
        "examples": ["{tr}covid andhra pradesh", "{tr}covid india", "{tr}covid world"],
    },
)
async def corona(event):
    "To get latest information about covid-19."
    input_str = event.pattern_match.group(1)
    country = (input_str).title() if input_str else "World"
    catevent = await edit_or_reply(event, "`درحال جمع آوری داده ها...`")
    covid = Covid(source="worldometers")
    try:
        country_data = covid.get_status_by_country_name(country)
    except ValueError:
        country_data = ""
    if country_data:
        hmm1 = country_data["confirmed"] + country_data["new_cases"]
        hmm2 = country_data["deaths"] + country_data["new_deaths"]
        data = ""
        data += f"\n⚠️ تایید شده   : <code>{hmm1}</code>"
        data += f"\n😔 فعال           : <code>{country_data['active']}</code>"
        data += f"\n⚰️ فوت شدگان         : <code>{hmm2}</code>"
        data += f"\n🤕 بحرانی          : <code>{country_data['critical']}</code>"
        data += f"\n😊 بهبود یافت   : <code>{country_data['recovered']}</code>"
        data += f"\n💉 مجموع تست ها    : <code>{country_data['total_tests']}</code>"
        data += f"\n🥺 موارد جدید   : <code>{country_data['new_cases']}</code>"
        data += f"\n😟فوت شدگان جدید : <code>{country_data['new_deaths']}</code>"
        await catevent.edit(
            "<b>Corona Virus Info of {}:\n{}</b>".format(country, data),
            parse_mode="html",
        )
    else:
        data = await covidindia(country)
        if data:
            cat1 = int(data["new_positive"]) - int(data["positive"])
            cat2 = int(data["new_death"]) - int(data["death"])
            cat3 = int(data["new_cured"]) - int(data["cured"])
            result = f"<b>Corona virus info of {data['state_name']}\
                \n\n⚠️ تایید شده   : <code>{data['new_positive']}</code>\
                \n😔 فعال           : <code>{data['new_active']}</code>\
                \n⚰️ فوت شدگان         : <code>{data['new_death']}</code>\
                \n😊 بهبود یافت   : <code>{data['new_cured']}</code>\
                \n🥺 موارد جدید   : <code>{cat1}</code>\
                \n😟 فوت شدگان جدید : <code>{cat2}</code>\
                \n😃 درمان جدید  : <code>{cat3}</code> </b>"
            await catevent.edit(result, parse_mode="html")
        else:
            await edit_delete(
                catevent,
                "`اطلاعات ویروس کرونا دردسترس نیست❌`".format(
                    country
                ),
                5,
            )
