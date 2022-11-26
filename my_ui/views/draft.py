import discord
from collections.abc import Sequence
from collections import defaultdict
from typing import Optional, Union, Any, List
from my_ui import Dropdown
import datetime
import random
from my_ui.button.delete import DeleteButton
import logging
import logging.handlers
import re

logger = logging.getLogger(__name__)


class DraftView(discord.ui.View):
    def __init__(self, bot: discord.ext.commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

        self.organizer_id = None
        # self.organizer_id = 615083789407748097  # debug

        self.team_num = None
        # self.team_num = 2  # debug

        self.leader_ids = None
        # self.leader_ids = [615083789407748097, 759185408197656587, 758857025516994570, 977851535750995998]  # debug

        self.designate_status = {}

        self.team = defaultdict(list)

        # # debug
        # self.team = {}
        # for leader_id in self.leader_ids:
        #     self.team[leader_id] = []

        self.input_result_options = defaultdict(dict)

        self.result_dict = defaultdict(dict)

        self.got_member_leaders = []

    @discord.ui.button(label="初期設定", style=discord.ButtonStyle.success, custom_id="DraftView:init", row=0)
    async def init(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.DraftInitView = DraftInitView(self.bot, self, interaction.guild.members)
        self.get_member = interaction.guild.get_member
        await interaction.response.send_message(content="①ドラフト名を設定してください(任意)\n②ドラフト主催者を選択してください。\n(選択欄ボタンで選択欄を切り替えることができます。)\n③チーム数を設定してください。", view=self.DraftInitView, ephemeral=True)

    # @discord.ui.button(label="リーダー決め", style=discord.ButtonStyle.primary, custom_id="DraftView:leaderdicide", row=0, disabled=True)
    @discord.ui.button(label="リーダー決め", style=discord.ButtonStyle.primary, custom_id="DraftView:leaderdicide", row=0, disabled=False)  # debug
    async def leader_dicide(self, interaction: discord.Interaction, button: discord.ui.Button):
        leader_desc_emb = discord.Embed(title="リーダー決め", description=f"参加者がダイスを振って値が大きい{self.team_num}人がリーダーとなります。", colour=discord.Colour.red())
        await interaction.response.send_message(view=LeaderDicideView(self), embed=leader_desc_emb)

    # @discord.ui.button(label="ドラフト", style=discord.ButtonStyle.primary, custom_id="DraftView:draft", row=0, disabled=True)
    @discord.ui.button(label="ドラフト", style=discord.ButtonStyle.primary, custom_id="DraftView:draft", row=0, disabled=False)  # debug
    async def draft(self, interaction: discord.Interaction, button: discord.ui.Button):
        get_member = interaction.guild.get_member
        draft_emb = discord.Embed(title="ドラフト", description="ドラフトを行います。\nリーダーは「選手選択」ボタンを押して指名を行ってください。\nすべてのリーダーの指名が完了したら主催者は「結果発表」ボタンを押して結果を表示してください。", colour=discord.Colour.from_rgb(245, 245, 245))
        team_emb = discord.Embed(title="チーム", description="", colour=discord.Colour.blue())

        for leader_id in self.leader_ids:
            team_emb.add_field(name=f"{get_member(leader_id).display_name}チーム", value="-", inline=False)
        await interaction.response.send_message(view=DraftingView(self), embeds=[draft_emb, team_emb])

    # @discord.ui.button(label="成績入力", style=discord.ButtonStyle.primary, custom_id="DraftView:input_result", row=0, disabled=True)
    @discord.ui.button(label="成績入力", style=discord.ButtonStyle.primary, custom_id="DraftView:input_result", row=0, disabled=False)  # debug
    async def input_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(view=InputResultView(self), ephemeral=True)

    # @discord.ui.button(label="結果発表", style=discord.ButtonStyle.primary, custom_id="DraftView:show_result", row=0, disabled=False)
    @discord.ui.button(label="結果発表", style=discord.ButtonStyle.primary, custom_id="DraftView:show_result", row=0, disabled=False)  # debug
    async def show_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = InputResultView(self).generate_result_embed()
        await interaction.response.send_message(content="以下の結果を全体に公開します\nよろしいですか？", view=ConfirmView(embeds), embeds=embeds, ephemeral=True)


class MemberListButton(discord.ui.Button):
    def __init__(
        self,
        *,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        label: Optional[str] = None,
        disabled: bool = False,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        emoji: Optional[Union[str, discord.Emoji, discord.PartialEmoji]] = None,
        row: Optional[int] = None,
        drop_down_row: Optional[int] = None,
        drop_down_placeholder: Optional[int] = None,
    ):
        self.label_num = label.replace("選択欄", "")
        self.dropdown_row = drop_down_row
        self.dropdown_placeholder = drop_down_placeholder
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)

    async def callback(self, interaction: discord.Interaction) -> Any:
        self.view.remove_item(self.view.member_select_dropdown)
        self.view.member_select_dropdown = MemberSelectDropdown(
            self.view.member_select_options[25 * (int(self.label_num) - 1): 25 * int(self.label_num)], placeholder=f"{self.dropdown_placeholder}{self.label_num}", row=self.dropdown_row
        )
        self.view.add_item(self.view.member_select_dropdown)

        for item in self.view.children:
            if item.custom_id.startswith("DraftInitView:MemberListButton"):
                if item.custom_id == f"DraftInitView:MemberListButton{self.label_num}":
                    item.style = discord.ButtonStyle.primary
                else:
                    item.style = discord.ButtonStyle.gray

        await interaction.response.edit_message(view=self.view)


class DraftNameModal(discord.ui.Modal, title="ドラフト名設定"):
    draft_name_input = discord.ui.TextInput(label="ドラフト名を設定してください(任意)", style=discord.TextStyle.short, placeholder="ドラフト名を入力", required=False, max_length=100)

    def __init__(self, view: discord.ui.view) -> None:
        super().__init__(timeout=None)
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        self.view.draft_name = self.draft_name_input.value
        await interaction.response.defer()


class DraftInitView(discord.ui.View):
    def __init__(self, bot: discord.ext.commands.Bot, view: DraftView, guild_members: Sequence[discord.Member]):
        super().__init__(timeout=None)
        self.bot = bot
        self.view = view
        self.draft_name = None

        self.member_select_options = [discord.SelectOption(label=member.display_name, value=member.id) for i, member in enumerate(guild_members) if not member.bot]
        # self.member_select_options = [discord.SelectOption(label=f"test{i}") for i in range(30)]  # debug

        list_num = -(-len(self.member_select_options) // 25)
        if len(self.member_select_options) > 25:
            member_select_options = self.member_select_options[:25]
        else:
            member_select_options = self.member_select_options

        self.member_select_dropdown = Dropdown(member_select_options, placeholder="②主催者選択欄1", row=1)
        self.add_item(self.member_select_dropdown)
        for i in range(1, list_num + 1):
            style = discord.ButtonStyle.gray
            if i == 1:
                style = discord.ButtonStyle.primary
            self.add_item(MemberListButton(label=f"選択欄{i}", style=style, custom_id=f"DraftInitView:MemberListButton{i}", row=2, drop_down_row=1, drop_down_placeholder="②主催者選択欄"))

        team_num_options = [discord.SelectOption(label=f"{i}チーム", value=i, emoji=f"{i}\u20e3") for i in range(2, 10)]
        self.team_num_dropdown = Dropdown(team_num_options, placeholder="③参加チーム数", row=3)
        self.add_item(self.team_num_dropdown)

    @discord.ui.button(label="①ドラフト名設定(任意)", style=discord.ButtonStyle.primary, custom_id="DraftInitView:draftnameButton", row=0)
    async def draft_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DraftNameModal(self))

    @discord.ui.button(label="決定", style=discord.ButtonStyle.success, custom_id="DraftInitView:dicideButton", row=4)
    async def dicide(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not self.draft_name:
            draft_name = "MOIドラフト"

        else:
            draft_name = self.draft_name

        # 主催者とチーム数が入力されている時
        if self.member_select_dropdown.values and self.team_num_dropdown.values:
            self.view.organizer_id = int(self.member_select_dropdown.values[0])
            organizer_name = interaction.guild.get_member(self.view.organizer_id).display_name
            self.view.team_num = int(self.team_num_dropdown.values[0])
            JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")
            dt_now = datetime.datetime.now(JST)
            now = dt_now.strftime("%Y年%m月%d日")

            init_embed = discord.Embed(colour=discord.Colour.blue(), title=draft_name)
            init_embed.add_field(name="開催日", value=now, inline=False)
            init_embed.add_field(name="主催者", value=organizer_name, inline=False)
            init_embed.add_field(name="参加チーム数", value=self.view.team_num)
            for item in self.view.children:
                if item.custom_id == "DraftView:leaderdicide":
                    item.disabled = False
                if item.custom_id == "DraftView:init":
                    item.disabled = True

            await interaction.response.send_message("ドラフト設定が完了しました！", embed=init_embed)
            draft_view_message_id = interaction.message.reference.message_id
            draft_view_message = interaction.channel.get_partial_message(draft_view_message_id)
            await draft_view_message.edit(view=self.view)

        else:
            await interaction.response.send_message("主催者またはチーム数が入力されていません。\n入力内容を確認して決定ボタンを押してください。", ephemeral=True)


# ダイスロールview
class LeaderDicideView(discord.ui.View):
    def __init__(self, view: DraftView):
        # クラス継承
        super().__init__(timeout=None)
        self.view = view
        # メッセージ削除ボタン追加
        self.add_item(DeleteButton("ダイスロールメッセージ"))
        self.dice_result = {}
        self.dice_log = []

    @discord.ui.button(label="ダイスを振る", style=discord.ButtonStyle.primary, custom_id="LeaderDicideView:roll_dice")
    async def roll_dice(self, interaction: discord.Interaction, button: discord.ui.Button):

        # ログクリアボタン取得
        for item in self.children:
            if item.custom_id == "LeaderDicideView:clear_log" or item.custom_id == "LeaderDicideView:showresult":
                item.disabled = False

        # ダイス結果(最大、最小、真ん中)を計算する
        def get_dice_result(dice_result, nearrest_num: int = 50):
            # ダイス結果をダイスの小さい順にソート
            dice_sorted = sorted(dice_result, key=lambda x: x[1])

            # ダイス値のmin, max算出
            min_dice = dice_sorted[0][1]
            max_dice = dice_sorted[-1][1]

            # ダイスが最小、最大の人の名前リスト (複数いる場合があるため)
            max_name_list = [(name, dice) for name, dice in dice_result if dice == max_dice]
            min_name_list = [(name, dice) for name, dice in dice_result if dice == min_dice]

            # 指定した数値に一番近いキーを見つける (デフォルトは50)
            offset_list = [abs(dice - nearrest_num) for name, dice in dice_result]
            nearest_name_list = [(name, dice) for name, dice in dice_result if abs(dice - nearrest_num) == min(offset_list)]

            return min_name_list, max_name_list, nearest_name_list

        # ダイスの目をランダムに選択
        dice = random.randint(1, 100)

        # ダイス結果を保存
        if interaction.user.id in self.dice_result:
            await interaction.response.send_message("ダイスを振ることができるのは1人1回までです！", ephemeral=True)

        else:
            self.dice_log.append((interaction.user.display_name, dice))
            self.dice_result[interaction.user.id] = dice

            # ダイス結果取得
            min_list, max_list, mid_list = get_dice_result(self.dice_result.items())

            # embed生成
            embed = discord.Embed(title="リーダー決めダイスログ", description="\n".join([f"{name}さんがダイスを振りました" for name, dice in self.dice_log]), color=0x00FF00)

            # メッセージ編集
            await interaction.response.edit_message(view=self, embeds=[embed])

    @discord.ui.button(label="リーダー決定", style=discord.ButtonStyle.success, custom_id="LeaderDicideView:showresult", disabled=True)
    async def dice_result_show(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.view.organizer_id == interaction.user.id:
            dice_sorted = sorted(self.dice_result.items(), key=lambda x: x[1], reverse=True)
            embed = discord.Embed(title="リーダー決めダイス結果", description="下線がついている人がリーダーです。", colour=discord.Colour.green())
            embed.add_field(
                name="結果",
                value="\n".join(
                    [
                        f"{interaction.guild.get_member(result[0]).display_name}: {result[1]}"
                        if i >= self.view.team_num
                        else f"__{interaction.guild.get_member(result[0]).display_name}__: {result[1]}"
                        for i, result in enumerate(dice_sorted)
                    ]
                ),
            )
            self.view.leader_ids = [result[0] for i, result in enumerate(dice_sorted) if i < self.view.team_num]
            await interaction.response.send_message(embed=embed)

            for item in self.view.children:
                if item.custom_id == "DraftView:draft":
                    item.disabled = False

                if item.custom_id == "DraftView:leaderdicide":
                    item.disabled = True

            draft_view_message = interaction.channel.get_partial_message(interaction.message.reference.message_id)
            await draft_view_message.edit(view=self.view)

        else:
            await interaction.response.send_message("このボタンは主催者のみが使用できます。", ephemeral=True)

    @discord.ui.button(label="ログクリア", style=discord.ButtonStyle.success, custom_id="LeaderDicideView:clear_log", disabled=True)
    async def dice_result_clear(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.view.organizer_id == interaction.user.id:

            # クリアembed
            embed = discord.Embed(title="リーダー決めダイスログ", description="クリアしました", colour=discord.Colour.green())

            # ログクリア
            self.dice_result.clear()
            self.dice_log.clear()

            # クリアしたらボタン無効
            button.disabled = True

            # メッセージ編集
            await interaction.response.edit_message(view=self, embeds=[embed])

        else:
            await interaction.response.send_message("このボタンは主催者のみが使用できます。", ephemeral=True)


class MemberSelectDropdown(discord.ui.Select):
    def __init__(self, options, placeholder, row=0):
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, row=row)

    async def callback(self, interaction: discord.Interaction):
        self.view.view.designate_status[interaction.user.id] = int(self.values[0])
        await interaction.response.defer()


class MemberSelectView(discord.ui.View):
    def __init__(self, view: DraftView, guild_members: Sequence[discord.Member]):
        # クラス継承
        super().__init__(timeout=None)
        self.view = view
        self.select_value = None

        self.member_select_options = [discord.SelectOption(label=member.display_name, value=member.id) for i, member in enumerate(guild_members) if not member.bot]
        # self.member_select_options = [discord.SelectOption(label=member.display_name, value=member.id) for i, member in enumerate(guild_members)] # debug
        # self.member_select_options = [discord.SelectOption(label=member, value=i) for i, member in enumerate([f"test{j}" for j in range(29)])]  # debug

        list_num = -(-len(self.member_select_options) // 25)
        if len(self.member_select_options) > 25:
            member_select_options = self.member_select_options[:25]
        else:
            member_select_options = self.member_select_options

        self.member_select_dropdown = MemberSelectDropdown(member_select_options, placeholder="選手選択欄1", row=0)
        self.add_item(self.member_select_dropdown)
        for i in range(1, list_num + 1):
            style = discord.ButtonStyle.gray
            if i == 1:
                style = discord.ButtonStyle.primary
            self.add_item(MemberListButton(label=f"選択欄{i}", style=style, custom_id=f"DraftingView:MemberListButton{i}", row=1, drop_down_row=0, drop_down_placeholder="選手選択欄"))

    @discord.ui.button(label="指名", style=discord.ButtonStyle.success, custom_id="MemberSelectView:designate", row=2)
    async def select_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.member_select_dropdown.values:
            get_member = interaction.guild.get_member

            # self.view.designate_status[interaction.user.id] = int(self.member_select_dropdown.select_value)

            # self.view.designate_status[interaction.user.id] = id
            draft_message = interaction.channel.get_partial_message(interaction.message.reference.message_id)
            print(draft_message)
            draft_message = await draft_message.fetch()
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"{get_member(self.view.designate_status[interaction.user.id]).display_name}さんを指名しました。", ephemeral=True)
            print(self.view.designate_status)
            designate_status_embed = discord.Embed(
                title="指名状況",
                description="\n".join([f"{interaction.guild.get_member(leader_id).display_name}が指名を完了しました。" for leader_id, designated_id in self.view.designate_status.items()]),
                colour=discord.Colour.green(),
            )
            # designate_status_embed = discord.Embed(title="指名状況", description="\n".join([f"{leader_id}が指名を完了しました。" for leader_id, designated_id in self.view.designate_status.items()]))  # debug

            await draft_message.edit(embeds=[draft_message.embeds[0], draft_message.embeds[1], designate_status_embed])

        else:
            await interaction.response.send_message("選手が選択されていません。\n選手選択欄を確認してください。", ephemeral=True)


# ダイスロールview
class DraftConflictView(discord.ui.View):
    def __init__(self, view: DraftView, designated_id):
        # クラス継承
        super().__init__(timeout=None)
        self.view = view
        self.designated_id = designated_id
        # メッセージ削除ボタン追加
        self.add_item(DeleteButton("ダイスロールメッセージ"))
        self.dice_result = {}
        self.dice_log = []

    @discord.ui.button(label="ダイスを振る", style=discord.ButtonStyle.primary, custom_id="LeaderDicideView:roll_dice")
    async def roll_dice(self, interaction: discord.Interaction, button: discord.ui.Button):

        # ログクリアボタン取得
        for item in self.children:
            if item.custom_id == "LeaderDicideView:clear_log" or item.custom_id == "LeaderDicideView:showresult":
                item.disabled = False

        # ダイス結果(最大、最小、真ん中)を計算する
        def get_dice_result(dice_result, nearrest_num: int = 50):
            # ダイス結果をダイスの小さい順にソート
            dice_sorted = sorted(dice_result, key=lambda x: x[1])

            # ダイス値のmin, max算出
            min_dice = dice_sorted[0][1]
            max_dice = dice_sorted[-1][1]

            # ダイスが最小、最大の人の名前リスト (複数いる場合があるため)
            max_name_list = [(name, dice) for name, dice in dice_result if dice == max_dice]
            min_name_list = [(name, dice) for name, dice in dice_result if dice == min_dice]

            # 指定した数値に一番近いキーを見つける (デフォルトは50)
            offset_list = [abs(dice - nearrest_num) for name, dice in dice_result]
            nearest_name_list = [(name, dice) for name, dice in dice_result if abs(dice - nearrest_num) == min(offset_list)]

            return min_name_list, max_name_list, nearest_name_list

        # ダイスの目をランダムに選択
        dice = random.randint(1, 100)

        # ダイス結果を保存
        if interaction.user.id in self.dice_result:
            await interaction.response.send_message("ダイスを振ることができるのは1人1回までです！", ephemeral=True)

        else:
            self.dice_log.append((interaction.user.display_name, dice))
            self.dice_result[interaction.user.id] = dice

            # ダイス結果取得
            min_list, max_list, mid_list = get_dice_result(self.dice_result.items())

            # embed生成
            embed = discord.Embed(title="", description="\n".join([f"{name}さんがダイスを振りました" for name, dice in self.dice_log]), color=0x00FF00)

            # メッセージ編集
            await interaction.response.edit_message(view=self, embeds=[interaction.message.embeds[0], embed])

    @discord.ui.button(label="結果表示", style=discord.ButtonStyle.success, custom_id="LeaderDicideView:showresult", disabled=True)
    async def dice_result_show(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.view.organizer_id == interaction.user.id:
            dice_sorted = sorted(self.dice_result.items(), key=lambda x: x[1], reverse=True)
            get_member = interaction.guild.get_member
            embed = discord.Embed(
                title=f"{get_member(self.designated_id).display_name} 抽選結果",
                description=f"{get_member(dice_sorted[0][0]).display_name}が{get_member(self.designated_id).display_name}を獲得しました。",
                colour=discord.Colour.green(),
            )
            # embed = discord.Embed(title=self.title, description=f"{dice_sorted[0][0]}が{self.designated_id}を獲得しました。", colour=discord.Colour.green())  # debug

            embed.add_field(
                name="結果",
                value="\n".join(
                    [
                        f"__{interaction.guild.get_member(result[0]).display_name}__: {result[1]}" if i == 0 else f"{interaction.guild.get_member(result[0]).display_name}: {result[1]}"
                        for i, result in enumerate(dice_sorted)
                    ]
                ),
            )

            self.view.team[dice_sorted[0][0]].append(self.designated_id)
            self.view.got_member_leaders.append(dice_sorted[0][0])
            await interaction.response.send_message(embed=embed)

            draft_message = await interaction.channel.get_partial_message(interaction.message.reference.message_id).fetch()

            team_emb = discord.Embed(title="チーム", description="", colour=discord.Colour.blue())
            for leader_id in self.view.leader_ids:
                team_members = [get_member(id).display_name for id in self.view.team[leader_id]]
                if team_members:
                    value = "\n".join([get_member(id).display_name for id in self.view.team[leader_id]])
                else:
                    value = "-"
                team_emb.add_field(name=f"{get_member(leader_id).display_name}チーム", value=value, inline=False)

            await draft_message.edit(embeds=[draft_message.embeds[0], team_emb, draft_message.embeds[2]])

            for item in self.view.children:
                if item.custom_id == "DraftView:draft":
                    item.disabled = False

            if len(self.view.got_member_leaders) == len(self.view.leader_ids):
                self.view.got_member_leaders.clear()

            self.view.designate_status.clear()
            # draft_view_message = interaction.channel.get_partial_message(interaction.message.reference.message_id)
            # await draft_view_message.edit(view=self.view)

        else:
            await interaction.response.send_message("このボタンは主催者のみが使用できます。", ephemeral=True)

    @discord.ui.button(label="ログクリア", style=discord.ButtonStyle.success, custom_id="LeaderDicideView:clear_log", disabled=True)
    async def dice_result_clear(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.view.organizer_id == interaction.user.id:

            # クリアembed
            embed = discord.Embed(title="リーダー決めダイスログ", description="クリアしました", colour=discord.Colour.green())

            # ログクリア
            self.dice_result.clear()
            self.dice_log.clear()

            # クリアしたらボタン無効
            button.disabled = True

            # メッセージ編集
            await interaction.response.edit_message(view=self, embeds=[interaction.message.embeds[0], embed])

        else:
            await interaction.response.send_message("このボタンは主催者のみが使用できます。", ephemeral=True)


class DraftingView(discord.ui.View):
    def __init__(self, view: DraftView):
        # クラス継承
        super().__init__(timeout=None)
        self.view = view

    @discord.ui.button(label="選手選択", style=discord.ButtonStyle.primary, custom_id="DraftingView:selectmember")
    async def select_member(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id in self.view.leader_ids:

            if interaction.user.id in self.view.got_member_leaders:
                await interaction.response.send_message("指名が一巡するまで再指名することはできません。", ephemeral=True)

            else:
                selected_member = []
                for leader_id, team_members in self.view.team.items():

                    selected_member.append(interaction.guild.get_member(int(leader_id)))
                    for member_id in team_members:
                        selected_member.append(interaction.guild.get_member(int(member_id)))
                print(selected_member)
                members = [member for member in interaction.guild.members if member not in selected_member]
                member_select_view = MemberSelectView(self.view, members)
                await interaction.response.send_message(view=member_select_view, ephemeral=True)

        else:
            await interaction.response.send_message("このボタンはリーダーのみが使用できます。", ephemeral=True)

    # @discord.ui.button(label="結果発表", style=discord.ButtonStyle.primary, custom_id="DraftingView:showresult", disabled=True)
    @discord.ui.button(label="結果発表", style=discord.ButtonStyle.primary, custom_id="DraftingView:showresult", disabled=False)
    async def show_result(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id == self.view.organizer_id:
            await interaction.response.defer()
            get_member = interaction.guild.get_member
            this_message = interaction.message

            designate = defaultdict(list)

            for leader_id, designated_id in self.view.designate_status.items():
                designate[designated_id].append(leader_id)

            get_member = interaction.guild.get_member
            for designated_id, leader_ids in designate.items():
                if len(leader_ids) > 1:
                    selecters = "さん\n".join([get_member(id).display_name for id in leader_ids])
                    conflict_embed = discord.Embed(
                        title=f"{get_member(designated_id).display_name}さん抽選ダイス",
                        description=f"{selecters}さんは\n{interaction.guild.get_member(int(designated_id)).display_name}さん獲得のためにダイスを振ってください",
                        colour=discord.Colour.yellow(),
                    )
                    await interaction.followup.send(embed=conflict_embed, view=DraftConflictView(self.view, designated_id))

                elif len(leader_ids) == 1:
                    self.view.team[leader_ids[0]].append(designated_id)
                    self.view.got_member_leaders.append(leader_ids[0])

                print(leader_ids)

            # designate_status_embed = discord.Embed(title="指名状況", description="\n".join([f"{interaction.guild.get_member(int(leader_id)).display_name} → {interaction.guild.get_member(int(designated_id)).display_name}" for leader_id, designated_id in self.view.designate_status.items()]))
            designate_status_embed = discord.Embed(
                title="指名結果",
                description="\n".join([f"{get_member(leader_id).display_name} → {get_member(designated_id).display_name}" for leader_id, designated_id in self.view.designate_status.items()]),
                colour=discord.Colour.green(),
            )
            # designate_status_embed = discord.Embed(title="指名結果", description="\n".join([f"{leader_id} → {designated_id}" for leader_id, designated_id in self.view.designate_status.items()]))  # debug

            team_emb = discord.Embed(title="チーム", description="", colour=discord.Colour.blue())
            for leader_id in self.view.leader_ids:
                team_members = [get_member(id).display_name for id in self.view.team[leader_id]]
                if team_members:
                    value = "\n".join([get_member(id).display_name for id in self.view.team[leader_id]])
                else:
                    value = "-"
                team_emb.add_field(name=f"{get_member(leader_id).display_name}チーム", value=value, inline=False)

            await interaction.edit_original_response(embeds=[this_message.embeds[0], team_emb, designate_status_embed])
            self.view.designate_status.clear()
            if len(self.view.got_member_leaders) == len(self.view.leader_ids):
                self.view.got_member_leaders.clear()

        else:
            await interaction.response.send_message("このボタンは主催者のみが使用できます。", ephemeral=True)


class InputResultDropdown(discord.ui.Select):
    def __init__(self, options, placeholder, row=0):
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, row=row)

    async def callback(self, interaction: discord.Interaction):
        self.view: InputResultView

        if self.placeholder == "チーム":
            option_type = "team"
        elif self.placeholder == "ミッションの種類":
            option_type = "mission_type"

        self.view.draft_view.input_result_options[interaction.user.id][option_type] = self.values[0]
        await interaction.response.defer()


class RegistResultView(discord.ui.View):
    def __init__(self, draft_view: DraftView):
        super().__init__(timeout=None)
        self.draft_view = draft_view

    @discord.ui.button(label="成績登録", style=discord.ButtonStyle.success, custom_id="DraftingView:selectmembersss", row=3)
    async def regist_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        # input_result
        selected_options = self.draft_view.input_result_options[interaction.user.id]
        team_name = selected_options["team"]
        mission_type = selected_options["mission_type"]
        mission_time = selected_options["mission_time"]
        self.draft_view.result_dict[team_name][mission_type] = mission_time

        embeds = InputResultView(self.draft_view).generate_result_embed()

        await interaction.response.send_message(embeds=embeds, ephemeral=True)


class Feedback(discord.ui.Modal, title="ミッション時間入力"):
    mission_time = discord.ui.TextInput(label="時間を0m:ss.ssの形式で入力してください\n例: 02:13.74", placeholder="例:02:13.74", required=True)

    def __init__(self, view) -> None:
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        self.view: InputResultView
        if re.fullmatch(r"0[0-7]:[0-5][0-9]\.\d{2}", self.mission_time.value):
            self.view.input_result_options[interaction.user.id]["mission_time"] = self.mission_time.value
            await interaction.response.send_message(content=f"入力した時間: {self.mission_time.value}", view=RegistResultView(self.view), ephemeral=True)
        else:
            raise Exception

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("時間の形式が不正です。\n入力した時間が0m:ss.ssの形式でないか、8分以上の時間が入力されています。", ephemeral=True)


class InputResultView(discord.ui.View):
    def __init__(self, draft_view: DraftView):
        super().__init__(timeout=None)
        self.draft_view = draft_view

        team_select_options = [discord.SelectOption(label=f"{self.draft_view.get_member(leader_id).display_name}さんチーム") for leader_id in self.draft_view.team.keys()]
        mission_type_select_options = [discord.SelectOption(label=mission_type) for mission_type in ("TRIAL", "SURVIVAL", "BOSS")]
        team_select_dropdown = InputResultDropdown(team_select_options, placeholder="チーム", row=0)
        mission_select_dropdown = InputResultDropdown(mission_type_select_options, placeholder="ミッションの種類", row=1)

        self.add_item(team_select_dropdown)
        self.add_item(mission_select_dropdown)

    def generate_result_embed(self):
        def calc_total_mission_time(times: List[str]):
            minute = 0
            second = 0
            for str_time in times:
                match_obj = re.fullmatch(r"0(\d):([0-5][0-9]\.\d{2})", str_time)
                minute += float(match_obj.group(1))
                second += float(match_obj.group(2))
            min = second // 60
            sec = second % 60

            minute += min

            return f"{minute:02.0f}:{sec:05.02f}"
            # result embeds

        embeds = []
        total_time_dic = {}
        for team_name, result in self.draft_view.result_dict.items():
            result_embed = discord.Embed(title=team_name, colour=discord.Colour.blue())
            mission_times = []
            for mission_type, mission_time in result.items():
                result_embed.add_field(name=mission_type, value=mission_time)
                mission_times.append(mission_time)

            total_time = calc_total_mission_time(mission_times)
            total_time_dic[team_name] = total_time
            # result_embed.add_field(name="Total", value=total_time, inline=False)
            embeds.append(result_embed)

        # ranking embed
        medals = ["🥇", "🥈", "🥉"] + [""] * len(total_time_dic)
        ranking_embed = discord.Embed(title="ランキング", colour=discord.Colour.gold())
        sorted_total_results = sorted(total_time_dic.items(), key=lambda x: x[1])
        sorted_total_times = [total_time for team_name, total_time in sorted_total_results]

        rank = [None] * len(sorted_total_times)
        rank[0] = 0
        cnt = 1
        for i in range(len(sorted_total_times) - 1):
            if sorted_total_times[i] == sorted_total_times[i + 1]:
                rank[i + 1] = rank[i]
                cnt += 1

            else:
                rank[i + 1] = rank[i] + cnt
                cnt = 1

        for i, result in enumerate(sorted_total_results):
            team_name, total_time = result
            ranking_embed.add_field(name=f"{medals[rank[i]]}{team_name}", value=total_time, inline=False)
        embeds.append(ranking_embed)

        return embeds

    @discord.ui.button(label="時間入力", style=discord.ButtonStyle.primary, custom_id="DraftingView:dd", row=2)
    async def input_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(Feedback(self.draft_view))


class ConfirmView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=None)
        self.embeds = embeds

    @discord.ui.button(label="はい", style=discord.ButtonStyle.primary, custom_id="DraftingView:dd", row=0)
    async def input_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embeds=self.embeds)
