import discord
import random
from my_ui.button.delete import DeleteButton

# 機体選択画面の16機体からランダムで選択、提示するview
class RandomSelectMSView(discord.ui.View):
    SELECT_MS_INIT_EMBED = discord.Embed(title="機体選択", description="\n各々に振り分けられた番号の機体で出撃してください！", color=0x00FF00)
    # 画像読み込み
    file_name = "select_ms_number.webp"
    select_ms_number_img = discord.File(f"./image/{file_name}", filename="select_ms_number.webp")
    SELECT_MS_INIT_EMBED.set_image(url=f"attachment://{file_name}")

    def __init__(self):
        # クラス継承
        super().__init__(timeout=None)
        self.add_item(DeleteButton("機体選択メッセージ"))

    # 前へボタンで前のviewを表示
    @discord.ui.button(label="選択", style=discord.ButtonStyle.green, custom_id="RandomSelectMSView:select")
    async def select(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ms番号を決定する
        def generate_select_ms_embed():
            # embed定義
            embed = discord.Embed(title="機体選択結果", description="", color=0x00FF00)

            # 各メンバーの番号をランダムで算出、メンバー名と番号をembedのフィールドに追加
            numbers = random.sample(range(1, 16), k=len(ch_members))
            for member_name, number in zip(ch_members, numbers):
                embed.add_field(name=member_name, value=number % 16)
            file_name = "select_ms_number.webp"
            select_ms_number_img = discord.File(f"./image/{file_name}", filename="select_ms_number.webp")
            # embed.set_image(url=f"attachment://{file_name}")
            return embed, select_ms_number_img

        # ボタンを押した人のボイス情報
        push_user_voice = interaction.user.voice

        # ボタンを押した人のボイス情報がなければエラー
        if push_user_voice is None:
            embed = discord.Embed(title="エラー", description="ボイスチャンネルに入った状態でボタンを押してね！")

        # ボタンを押した人がボイスチャンネルに入っているとき
        else:
            # ボイスチャンネル内メンバー格納用リスト
            ch_members = []

            # サーバー内メンバー取得
            for member in interaction.guild.members:

                # ボイスチャンネルに入っていない or botだったら無視
                if member.voice is None or member.bot:
                    continue

                else:
                    # メンバーのチャンネルとボタン押した人のチャンネルが一致していたらappend
                    if member.voice.channel == push_user_voice.channel:
                        ch_members.append(member.display_name)

            embed, select_ms_number_img = generate_select_ms_embed()

        await interaction.response.edit_message(embeds=[self.SELECT_MS_INIT_EMBED, embed])
        msg = await interaction.original_response()
        msg.content = "機体番号を表示しました。"
        await interaction.client.cogs["EventCog"].message_queue.put(msg)
