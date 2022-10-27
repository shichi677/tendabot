import pandas as pd
import re
import datetime
import requests
import lxml.html
from collections import defaultdict
from tabulate import tabulate
import aiohttp

# import locale

# locale.setlocale(locale.LC_TIME, "ja_JP.UTF-8")


# def convert_text_for_discord(df):
#     return f'```\n{tabulate(df, headers=df.columns, showindex=False, tablefmt="github", stralign="center").replace("nan", "").translate(str.maketrans({chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)})).replace(" ", "　").replace("○", "〇").replace("－", "ー")}\n```\n"'


async def get_clanmatch_prise():
    clanmatch_url = "https://bo2.ggame.jp/jp/info/?p=49198"
    async with aiohttp.ClientSession() as session:
        async with session.get(clanmatch_url) as res:
            if res.status == 200:
                response = await res.text()
                html = lxml.html.fromstring(response)

                search = '"新規MS"'
                new_ms = html.xpath(f"//dd[contains(text(), {search})]")[0]
                ms_name = re.sub("[・）]", "", new_ms.getnext().text)
                ms_name = re.sub("[、（]", "\n", ms_name)

                search = '"clan_cdt"'
                new_ms = html.xpath(f"//dd[@id={search}]/img")[0]
                new_ms_image_url = f"https://bo2.ggame.jp{new_ms.get('src')}"

                return {"ms_name": ms_name, "image_url": new_ms_image_url}


async def get_clanmatch_info(match_date=None):
    url = "https://bo2.ggame.jp/jp/info/?p=49198"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            if res.status == 200:
                resp = await res.read()
                clanmatch_info_dict = {"Hold": {}, "Prise": {"Cond": {}, "MS": {}}}

                df = pd.read_html(resp)

                acquisition_cond = df[3]
                acquisition_cond = acquisition_cond.drop(1, axis=1)
                acquisition_cond = acquisition_cond.drop([0, 6], axis=0)
                acquisition_cond = acquisition_cond.drop([6], axis=1)
                acquisition_cond = acquisition_cond.replace("–", "　")
                acquisition_cond = acquisition_cond.replace(" ", "")
                acquisition_cond.columns = acquisition_cond.iloc[0]
                acquisition_cond = acquisition_cond.drop(1, axis=0)

                acquisition_cond_list = acquisition_cond.values.tolist()
                event_time = acquisition_cond.columns.tolist()
                dict_ = {}
                # print(acquisition_cond)
                # print(convert_text_for_discord(acquisition_cond))

                for event in acquisition_cond_list:

                    dict_[event[0]] = []

                    for i, cond in enumerate(event):
                        if cond == "○":
                            dict_[event[0]].append(event_time[i])

                for key, value in dict_.items():
                    rank_str = "".join(value)  # 例: 1～3位4～10位11～40位
                    start_idx = rank_str.find("～")
                    end_idx = rank_str.rfind("～")
                    rank_cond = rank_str[:start_idx] + rank_str[end_idx:]
                    rank_cond = rank_cond.replace("～", " ～ ")
                    key = key.replace("～", " ～ ")

                    clanmatch_info_dict["Prise"]["Cond"][key] = rank_cond

                clanmatch_info_dict["Prise"]["MS"] = await get_clanmatch_prise()

                df = df[:3]
                for table_data in df:
                    clanmatch_list = table_data.values.tolist()

                    # 開始日時取得
                    start_time = clanmatch_list[0][2][: clanmatch_list[0][2].find(" ～")]  # ex. clanmatch_list[0][2] = 2022年8月14日(日)13:00 ～ 14:59
                    start_time = re.sub(r"\(.\)", "", start_time)
                    start_time = datetime.datetime.strptime(start_time, "%Y年%m月%d日%H:%M")
                    start_time = start_time.strftime("%Y%m%d%H%M")

                    # 日付と時間に分ける
                    date = clanmatch_list[0][2][: clanmatch_list[0][2].find(")") + 1]
                    time = clanmatch_list[0][2][clanmatch_list[0][2].find(")") + 1:]

                    # YYYY年mm月dd日(a) -> YYYY/mm/dd(a)
                    date = re.sub(r"(\d+)年(\d+)月(\d+)日", r"\1/\2/\3", date)
                    # date = re.sub(r"(\d+)年(\d+)月(\d+)日", r'\1/0\2/0\3', date)
                    # date = re.sub(r"(\d+)/0*(\d{2,})/0*(\d{2,})", r'\1/\2/\3', date)
                    # date = datetime.datetime.strptime(date, "%Y年%m月%d日(%a)")
                    # date = date.strftime("%Y/%m/%d(%a)")

                    clanmatch_info_dict["Hold"][clanmatch_list[0][0]] = {
                        "date": date,
                        "time": time,
                        "start_time": start_time,
                        "rule": clanmatch_list[1][2],
                        "cost": clanmatch_list[1][4],
                        "stage": clanmatch_list[2][2],
                        "players": clanmatch_list[2][4],
                    }

                return clanmatch_info_dict

            else:
                return None


