import discordbot
from modules import get_clanmatch_info, get_MS_page_url_from_wiki, get_spec_from_wiki_MS_page, get_stage, url_image_process
from my_ui import Dropdown, DiceView, RandomSelectMSView, RuleSelectDropdownView, RateRegistView, MemberSelectDropdownView, RateRegistModal, TeamDivideDropdownView, ConfirmView
import discord
from discord.ext import commands
from discord import app_commands, Embed
import sys
import os
from collections import defaultdict
import aiohttp
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

import logging
import logging.handlers

sys.path.append("../")

load_dotenv(verbose=True)
load_dotenv("../.env")


logger = logging.getLogger(__name__)


# wiki機体検索view
class GetMSPageFromWikiView(discord.ui.View):
    def __init__(self, ms_dict):
        super().__init__(timeout=None)
        self.ms_dict = ms_dict

        army_select_dropdown_options = [
            discord.SelectOption(label="強襲", description="強襲機を検索します", emoji="🟥"),
            discord.SelectOption(label="汎用", description="汎用機を検索します", emoji="🟦"),
            discord.SelectOption(label="支援", description="支援機を検索します", emoji="🟧"),
        ]

        self.select_army_dropdown = Dropdown(army_select_dropdown_options, placeholder="検索する兵科を選んでください", row=0)
        self.add_item(self.select_army_dropdown)

        # コスト検討中 現在固定で対処中
        # costs = [(len(self.ms_dict[army].keys()), self.ms_dict[army].keys()) for army in ("強襲", "汎用", "支援")]
        # costs.sort()
        # costs = costs[0][1]

        costs = [cost for cost in range(100, 750, 50)]

        cost_select_dropdown_options = []
        for i, cost in enumerate(costs):
            option = discord.SelectOption(label=f"{cost}", description=f"コスト{cost}の機体を検索します", emoji=f"{(i + 1)%10}\u20e3")
            cost_select_dropdown_options.append(option)

        self.select_cost_dropdown = Dropdown(cost_select_dropdown_options, placeholder="検索するコストを選んでください", row=1)
        self.add_item(self.select_cost_dropdown)

    # 決定ボタン
    @discord.ui.button(label="検索", style=discord.ButtonStyle.green, custom_id="GetMSPageFromWikiView:dicide", row=2)
    async def dicide(self, interaction: discord.Interaction, button: discord.ui.Button):

        army = self.select_army_dropdown.values[0]
        cost = self.select_cost_dropdown.values[0]

        embed = Embed(title=f"検索結果 ー {army} {cost}コスト", description="", color=0x00FF00)

        for i, item in enumerate(self.ms_dict[army][cost].items()):
            ms_name, link = item
            number = str(i + 1)
            emoji_number = ""
            for s in number:
                emoji_number += f"{s}\u20e3"
            embed.add_field(name=f"{emoji_number} {ms_name}", value=f"{link}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


class TendaView(discord.ui.View):
    def __init__(self, bot):

        super().__init__(timeout=None)
        self.bot = bot
        self.dice_log = []
        self.dice_result = {}
        self.memberList = []
        self.rateList = []
        self.channel_member_sotie_dict = defaultdict(dict)
        self.ms_dict = None
        self.batch_select_random_ms_message = None
        self.clanmatch_schedule_message = None
        self.rate_regist_message_id = None
        self.team_divide_message = None
        self.rate_msg_flag = False
        # self.stage_dict = get_stage()
        self.add_item(discord.ui.Button(label="公式サイト", style=discord.ButtonStyle.blurple, url="https://bo2.ggame.jp/", row=4))
        self.add_item(discord.ui.Button(label="wiki", style=discord.ButtonStyle.blurple, url="https://w.atwiki.jp/battle-operation2/", row=4))

    @discord.ui.button(label="ダイスロール", style=discord.ButtonStyle.blurple, custom_id="TendaView:dice", row=0)
    async def dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=DiceView.DICE_INIT_EMBED, view=DiceView())

    @discord.ui.button(label="レーティング登録", style=discord.ButtonStyle.blurple, custom_id="TendaView:regist", row=1)
    async def regist(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.rate_msg_flag:
            await interaction.response.send_message("__すでにレーティング登録メッセージが送信されているようです。__\nレーティングを登録する場合はレーティング登録メッセージの「登録」ボタンからお願いします。\nレーティング登録メッセージを再送信する場合は「送信」ボタンを押してください。", view=ConfirmView(button_label="送信", input_callback=interaction.followup.send(embed=RateRegistModal.RATE_REGIST_INIT_EMBED, view=RateRegistView(self))), ephemeral=True)

        else:
            await interaction.response.send_message(embed=RateRegistModal.RATE_REGIST_INIT_EMBED, view=RateRegistView(self))
            self.rate_msg_flag = True

    @discord.ui.button(label="チーム分け", style=discord.ButtonStyle.blurple, custom_id="TendaView:team_divide", row=1)
    async def team_divide(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.team_dicide_dropdown_view = TeamDivideDropdownView(self.memberList, self.rateList)
        await interaction.response.send_message("チーム数とチーム分けの方法を選んでね！", embed=TeamDivideDropdownView.TEAM_DIVIDE_INIT_EMBED, view=self.team_dicide_dropdown_view)

    @discord.ui.button(label="メンバー選出", style=discord.ButtonStyle.blurple, custom_id="TendaView:select_memeber", row=1)
    async def member_select(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("選択する人数と方法を選んでね！", view=MemberSelectDropdownView(interaction.message, self.channel_member_sotie_dict))

    @discord.ui.button(label="マップ・コスト選択", style=discord.ButtonStyle.blurple, custom_id="TendaView:select_rule", row=2)
    async def select_rule(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("決めるゲームルールを選択してね", view=RuleSelectDropdownView(stage_dict=await get_stage()))

    # @discord.ui.button(label="機体選択", style=discord.ButtonStyle.blurple, custom_id="TendaView:select_random_ms", row=2)
    # async def select_ms(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     select_num = random.randint(1, 16)
    #     await interaction.response.send_message(f"搭乗する機体は機体選択画面の__{select_num}番目__です！", view=RandomSelectMSView(interaction.message, select_num), ephemeral=True)

    @discord.ui.button(label="機体選択", style=discord.ButtonStyle.blurple, custom_id="TendaView:batch_select_random_ms", row=2)
    async def batch_select_ms(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(view=RandomSelectMSView(), embed=RandomSelectMSView.SELECT_MS_INIT_EMBED, file=RandomSelectMSView.select_ms_number_img)

    @discord.ui.button(label="クランマッチ情報", style=discord.ButtonStyle.blurple, custom_id="TendaView:clanmatch_schedule", row=3)
    async def clanmatch_schedule(self, interaction: discord.Interaction, button: discord.ui.Button):

        # thinkingメッセージ送信
        await interaction.response.defer(thinking=True)

        # クランマッチ情報取得
        try:
            self.clanmatch_info = await get_clanmatch_info()
            embeds = []  # embedリスト クランマッチ開催情報3つ + 報酬情報
            files = []  # 画像リスト マップ3つ + 報酬MS

            # マッチ情報3つについて
            for hold_num in self.clanmatch_info["Hold"]:
                # マッチ情報embed作成
                match_info = "日　時：{0[date]}\n時　間：{0[time]}\nルール：{0[rule]}\nコスト：{0[cost]}\nマップ：{0[stage]}\n人　数：{0[players]}".format(self.clanmatch_info["Hold"][hold_num])
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
            message = "現在公開されているクランマッチ開催スケジュールはこちらです！"

            # メッセージリフレッシュ
            await interaction.followup.send(content=message, embeds=embeds, files=files, ephemeral=False)

        # エラー時
        except Exception as e:
            print(f"clanmatch schedule error: {e}")
            embed = Embed(title="クランマッチ情報取得エラー", description="クランマッチ情報の取得に失敗しました。\nもう一度試してみてください。", colour=discord.Colour.red())
            await interaction.followup.send(embed=embed, ephemeral=False)

    @discord.ui.button(label="機体検索 (wiki)", style=discord.ButtonStyle.blurple, custom_id="TendaView:get_wiki_data", row=3)
    async def get_wiki_data(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)
        self.ms_dict = await get_MS_page_url_from_wiki()

        message = "機体カテゴリ、コストを指定してね！"
        await interaction.followup.send(content=message, view=GetMSPageFromWikiView(self.ms_dict), ephemeral=True)


# コグとして用いるクラスを定義。
class TestCog(commands.Cog):

    # TestCogクラスのコンストラクタ。Botを受取り、インスタンス変数として保持。
    def __init__(self, bot):

        self.bot = bot
        self.flag = True
        self.funcflag = 0
        self.memberList = []  # レート登録時のメンバー名リスト
        self.memberidList = []  # レート登録時のメンバーIDリスト
        self.rateList = []  # レート登録時のレート値リスト
        self.rest_member_list = []
        self.member_sotie_num_dict = {}  # メンバー選択用の各メンバーの名前と出撃回数を記録する辞書
        self.channel_member_sotie_dict = {}  # ボイスチャンネル名と上記の辞書を記録する辞書
        self.refresh_messages = []
        self.divided_team_list = []  # チーム分け用リスト
        self.question_message = [0]  # 出撃チェックのメッセージ用リスト
        self.refresh_messages = []  # メッセージリフレッシュ用リスト
        self.dice_dict = {}
        self.map = None
        self.cost = None
        self.rule = None
        self.match = None

        self.ctx_menu = app_commands.ContextMenu(
            name="wiki機体ページ検索(β)",
            callback=self.my_cool_context_menu,
            guild_ids=[int(os.environ["SHICHI_GUILD_ID"]), int(os.environ["MOI_GUILD_ID"])],
        )

        self.delete_message_ctx_menu = app_commands.ContextMenu(
            name="このメッセージを削除",
            callback=self.message_delete,
            guild_ids=[int(os.environ["SHICHI_GUILD_ID"]), int(os.environ["MOI_GUILD_ID"])],
        )

        self.bot.tree.add_command(self.ctx_menu)
        self.bot.tree.add_command(self.delete_message_ctx_menu)

        @self.delete_message_ctx_menu.error
        async def permission_deny(interation: discord.Interaction, error: app_commands.AppCommandError):
            await interation.response.send_message("実行権限がありません", ephemeral=True)

    @app_commands.command(name="テンダちゃーん", description="テンダちゃんを呼びます")
    @app_commands.guilds(discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])), discord.Object(id=int(os.environ["MOI_GUILD_ID"])))
    async def call_tenda_app(self, interaction: discord.Interaction):

        await interaction.response.send_message("お呼びでしょーか！", view=TendaView(self.bot))
        self.bot.latest_tendaview_message = await interaction.original_response()

    @app_commands.command(name="cogreload", description="cogをリロードします")
    @app_commands.guilds(discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])))
    async def cogreload(self, interaction: discord.Interaction):
        message = ""
        for cog in discordbot.COGS:
            message += f"{cog}\n"
            await self.bot.reload_extension(name=cog)

        # import glob
        # for name in glob.glob("./my_ui/*/*.py"):
        #     await self.bot.load_extension(name=name.replace("/", ".")[2:-3], package=name.replace("/", ".")[1:-3])
        # await self.bot.
        await interaction.response.send_message(f"{message}\ncog loaded")
        # await self.call_tenda_app()
        print("cogreloaded")

    @app_commands.command(name="message_test", description="メッセージ体裁確認用コマンド")
    @app_commands.guilds(discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])))
    async def tabtest(self, interaction: discord.Interaction):
        test_str = get_spec_from_wiki_MS_page("https://w.atwiki.jp/battle-operation2/pages/2794.html")[:1127]
        await interaction.response.send_message(test_str)

    @app_commands.command(name="req_test", description="getメソッドテスト用")
    @app_commands.guilds(discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])))
    async def reqtest(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer(thinking=True)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as res:
                    logger.info(res)
                    if res.status == 200:
                        response = await res.text()

                    else:
                        response = "status error"
                        logger.error(res.status)

            await interaction.followup.send(response[:100])

        except Exception as e:
            response = f"error {e}"
            await interaction.followup.send(response)

    @commands.command()
    async def msg_delete(self, ctx: commands.Context):
        msg = await ctx.fetch_message(1019254506770415646)
        await msg.delete()

    @commands.command()
    async def cmdtest(self, ctx: commands.Context):
        print("test")

    @commands.command()
    async def sync(self, ctx: commands.Context):
        self.bot.tree.copy_global_to(guild=discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])))
        self.bot.tree.copy_global_to(guild=discord.Object(id=int(os.environ["MOI_GUILD_ID"])))
        com = await self.bot.tree.sync(guild=discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])))
        com2 = await self.bot.tree.sync(guild=discord.Object(id=int(os.environ["MOI_GUILD_ID"])))

        await ctx.send(f"sync: {com}\n{com2}")

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])))
    async def member_voice_move_test(self, interaction):
        await interaction.response.defer(thinking=True)
        # メッセージが送られたギルド（サーバー）取得
        currentguild = interaction.user.guild
        # ボイスチャンネルの一覧を取得
        voicechannel_list = currentguild.voice_channels[1:3]

        N = 8

        # lis = [interaction.user.move_to(voicechannel_list[i % 2]) for i in range(N)]
        # lis = [interaction.user.edit(voice_channel=voicechannel_list[0]) for i in range(N)]
        # await asyncio.gather(*lis)

        for i in range(N):
            await interaction.user.edit(voice_channel=voicechannel_list[0])
            print(i)
        # if N * 2 > 10:
        #     await asyncio.sleep(7.5)

        for i in range(N):
            await interaction.user.edit(voice_channel=voicechannel_list[0])
            print(i)

        # # for future in asyncio.as_completed(lis):

        await interaction.followup.send("complete")

    def is_sub_leader():
        def predicate(interaction: discord.Interaction) -> bool:
            sub_leader_IDs = [int(os.environ["niwaka_ID"]), int(os.environ["rotoru_ID"])]
            return interaction.user.id in sub_leader_IDs

        return app_commands.check(predicate)

    @is_sub_leader()
    async def message_delete(self, interaction: discord.Interaction, message: discord.Message):
        try:
            await message.delete()
            await interaction.response.send_message("メッセージを削除しました", ephemeral=True)

        except Exception as e:
            logger.error(e)
            await interaction.response.send_message("メッセージを削除できませんでした。\nもう一度実行するか、削除するメッセージを確認してください", ephemeral=True)

    async def my_cool_context_menu(self, interaction: discord.Interaction, message: discord.Message):
        message = "機体カテゴリ、コストを指定してね！"
        await interaction.response.send_message(content=message, view=GetMSPageFromWikiView(TendaView(self.bot).ms_dict), ephemeral=True)


async def setup(bot):
    await bot.add_cog(TestCog(bot))
