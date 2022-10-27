import discord

class Button(discord.ui.Button):
    def __init__(self, x: int, y: int, style: discord.ButtonStyle = discord.ButtonStyle.secondary):
        super().__init__(style=style, label=f"{x + 4 * y + 1}", row=y)

    async def callback(self, interaction: discord.Interaction):

        if self.style == discord.ButtonStyle.secondary:
            self.style = discord.ButtonStyle.success

        else:
            self.style = discord.ButtonStyle.secondary

        await interaction.response.edit_message(view=self.view)

# 機体選択画面の16機体からランダムで選択、提示するview
class RandomSelectMSView(discord.ui.View):
    def __init__(self, parent_message, select_num):
        # クラス継承
        super().__init__(timeout=None)
        # 親メッセージ(TendaViewのあるメッセージ)を取得
        self.parent_message = parent_message

        for x in range(4):
            for y in range(4):
                if x + 4 * y + 1 == select_num:
                    self.add_item(Button(x, y, style=discord.ButtonStyle.success))
                    continue
                self.add_item(Button(x, y))
