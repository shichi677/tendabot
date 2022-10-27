import discord

# レーティング登録用Modal
class RateRegistModal(discord.ui.Modal, title="レーティング登録"):

    rate_input = discord.ui.TextInput(
        label="レートを半角数字4桁で入力してください",
        style=discord.TextStyle.short,
        placeholder="例: 2650",
        required=True,
        max_length=4,
    )

    RATE_REGIST_INIT_EMBED = discord.Embed(title="レーティング登録", description="", colour=discord.Colour.blue())
    RATE_REGIST_INIT_EMBED.add_field(name="「登録」", value="レーティングを登録するウインドウを開きます。\nすでに登録している場合は再登録できます。", inline=False)
    RATE_REGIST_INIT_EMBED.add_field(name="「削除」", value="このメッセージ自体を削除します。", inline=False)

    def __init__(self, tendaview):
        super().__init__()
        self.tendaview = tendaview

    # 送信時の処理（レーティング登録処理）
    async def on_submit(self, interaction: discord.Interaction):

        # 入力されたレートを判定
        try:
            rate = int(self.rate_input.value)

            if not 1450 <= rate <= 2999:
                raise Exception("rate out of range")

        except Exception as e:
            print(f"regist rate error: {e}")
            await interaction.response.send_message(content=f"不正なレートです！\n1450 〜 2999の数字を入力してください！\nあなたの入力: {self.rate_input.value}", ephemeral=True)
            return

        # 同じ人が2度登録コマンドを入力した時の処理
        if interaction.user in self.tendaview.memberList:
            # 再登録したuserのmember_listのインデックスを取得
            chg_index = self.tendaview.memberList.index(interaction.user)
            self.tendaview.rateList[chg_index] = rate  # レート書き換え
            regist_comp_message = f"レーティング{int(self.rate_input.value)}で再登録完了したよ!"

        # 通常登録処理
        else:
            # 発言した人の名前，ID，レートポイントを記録
            self.tendaview.memberList.append(interaction.user)
            self.tendaview.rateList.append(rate)
            regist_comp_message = f"レーティング{int(self.rate_input.value)}で登録完了したよ!"

        # レート登録者、未登録者リスト
        regist_name_list = [member.display_name for member in self.tendaview.memberList]
        not_regist_name_list = [member.display_name for member in interaction.user.guild.voice_channels[0].members if not member.bot and member not in self.tendaview.memberList]

        # プログレスバー
        regist_ratio = len(regist_name_list) / (len(not_regist_name_list) + len(regist_name_list))
        regist_ratio_10 = int(10 * regist_ratio)
        progress_bar = "".join(["■"] * regist_ratio_10 + ["□"] * (10 - regist_ratio_10))

        # embed定義
        embed = discord.Embed(title=f"レート登録状況\n {int(regist_ratio * 100)}%\n{progress_bar}", description="", colour=discord.Colour.green())
        embed.add_field(name=f"登録者 {len(regist_name_list)}人", value="\n".join(regist_name_list))

        # 未登録者field
        if not_regist_name_list:
            embed.add_field(name="未登録者", value="\n".join(not_regist_name_list))

        else:
            embed.add_field(name="未登録者", value="なし")

        await interaction.response.edit_message(embeds=[self.RATE_REGIST_INIT_EMBED, embed])
        await interaction.followup.send(content=regist_comp_message, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        embed = discord.Embed(title="エラー", description="エラーが発生しました。", colour=discord.Colour.red())
        embed.add_field(name="エラー内容", value=error)
        await interaction.channel.send(embed=embed)
