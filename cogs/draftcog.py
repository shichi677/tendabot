import importlib
import sys
import os
import discord
from discord.ext import commands
from discord import app_commands
import my_ui
from dotenv import load_dotenv
import logging
import logging.handlers
print(importlib.reload(my_ui))
from my_ui import DraftView
sys.path.append("../")

load_dotenv(verbose=True)
load_dotenv("../.env")

logger = logging.getLogger(__name__)

# コグとして用いるクラスを定義。
class DraftCog(commands.Cog):

    # TestCogクラスのコンストラクタ。Botを受取り、インスタンス変数として保持。
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ドラフト", description="MOIドラフト用メッセージを送信します")
    @app_commands.guilds(discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])), discord.Object(id=int(os.environ["MOI_GUILD_ID"])))
    async def call_draft_app(self, interaction: discord.Interaction):
        draft_app_embed = discord.Embed(title="ドラフト用メッセージ", description="ドラフト用メッセージへようこそ！", colour=discord.Colour.gold())
        draft_app_embed.add_field(name="初期設定", value="主催者などを設定します。")
        draft_app_embed.add_field(name="リーダー決め", value="ダイスでリーダーを決定します。")
        draft_app_embed.add_field(name="ドラフト", value="ドラフトを行います。")
        draft_app_embed.add_field(name="成績入力", value="各チームの成績を入力します。")
        draft_app_embed.add_field(name="結果発表", value="結果を表示します。")
        await interaction.response.send_message(embed=draft_app_embed, view=DraftView(self.bot))

async def setup(bot):
    await bot.add_cog(DraftCog(bot))
