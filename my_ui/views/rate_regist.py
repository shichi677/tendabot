import discord
from my_ui import RateRegistModal
from typing import Optional
from my_ui.button.delete import DeleteButton


class RateRegistView(discord.ui.View):
    def __init__(self, tendaview, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.tendaview = tendaview
        self.add_item(DeleteButton("レーティング登録メッセージ"))

    @discord.ui.button(label="登録", style=discord.ButtonStyle.primary, custom_id="RateRegistView:regist")
    async def regist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RateRegistModal(self.tendaview))
