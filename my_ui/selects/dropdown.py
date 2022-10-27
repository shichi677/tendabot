import discord
# ドロップダウンメニュークラス
class Dropdown(discord.ui.Select):
    def __init__(self, options, placeholder, row=0):
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
