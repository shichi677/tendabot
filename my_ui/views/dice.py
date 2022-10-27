import discord
import random
from my_ui.button.delete import DeleteButton

# ダイスロールview
class DiceView(discord.ui.View):

    # ダイスロール初期embed
    DICE_INIT_EMBED = discord.Embed(title="ダイスロール", description="", colour=discord.Colour.blue())
    DICE_INIT_EMBED.add_field(name="「ダイスを振る」", value="1から100までの目があるダイスを振ります。", inline=False)
    DICE_INIT_EMBED.add_field(name="「ログクリア」", value="今までの結果を削除します。", inline=False)
    DICE_INIT_EMBED.add_field(name="「削除」", value="このメッセージ自体を削除します。", inline=False)

    def __init__(self):
        # クラス継承
        super().__init__(timeout=None)
        # メッセージ削除ボタン追加
        self.add_item(DeleteButton("ダイスロールメッセージ"))
        self.dice_result = {}
        self.dice_log = []

    @discord.ui.button(label="ダイスを振る", style=discord.ButtonStyle.primary, custom_id="DiceView:roll_dice")
    async def roll_dice(self, interaction: discord.Interaction, button: discord.ui.Button):

        # ログクリアボタン取得
        for item in self.children:
            if item.custom_id == "DiceView:clear_log":
                clear_log_button = item

        clear_log_button.disabled = False

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
        self.dice_log.append((interaction.user.display_name, dice))
        self.dice_result[interaction.user.display_name] = dice

        # ダイス結果取得
        min_list, max_list, mid_list = get_dice_result(self.dice_result.items())

        # embed生成
        embed = discord.Embed(title="ダイスログ", description="\n".join([f"{name}さんの出した目は**{dice}**です！" for name, dice in self.dice_log]), color=0x00FF00)
        embed.add_field(name="一番小さいひと", value="".join([f"{name}: {dice}" for name, dice in min_list]))
        embed.add_field(name="50に近いひと", value="".join([f"{name}: {dice}" for name, dice in mid_list]))
        embed.add_field(name="一番大きいひと", value="".join([f"{name}: {dice}" for name, dice in max_list]))

        # メッセージ編集
        await interaction.response.edit_message(view=self, embeds=[self.DICE_INIT_EMBED, embed])

    @discord.ui.button(label="ログクリア", style=discord.ButtonStyle.success, custom_id="DiceView:clear_log", disabled=True)
    async def dice_result_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        # クリアembed
        embed = discord.Embed(title="ダイスログ", description="クリアしました", colour=discord.Colour.green())

        # ログクリア
        self.dice_result.clear()
        self.dice_log.clear()

        # クリアしたらボタン無効
        button.disabled = True

        # メッセージ編集
        await interaction.response.edit_message(view=self, embeds=[self.DICE_INIT_EMBED, embed])