def convert_text_for_discord(df):
    return "```\n" + tabulate(df, headers=df.columns, showindex=False).replace("nan", "").translate(str.maketrans({chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)})).replace(" ", "　") + "\n```\n"


async def get_MS_page_url_from_wiki():
    URL = "https://w.atwiki.jp/battle-operation2/"
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as res:
            if res.status == 200:
                response = await res.text()

                ARMY_DICT = {"'menu_kyoushu'": "強襲", "'menu_hanyou'": "汎用", "'menu_sien'": "支援"}

                # lxmlを利用してWebページを解析する
                html = lxml.html.fromstring(response)
                SEARCH_DIV_IDS = ARMY_DICT.keys()

                mobilesuit_dict = defaultdict(dict)

                for search_id in SEARCH_DIV_IDS:
                    # h4タグにコストが示されている
                    costs_h = html.xpath(f"//div[@id={search_id}]/h4")

                    key_name = ARMY_DICT[search_id]

                    mobilesuit_dict[key_name] = {}

                    for cost in costs_h:
                        cost = cost.text
                        mobilesuit_dict[key_name][cost] = {}
                        # コストが示されているh4タグの一つ後にulタグ、その下にliタグがあり、aタグにMS名とURLが書かれている
                        mobilesuit_list = html.xpath(f"//div[@id={search_id}]/h4[contains(text(), '{cost}')]/following-sibling::ul[1]/li/a")
                        for ms in mobilesuit_list:
                            url = ms.get("href")
                            mobilesuit_dict[key_name][cost][ms.text] = f"https:{url}"

                return mobilesuit_dict

            else:
                return None


def get_table(elements):
    # print(elements)
    for child in elements:
        if child.tag == "table":
            df = pd.read_html(lxml.etree.tostring(child))
            yield df[0]

        if child.getchildren() is not None:
            yield from get_table(child.getchildren())

        else:
            continue


def organizer(df):
    df = df.dropna(axis=0, how="all")
    df2 = df[0:1].dropna(axis=1).columns
    df = df[df2]
    print(df)
    try:

        # df.columns = [i + j for i, j in df.columns]
        df.columns = df.columns.droplevel([1, 2])
        # pass
        df = df.drop("効果", axis=1)

    except Exception as e:
        print(e)
        pass

    return df


def get_spec_from_wiki_MS_page(url):
    message = ""
    response = requests.get(url)
    TARGET_DIV_ID = '"wikibody"'
    # lxmlを利用してWebページを解析する
    html = lxml.html.fromstring(response.text)
    h2_tags = html.xpath(f"//div[@id={TARGET_DIV_ID}]/h2")

    for h2 in h2_tags[1:]:
        if h2.text in ["備考", "強化リスト情報"]:
            break

        message += f"{h2.text}\n"
        target_element = h2.getnext()
        while True:

            if target_element.tag == "h3":
                message += f"{target_element.text}\n"

            if target_element.tag == "div":
                for tabledf in get_table(target_element.getchildren()):

                    message += convert_text_for_discord(organizer(tabledf))

            if target_element.tag == "table":
                df = pd.read_html(lxml.etree.tostring(target_element))
                message += convert_text_for_discord(organizer(df[0]))

            target_element = target_element.getnext()

            if target_element.tag == "h2":
                break

    return message


async def get_stage():
    """
    公式ページからマップ名、id、場所(地上、宇宙)を取得する
    """
    URL = "https://bo2.ggame.jp/jp/ms_stage/stage.php"
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as res:
            if res.status == 200:
                response = await res.text()

                # lxmlを利用してWebページを解析する
                html = lxml.html.fromstring(response)

                stage_dict = {}
                # 宇宙、地上のマップが記載されたclass_name
                for i, serch_class_name in enumerate(('"stgList"', '"stgList groundList"')):
                    # マップ名が記載されたタグを検索
                    dt_tags = html.xpath(f"//div[@class={serch_class_name}]/ul/li/a/dl/dt")
                    # マップid, 場所を記録
                    for j, dt in enumerate(dt_tags):
                        if i == 0:
                            place = "space"
                        else:
                            place = "ground"

                        stage_dict[dt.text] = {"place": place, "image_url": f"https://bo2.ggame.jp/jp/images/ms_stage/stage/img_{place}_{str(j + 1).zfill(2)}.jpg"}

                return stage_dict
