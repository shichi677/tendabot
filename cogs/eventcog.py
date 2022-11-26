import os
import re
import datetime
import random
from io import BytesIO
from collections import defaultdict
import discord

import pandas as pd
from discord.ext import commands, tasks
from discord import Embed, ChannelType
from dotenv import load_dotenv
import aiohttp
import asyncio

# import asyncgTTS
from PIL import Image

from cogs.tendacog import TendaView
from modules import get_clanmatch_info, FFmpegPCMAudio, CreateText, url_image_process, get_stage

import logging
import logging.handlers

import core

logger = logging.getLogger(__name__)

load_dotenv(verbose=True)
load_dotenv("../.env")


class EventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emb = None
        self.daycord_url = None
        self.practice_date = None
        self.match_date = None
        self.voice_state_message = ""
        self.voice_channel_state = defaultdict(dict)
        # self.message_queue: asyncio.Queue = asyncio.Queue(5)  # 5個まで
        self.loop = asyncio.get_event_loop()
        self.message_queue = asyncio.Queue(5)
        self.clanmatch_send_message_ch = None
        # self.stage_dict = get_stage()
        self.text_to_speech_dict = {"古代の機械": "アンティーク・ギア", "磁石の戦士": "マグネット・ウォリアー", "魔救の": "アダマシア", "超": "メガトン", "混沌": "カオス"}

        self.loop.create_task(self.text_to_speech())

    async def fetch_daycord_message(self, url=None):
        if url is None:
            for_contact_channel_id = int(os.environ["MOI_TXT_CH_CONTACT_ID"])
            daycord_id = int(os.environ["MOI_DAYCORD_USER_ID"])
            channel = self.bot.get_channel(for_contact_channel_id)

            pattern = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"

            async for message in channel.history(limit=10):
                if message.author.id == daycord_id:
                    last_content = message.content
                    break

            url = re.search(pattern, last_content).group()

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                if res.status == 200:
                    res_html = await res.read()
                    df = pd.read_html(res_html, header=0)[0]

                    try:
                        clanmatch_practice_date = re.sub("[^0-9]", "", df.iloc[2, 0])

                    except Exception:
                        clanmatch_practice_date = None
                        logger.error("failed fetch clanmatch practice date")

                    try:
                        clanmatch_date = re.sub("[^0-9]", "", df.iloc[3, 0])

                    except Exception:
                        clanmatch_date = None
                        logger.error("failed fetch clanmatch date")

                    if clanmatch_practice_date is not None:
                        if len(clanmatch_practice_date) < 12:
                            clanmatch_practice_date += "00"

                    if clanmatch_date is not None:
                        if len(clanmatch_date) < 12:
                            clanmatch_date += "00"

                    return url, clanmatch_practice_date, clanmatch_date
                else:
                    return None

    async def delete_past_tendaview(self):
        async for message in self.clanmatch_send_message_ch.history(limit=50):
            # メッセージのコンポーネント(ActionRow, Button, SelectMenu)が存在
            if message.components:
                component = message.components[0]
                #  ダイスボタンだったらメッセージ削除
                if component.type == discord.ComponentType.action_row:
                    if component.children[0].custom_id == "TendaView:dice":
                        print(f"delete message: created at {message.created_at.astimezone(datetime.timezone(datetime.timedelta(hours=+9)))}")
                        await message.delete()

            # cogreloadのメッセージ削除(デバッグ用)
            if message.content.startswith("cogs.eventcog"):
                await message.delete()

    @commands.Cog.listener()
    # Botの準備完了時に呼び出されるイベント
    async def on_ready(self):

        logger.info(f"Logged in as {self.bot.user.name}")
        # Tendaviewやクランマッチスケジュールを送るチャンネルを取得
        if self.bot.debugmode:
            channel_id = int(os.environ["SHICHI_TXT_CH_GENERAL_ID"])
            url = os.environ["DAYCORD_URL"]

        else:
            channel_id = int(os.environ["MOI_TXT_CH_BATOOPE_ID"])
            url = None

        self.clanmatch_send_message_ch = self.bot.get_channel(channel_id)
        logger.info(f"guild: {self.clanmatch_send_message_ch.guild.name}")

        try:
            await self.clanmatch_send_message_ch.purge(check=lambda m: m.author.bot and "クランマッチ" not in m.clean_content, reason="initialize")

        except Exception as e:
            logger.info(f"ボタンメッセージの削除に失敗しました: {e}")

        # デイコードからクランマッチの日程を取得
        try:
            self.daycord_url, self.practice_date, self.match_date = await self.fetch_daycord_message(url=url)
            self.send_message_every_10sec.start()

            if self.practice_date is not None:
                logger.info(f"練習日時：{self.practice_date[0:4]}年{self.practice_date[4:6]}月{self.practice_date[6:8]}日{self.practice_date[8:10]}時{self.practice_date[10:12]}分")

            if self.match_date is not None:
                logger.info(f"本番日時：{self.match_date[0:4]}年{self.match_date[4:6]}月{self.match_date[6:8]}日{self.match_date[8:10]}時{self.match_date[10:12]}分")

        except AttributeError:
            logger.info("デイコードからの情報取得に失敗しました")

        logger.info("voicevox initializing...")
        core.initialize(use_gpu=False)
        core.voicevox_load_openjtalk_dict("open_jtalk_dic_utf_8-1.11")
        logger.info("voicevox initialize finished")

    @tasks.loop(seconds=60)
    async def send_message_every_10sec(self):
        async def get_response(session, url):
            async with session.get(url) as res:
                if res.status == 200:
                    resp = await res.read()
                    return resp
                else:
                    return None

        # タイムゾーン取得
        JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")

        # 現在時刻にdelay_timeを足したものを現在時刻とする
        dt_now = datetime.datetime.now(JST)
        now = dt_now.strftime("%Y%m%d%H%M")

        # デバッグ用
        # now = "202208250500"
        # logger.info(now)

        if now[-4:] == "0600":
            # plan to create initialize function
            logger.info("message clean")
            await self.clanmatch_send_message_ch.purge(check=lambda m: m.author.bot and "クランマッチ" not in m.clean_content, reason="initialize")
            self.bot.latest_tendaview_message_id = None
            logger.info("clanmatch schedule update")
            self.daycord_url, self.practice_date, self.match_date = await self.fetch_daycord_message(url=None)
            logger.info(f"練習日時：{self.practice_date[0:4]}年{self.practice_date[4:6]}月{self.practice_date[6:8]}日{self.practice_date[8:10]}時{self.practice_date[10:12]}分")
            logger.info(f"本番日時：{self.match_date[0:4]}年{self.match_date[4:6]}月{self.match_date[6:8]}日{self.match_date[8:10]}時{self.match_date[10:12]}分")

            core.finalize()
            logger.info("voicevox initializing...")
            core.initialize(use_gpu=False)
            core.voicevox_load_openjtalk_dict("open_jtalk_dic_utf_8-1.11")
            logger.info("voicevox initialize finished")

        # 何分前に通知するか
        notification_min = 60
        clanmatch_notifi_time_dt = dt_now + datetime.timedelta(minutes=notification_min)
        clanmatch_notifi_time = clanmatch_notifi_time_dt.strftime("%Y%m%d%H%M")
        # clanmatch_notifi_time = "202211042100"

        # 現在時刻が練習もしくは本番時刻のとき
        if clanmatch_notifi_time == self.practice_date or clanmatch_notifi_time == self.match_date:

            # 練習化
            if clanmatch_notifi_time == self.practice_date:
                number = 2
                match_type = "クランマッチ練習"

            elif clanmatch_notifi_time == self.match_date:
                number = 3
                match_type = "クランマッチ"

            # embed、画像格納用リスト
            embeds = []
            files = []

            async with aiohttp.ClientSession() as session:
                # 参加者情報、クランマッチ情報を取得するtask
                tasks = [
                    asyncio.wait_for(get_response(session, self.daycord_url), timeout=5.0),
                    asyncio.wait_for(get_clanmatch_info(), timeout=5.0),
                ]

                # gatherでタスクを並行実行
                response_data = await asyncio.gather(*tasks, return_exceptions=True)

                # デイコードurlのresponse
                participant_info_res = response_data[0]

                # ○および△のひとを取得し、embed作成
                try:
                    df = pd.read_html(participant_info_res, header=0)[0]
                    circle_member = df.iloc[0][df.iloc[number] == "◯"].values
                    triangle_member = df.iloc[0][df.iloc[number] == "△"].values

                    # クランマッチ参加状況embed生成
                    participant_embed = Embed(title="参加予定者", description="", colour=discord.Colour.green())
                    participant_embed.add_field(name=f"○のひと: {len(circle_member)}人", value="\n".join(circle_member), inline=True)
                    participant_embed.add_field(name=f"△のひと: {len(triangle_member)}人", value="\n".join(triangle_member), inline=True)
                    embeds.append(participant_embed)

                # エラー時
                except Exception as e:
                    # クランマッチ参加状況embed生成
                    logger.warning(f"get participant error {e}")
                    participant_embed = Embed(title="エラー", description="参加予定者の取得に失敗しました", colour=discord.Colour.red())
                    embeds.append(participant_embed)

                # クランマッチ情報取得
                clanmatch_info = response_data[1]

                try:
                    # マッチ情報 embed生成
                    match_info_embed = Embed(title="マッチ情報", description="", colour=discord.Colour.blue())

                    # match_dateに一致するマッチ情報を取得
                    match_date_hold_num = [hold_num for hold_num in clanmatch_info["Hold"] if clanmatch_info["Hold"][hold_num]["start_time"] == self.match_date]

                    # マッチ情報embed作成
                    hold_num = match_date_hold_num[0]
                    match_info = "日　付：{0[date]}\n時　間：{0[time]}\nルール：{0[rule]}\nコスト：{0[cost]}\nマップ：{0[stage]}\n人　数：{0[players]}".format(clanmatch_info["Hold"][hold_num])
                    match_info_embed = Embed(title=hold_num, description=match_info, colour=discord.Colour.blue())

                    # マップ画像
                    stage = clanmatch_info["Hold"][hold_num]["stage"]
                    stage_dict = await get_stage()
                    image_url = stage_dict[stage]["image_url"]
                    stage_filename = "stage.webp"
                    stage_file = url_image_process(url=image_url, method="crop", filename=stage_filename, crop_size=400)
                    match_info_embed.set_thumbnail(url=f"attachment://{stage_filename}")
                    files.append(stage_file)

                except Exception as e:
                    logger.warning(f"reminder error: {e}")
                    match_info_embed = Embed(title="エラー", description="マッチ情報を取得できませんでした", colour=discord.Colour.red())

                # マッチ情報embed格納
                embeds.append(match_info_embed)

                # 報酬情報embed生成
                try:
                    # 報酬情報
                    prise_embed = Embed(title="報酬情報", description="", colour=discord.Colour.gold())

                    # 報酬条件 ex.第110回 ～ 111回：1 ～ 3位
                    cond = ""

                    for key, value in clanmatch_info["Prise"]["Cond"].items():
                        # 今回のマッチがどの条件に当てはまるか探索
                        hold_num_int = int(re.sub("[^0-9]", "", hold_num))  # 第115回 -> 115
                        during_list = [*map(int, re.sub("[第回以降]", "", key).split(" ～ "))]  # 第110回 ～ 111回 -> [110, 111] or 第116回以降 -> [116]

                        # 第110回 ～ 111回 -> [110, 111]のパターン
                        # 期間の始めと終わりを取得
                        if len(during_list) == 2:
                            begin, end = during_list

                        # 第116回以降 -> [116]のパターン
                        # +10回を終わりとしている
                        elif len(during_list) == 1:
                            begin = during_list[0]
                            end = begin + 10

                        # 条件に当てはまったら下線をつける
                        if hold_num_int in range(begin, end + 1):
                            cond += f"__{key}：{value}__\n"
                        else:
                            cond += f"{key}：{value}\n"

                    # 報酬取得条件フィールド
                    prise_embed.add_field(name="取得条件", value=cond)

                    # 報酬MS情報
                    prise_embed.add_field(name="報酬", value=clanmatch_info["Prise"]["MS"]["ms_name"].replace("（", "\n（"), inline=False)
                    image_url = clanmatch_info["Prise"]["MS"]["image_url"]
                    prise_filename = "prise_MS.webp"
                    prise_file = url_image_process(url=image_url, method="resize", filename=prise_filename, resize_rate=0.24)
                    prise_embed.set_image(url=f"attachment://{prise_filename}")
                    files.append(prise_file)
                    # 注釈追加
                    prise_embed.set_footer(text="※下線は今回のクランマッチ")

                # 報酬情報取得できなかったら
                except Exception as e:
                    logger.warning(f"clanmatch info get error {e}")
                    print(e)
                    prise_embed = Embed(title="エラー", description="クランマッチ報酬情報を取得できませんでした", colour=discord.Colour.red())

                # 報酬情報embed格納
                embeds.append(prise_embed)

            # メッセージ
            message = f"@everyone\n{match_type}の時間の{notification_min}分前になりました！"
            await self.clanmatch_send_message_ch.send(content=message, embeds=embeds, files=files)

        # 何分後に通知するか
        notification_min = 120
        after_clanmatch_notifi_time_dt = dt_now - datetime.timedelta(minutes=notification_min)
        after_clanmatch_notifi_time = after_clanmatch_notifi_time_dt.strftime("%Y%m%d%H%M")
        # after_clanmatch_notifi_time = "202211052100"

        if after_clanmatch_notifi_time == self.match_date:
            # クランマッチ情報取得
            try:
                self.clanmatch_info = await get_clanmatch_info()
                embeds = []  # embedリスト クランマッチ開催情報3つ + 報酬情報
                files = []  # 画像リスト マップ3つ + 報酬MS

                # マッチ情報3つについて
                for hold_num in self.clanmatch_info["Hold"]:
                    # マッチ情報embed作成
                    match_info = "日　付：{0[date]}\n時　間：{0[time]}\nルール：{0[rule]}\nコスト：{0[cost]}\nマップ：{0[stage]}\n人　数：{0[players]}".format(self.clanmatch_info["Hold"][hold_num])
                    embed = Embed(title=hold_num, description=match_info, colour=discord.Colour.blue())

                    # マップ画像
                    stage = self.clanmatch_info["Hold"][hold_num]["stage"]
                    stage_dict = await get_stage()
                    image_url = stage_dict[stage]["image_url"]
                    filename = f"image_{len(files)}.png"

                    # 画像取得のためのセッション
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as resp:
                            # getしてきたものをread
                            image = await resp.read()
                            # pilで読み込んで正方形にクロップしてサムネイルに
                            pil_img = Image.open(BytesIO(image))
                            file = url_image_process(url=image_url, pil_img=pil_img, method="crop", filename=filename, crop_size=400)
                            embed.set_thumbnail(url=f"attachment://{filename}")

                            embeds.append(embed)
                            files.append(file)

                # 報酬情報
                embed = Embed(title="報酬情報", description="", colour=discord.Colour.gold())

                # 報酬条件 ex.第110回 ～ 111回：1 ～ 3位
                cond = ""
                for key, value in self.clanmatch_info["Prise"]["Cond"].items():
                    cond += f"{key}：{value}\n"
                embed.add_field(name="取得条件", value=cond)

                # 報酬MS情報
                embed.add_field(name="報酬", value=self.clanmatch_info["Prise"]["MS"]["ms_name"].replace("（", "\n（"), inline=False)
                image_url = self.clanmatch_info["Prise"]["MS"]["image_url"]

                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        image = await resp.read()
                        pil_img = Image.open(BytesIO(image))
                        filename = "prise.webp"
                        file = url_image_process(url=image_url, pil_img=pil_img, method="resize", filename=filename, resize_rate=0.24)
                        embed.set_image(url=f"attachment://{filename}")
                        embeds.append(embed)
                        files.append(file)

                # クランマッチスケジュールのレスポンスメッセージ
                message = "クランマッチお疲れ様でした！\n現在公開されているクランマッチ開催スケジュールはこちらです！"

                # メッセージリフレッシュ
                await self.clanmatch_send_message_ch.send(content=message, embeds=embeds, files=files)

            # エラー時
            except Exception as e:
                print(f"clanmatch schedule error: {e}")
                embed = Embed(title="クランマッチ情報取得エラー", description="クランマッチ情報の取得に失敗しました。", colour=discord.Colour.red())
                await self.clanmatch_send_message_ch.send(embed=embed)

    async def text_to_speech(self):
        while True:
            try:
                message = await self.message_queue.get()

                if message.channel.guild.id == int(os.environ["SHICHI_GUILD_ID"]):
                    channel_id = int(os.environ["SHICHI_TXT_CH_DEBUG_ID"])

                else:
                    channel_id = int(os.environ["MOI_TXT_CH_BOT_TEST_ID"])

                if message.clean_content != "":
                    send_message = message.clean_content
                    if message.channel.id == channel_id:
                        for key, value in self.text_to_speech_dict.items():
                            send_message = send_message.replace(key, value)

                    text = CreateText(send_message)
                    # 音声合成
                    wavefmt = core.voicevox_tts(text, 1)

                    # async with aiohttp.ClientSession() as session:
                    #     gtts = await asyncgTTS.setup(premium=False, session=session)
                    #     hello_world = await gtts.get(text=text, lang="ja")

                    mp3_fp = BytesIO()
                    mp3_fp.write(wavefmt)
                    mp3_fp.seek(0)

                    source = FFmpegPCMAudio(mp3_fp.read(), pipe=True)

                    while message.guild.voice_client.is_playing():
                        await asyncio.sleep(0.1)

                    message.guild.voice_client.play(source)

            except Exception as e:
                logger.warning(e)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ボイスチャンネルに接続していて、メッセージがコマンドじゃないとき
        if self.bot.voice_clients and not message.content.startswith("?"):
            # 各クライアントに対して
            for voice_client in self.bot.voice_clients:
                # ボイスクライアントとメッセージのギルドが同じとき
                if voice_client.guild == message.guild and voice_client.is_connected():
                    # queue に追加（いっぱいなら待つ）
                    if message.attachments:
                        if message.attachments[0].content_type.startswith("image"):

                            print(message.attachments[0].content_type)
                            message.content = "画像が送信されました。"

                    await self.message_queue.put(message)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):

        if before.channel != after.channel and not member.bot:
            message = ""

            # ボイスチャンネルの状況取得処理
            self.voice_channel_state = defaultdict(dict)
            # メンバーが所属しているギルドのチャンネルに対して
            for channel in member.guild.channels:
                # ボイスチャンネルだったら
                if channel.type == ChannelType.voice:
                    # ボイスチャンネルに所属しているメンバーに対して
                    for channel_member in channel.members:
                        # bot以外だったら辞書にミュート情報を取得
                        if not channel_member.bot:
                            self.voice_channel_state[channel][channel_member.name] = channel_member.voice.self_mute

            # ボイスチャンネル状況embed生成
            embed = Embed(title="ボイスチャンネル状況", description="", color=0x00FF00)
            for channel, member_dict in self.voice_channel_state.items():
                voice_state_embed_des = f"参加: {len(member_dict)}人\n"
                embed.add_field(name=channel.name, value=f"{voice_state_embed_des}", inline=False)

            # ボイスチャット退室処理
            if after.channel is None:
                message = f"{member.display_name}さんが退室しました。"
                exist = before

            else:
                # 入室処理
                if before.channel is None:
                    message = f"{member.display_name}さんが入室しました。"

                    # botがボイスチャンネルに接続していなかったら接続、view送信
                    for voice_client in self.bot.voice_clients:
                        if voice_client.guild == member.guild:
                            break
                    else:
                        await member.voice.channel.connect()
                        # 今までview送信していなかったら送信
                        if self.bot.latest_tendaview_message_id is None:
                            if member.guild.id != int(os.environ["SHICHI_GUILD_ID"]):
                                view_send_channel_id = int(os.environ["MOI_TXT_CH_BATOOPE_ID"])
                                view_send_channel = self.bot.get_channel(view_send_channel_id)
                                tendaview_message = await view_send_channel.send(content="ボタンを表示するよ！", view=TendaView(self))
                                self.bot.latest_tendaview_message_id = tendaview_message.id

                    exist = after

            # ボイスチャンネルに接続しているクライアントについて
            for voice_client in self.bot.voice_clients:

                # bot以外のメンバー人数を計算
                member_cnt = 0
                for ch_member in voice_client.channel.members:
                    if not ch_member.bot:
                        member_cnt += 1

                # メンバーがいなかったら
                if member_cnt == 0:
                    for channel, is_mute in self.voice_channel_state.items():
                        # botが接続していないチャンネルについて調べる
                        if voice_client.channel != channel:
                            # 1以上いたら移動
                            if len(is_mute) > 0:
                                await voice_client.move_to(channel)
                                break

                    # どこにもいなかったら切断
                    else:
                        await voice_client.disconnect()
                        voice_client.cleanup()

            if message:
                if exist.channel.guild.id == int(os.environ["SHICHI_GUILD_ID"]):
                    channel_id = int(os.environ["SHICHI_TXT_CH_DEBUG_ID"])

                else:
                    channel_id = int(os.environ["MOI_TXT_CH_BOT_TEST_ID"])

                channel = self.bot.get_channel(channel_id)
                rand_num = random.random()
                threshold = 1 / 319
                # inequal_dict = {True: "<=", False: ">"}
                # print(f"{member.display_name}: {round(rand_num, 5)} {inequal_dict[rand_num <= threshold]} {round(threshold, 5)}")
                if rand_num <= threshold:
                    agagaembed = Embed(title="あががいのがいっ♪あががいのがいっ♪", description=f"{member.display_name}さん！大当たり！", color=0x00FF00)
                    await channel.send(f"{member.display_name}さんが319分の1を引当てました！", embed=agagaembed)

                await channel.send(content=message)

            if self.bot.latest_tendaview_message_id is not None:
                # update voice channel state embed
                for channel in member.guild.channels:
                    if channel.type == discord.ChannelType.text:
                        try:
                            tendaview_message = await channel.fetch_message(self.bot.latest_tendaview_message_id)
                            await tendaview_message.edit(embed=embed)
                            break
                        except Exception:
                            pass


async def setup(bot):
    await bot.add_cog(EventCog(bot))
