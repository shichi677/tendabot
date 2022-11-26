import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(verbose=True)
load_dotenv(".env")
# 読み込むコグの名前を格納しておく。
COGS = ["cogs.eventcog", "cogs.tendacog", "cogs.draftcog"]
# COGS = ["cogs.eventcog", "cogs.tendacog"]

# クラスの定義。ClientのサブクラスであるBotクラスを継承。
class MyBot(commands.Bot):

    # MyBotのコンストラクタ。
    def __init__(self, command_prefix, intents, debugmode=False):
        self.debugmode = debugmode
        intents.members = True
        intents.message_content = True

        if debugmode:
            super().__init__(command_prefix, intents=intents, application_id=int(os.environ['debugbot_ID']))

        else:
            super().__init__(command_prefix, intents=intents, application_id=int(os.environ["tendabot_ID"]))

        self.select_ms_number_img = discord.File("./image/select_ms_number.webp", filename="select_ms_number.webp")

        self.latest_tendaview_message_id = None

    async def setup_hook(self) -> None:
        if not self.debugmode:
            await self.tree.sync(guild=discord.Object(id=int(os.environ["MOI_GUILD_ID"])))

        await self.tree.sync(guild=discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])))

async def main():
    debugmode = False

    bot = MyBot(command_prefix="?", intents=discord.Intents.default(), debugmode=debugmode)

    for cog in COGS:
        await bot.load_extension(cog)

    if debugmode:
        await bot.start(token=os.environ["DEBUG_BOT_TOKEN"], )
    else:
        await bot.start(token=os.environ["DISCORD_BOT_TOKEN"])

if __name__ == "__main__":

    discord.utils.setup_logging()
    asyncio.run(main())
