import discord
from typing import Optional


class exeButton(discord.ui.Button):
    def __init__(self, button_label, input_callback, style: discord.ButtonStyle = discord.ButtonStyle.primary):
        super().__init__(style=style, label=button_label)
        self.input_callback = input_callback

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.input_callback


class ConfirmView(discord.ui.View):
    def __init__(self, button_label, input_callback, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.add_item(exeButton(button_label, input_callback))
