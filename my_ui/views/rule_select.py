import discord
import random
from ..selects.dropdown import Dropdown
from ..button.delete import DeleteButton
from modules import url_image_process

# コスト選択ボタン
class CostButton(discord.ui.Button):
    def __init__(self, txt: str, default_style: discord.ButtonStyle, row: int, custom_id: str):
        # Buttonクラス継承
        super().__init__(label=txt, style=default_style, row=row, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):

        # ボタン色切り替え
        if self.style == discord.ButtonStyle.primary:
            self.style = discord.ButtonStyle.secondary
        else:
            self.style = discord.ButtonStyle.primary

        # ボタン色更新
        await interaction.response.edit_message(view=self.view)


# コスト、マップ選択View
class SelectTargetButtonView(discord.ui.View):
    def __init__(self, place_list, default_place_list, view, method="マップ、コスト両方"):
        super().__init__(timeout=None)
        self.add_item(DeleteButton("コスト・マップ選択メッセージ", row=3))
        self.method = method
        row = 0
        self.previous_view = view
        self.interation_message = None

        # ボタン配置
        for i in range(len(place_list)):
            if i % 5 == 0 and i != 0:
                row += 1

            # デフォルトリストにあるものはボタンを青色に
            if place_list[i] in default_place_list:
                style = discord.ButtonStyle.primary
            else:
                style = discord.ButtonStyle.secondary

            # ボタンをviewに追加
            self.add_item(CostButton(f"{place_list[i]}", style, row=row, custom_id=f"{place_list[i]}"))
            # print(row, place_list[i], i)

    # マップやコストを選択
    def select(self, select_list, previous):
        # 前に選択したものがあれば
        if previous:
            try:
                # 前に選択したものの選択重みを0にする
                pre_select_idx = select_list.index(previous)
                weight = [0 if i == pre_select_idx else 1 for i in range(len(select_list))]

            # すべて選択してしまっていたら重みをすべて1にする
            except ValueError:
                weight = [1] * len(select_list)

            # 重みによってランダムに選択
            select = random.choices(select_list, weight)

        # 前に選択していない場合重みを用いずに選択
        else:
            select = random.choices(select_list)
            weight = ""

        return select[0]

    # 前へボタンで前のviewを表示
    @discord.ui.button(label="前へ", style=discord.ButtonStyle.green, custom_id="SelectTargetButtonView:prev", row=3)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=self.previous_view)

    # 決定ボタン
    @discord.ui.button(label="決定", style=discord.ButtonStyle.green, custom_id="SelectTargetButtonView:next", row=3)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):

        # マップ及びコスト選択時
        if self.method == "マップ、コスト両方":
            # 青色(primary)ボタンをマップ選択対象にする
            self.map_select_list = []
            for item in self.children:
                if item.style == discord.ButtonStyle.primary:
                    self.map_select_list.append(item.custom_id)
            # 前に選択したコスト、マップを入力して選択、前に選択したものを記録
            self.previous_view.parent_view.previous_cost_select = self.select(self.previous_view.cost_select_list, self.previous_view.parent_view.previous_cost_select)
            self.previous_view.parent_view.previous_map_select = self.select(self.map_select_list, self.previous_view.parent_view.previous_map_select)

            # 選択結果embed
            embed = discord.Embed(title="選択結果", description="", colour=discord.Colour.blue())
            embed.add_field(name="コスト", value=self.previous_view.parent_view.previous_cost_select, inline=True)
            embed.add_field(name="マップ", value=self.previous_view.parent_view.previous_map_select, inline=True)

            # マップ画像url取得
            image_url = self.previous_view.parent_view.stage_dict[self.previous_view.parent_view.previous_map_select]["image_url"]
            # マップ画像リサイズ
            filename = "selected_map.webp"
            file = url_image_process(url=image_url, method="resize", filename=filename, resize_rate=0.24)
            embed.set_image(url=f"attachment://{filename}")

            await interaction.response.edit_message(content="", embed=embed, attachments=[file])
            msg = await interaction.original_response()
            msg.content = f"コスト、マップを選択しました。{self.previous_view.parent_view.previous_cost_select}、{self.previous_view.parent_view.previous_map_select}"

        else:
            self.select_list = []
            for item in self.children:
                if item.style == discord.ButtonStyle.primary:
                    self.select_list.append(item.custom_id)

            if self.method == "コストのみ":
                # 前に選択したコストを入力して選択、前に選択したものを記録
                self.previous_view.previous_cost_select = self.select(self.select_list, self.previous_view.previous_cost_select)

                # 選択結果embed
                embed = discord.Embed(title="選択結果", description="", colour=discord.Colour.blue())
                embed.add_field(name="コスト", value=self.previous_view.previous_cost_select, inline=True)

                await interaction.response.edit_message(content="", embed=embed, attachments=[])
                msg = await interaction.original_response()
                msg.content = f"コストを選択しました。{self.previous_view.previous_cost_select}"

            if self.method == "マップのみ":
                self.previous_view.previous_map_select = self.select(self.select_list, self.previous_view.previous_map_select)
                # 選択結果embed
                embed = discord.Embed(title="選択結果", description="", colour=discord.Colour.blue())
                embed.add_field(name="マップ", value=self.previous_view.previous_map_select, inline=True)

                # マップ画像url取得
                image_url = self.previous_view.stage_dict[self.previous_view.previous_map_select]["image_url"]
                # マップ画像リサイズ
                filename = "selected_map.webp"
                file = url_image_process(url=image_url, method="resize", filename=filename, resize_rate=0.24)
                embed.set_image(url=f"attachment://{filename}")
                await interaction.response.edit_message(content="", embed=embed, attachments=[file])
                msg = await interaction.original_response()
                msg.content = f"マップを選択しました。{self.previous_view.previous_map_select}"

        await interaction.client.cogs["EventCog"].message_queue.put(msg)


