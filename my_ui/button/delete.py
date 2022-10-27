import discord

# Define a simple View that gives us a confirmation menu
class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="はい", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        button.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()


class DeleteButton(discord.ui.Button):
    def __init__(self, delete_msg_name, row=None, style: discord.ButtonStyle = discord.ButtonStyle.danger):
        super().__init__(style=style, label="削除", row=row)
        self.delete_msg_name = delete_msg_name

    async def callback(self, interaction: discord.Interaction):

        ori_message = interaction.message
        confirm = Confirm()
        await interaction.response.send_message(f"{self.delete_msg_name}を削除します！\nよろしいですか？", view=confirm, ephemeral=True)
        await confirm.wait()

        if confirm.value:
            try:
                await ori_message.delete()

            except discord.NotFound:
                await interaction.followup.send("メッセージの削除に失敗しました。\nメッセージがすでに削除されています。", ephemeral=True)

            except discord.HTTPException:
                await interaction.followup.send("メッセージの削除に失敗しました。", ephemeral=True)