class MapAndCostSelectView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=None)
        self.add_item(DeleteButton("コスト・マップ選択メッセージ", row=3))
        self.parent_view = parent_view
        self.button_placement(
            place_list=self.parent_view.COST_LIST,
            default_place_list=self.parent_view.DEFAULT_COST_LIST,
        )
        self.map_view = SelectTargetButtonView(place_list=self.parent_view.MAP_LIST, default_place_list=self.parent_view.DEFAULT_MAP_LIST, view=self)

    def button_placement(self, place_list, default_place_list):
        row = 0
        for i in range(len(place_list)):
            if i % 5 == 0 and i != 0:
                row += 1

            if place_list[i] in default_place_list:
                style = discord.ButtonStyle.blurple
            else:
                style = discord.ButtonStyle.gray
            self.add_item(CostButton(f"{place_list[i]}", style, row=row, custom_id=f"{place_list[i]}"))
            # print(row, place_list[i], i)

    @discord.ui.button(label="前へ", style=discord.ButtonStyle.green, custom_id="SelectTargetButtonView:prev", row=3)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=self.parent_view)

    @discord.ui.button(label="次へ", style=discord.ButtonStyle.green, custom_id="SelectTargetButtonView:next", row=3)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cost_select_list = []
        for item in self.children:
            if item.style == discord.ButtonStyle.blurple:
                self.cost_select_list.append(item.custom_id)
        await interaction.response.edit_message(view=self.map_view)


# ルール選択View
class RuleSelectDropdownView(discord.ui.View):
    COST_LIST = [i for i in range(200, 750, 50)]
    DEFAULT_COST_LIST = [i for i in range(300, 750, 50)]
    DEFAULT_MAP_LIST = ["墜落跡地", "熱帯砂漠", "無人都市", "廃墟都市", "北極基地", "地下基地", "補給基地"]
    RULE_LIST = ["ベーシック", "エースマッチ", "シンプルバトル", "シャッフルターゲット", "ミックスアップ"]

    def __init__(self, stage_dict):
        super().__init__(timeout=None)
        self.add_item(DeleteButton("コスト・マップ選択メッセージ", row=3))
        self.previous_cost_select = None
        self.previous_map_select = None
        self.interation_message = None
        self.stage_dict = stage_dict
        self.MAP_LIST = []
        for key, value in self.stage_dict.items():
            if value["place"] == "ground":
                self.MAP_LIST.append(key)

        self.cost_select_view = SelectTargetButtonView(place_list=self.COST_LIST, default_place_list=self.DEFAULT_COST_LIST, view=self, method="コストのみ")
        self.map_select_view = SelectTargetButtonView(place_list=self.MAP_LIST, default_place_list=self.DEFAULT_MAP_LIST, view=self, method="マップのみ")
        self.map_cost_select_view = MapAndCostSelectView(parent_view=self)

        # Set the options that will be presented inside the dropdown
        # メンバー選択人数指定用ドロップダウンメニュー
        self.default_label_select_rule = "コストのみ"
        select_rule_dropdown_options = [
            # 🏞️
            discord.SelectOption(label=self.default_label_select_rule, description="コストのみをランダムで選択します", emoji="🔢", default=False),
            discord.SelectOption(label="マップのみ", description="マップのみをランダムで選択します", emoji="🗺"),
            discord.SelectOption(label="マップ、コスト両方", description="マップのみをランダムで選択します", emoji="*⃣"),
        ]

        self.select_rule_dropdown = Dropdown(select_rule_dropdown_options, placeholder="ランダムで選択するものを選んでください")
        self.add_item(self.select_rule_dropdown)

    # 決定ボタン
    @discord.ui.button(label="次へ", style=discord.ButtonStyle.green, custom_id="Dropdown:dicide", row=3)
    async def dicide(self, interaction: discord.Interaction, button: discord.ui.Button):

        # デフォルトの選択肢が選ばれたときvaluesが返すのは空リストなのでその処理
        if self.select_rule_dropdown.values:
            self.select_rule = self.select_rule_dropdown.values[0]

        else:
            self.select_rule = self.default_label_select_rule

        message = "選択対象を決めてね！\n※青色：選択対象"
        if self.select_rule == "コストのみ":
            await interaction.response.edit_message(content=message, view=self.cost_select_view)

        if self.select_rule == "マップのみ":
            await interaction.response.edit_message(content=message, view=self.map_select_view)

        if self.select_rule == "マップ、コスト両方":
            await interaction.response.edit_message(content=message, view=self.map_cost_select_view)
