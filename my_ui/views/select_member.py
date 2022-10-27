import discord
from my_ui.selects.dropdown import Dropdown
from my_ui.button.delete import DeleteButton
from decimal import Decimal, ROUND_HALF_UP
import random


# メンバー選択View
class MemberSelectDropdownView(discord.ui.View):
    def __init__(self, parent_message, channel_member_sotie_dict):
        super().__init__(timeout=None)

        # TendaViewのあるメッセージ（親メッセージ）
        self.parent_message = parent_message
        # 出撃回数を記録する辞書
        self.channel_member_sotie_dict = channel_member_sotie_dict

        # メンバー選択人数指定用ドロップダウンメニュー
        self.default_label_select_num = "5人"
        select_num_dropdown_options = []

        # 選択人数のoptionを作成
        for i in range(2, 7):
            default_flag = False
            if i == 5:
                default_flag = True
            select_option = discord.SelectOption(label=f"{i}人", description=f"ボイスチャットにいる人から{i}人選択します", emoji=f"{i}\u20e3", default=default_flag)
            select_num_dropdown_options.append(select_option)

        # チーム分けの方法選択用ドロップダウンメニュー
        self.default_label_select_method = "選出回数を考慮する"
        select_method_dropdown_options = [
            discord.SelectOption(label=self.default_label_select_method, description="各人の選出回数を考慮して選択します", emoji="✅", default=True),
            discord.SelectOption(label="選出回数を考慮しない", description="今までの選出回数を考慮せずにランダムで選択します", emoji="❓"),
        ]

        # ドロップダウンメニュー作成
        self.select_num_dropdown = Dropdown(select_num_dropdown_options, placeholder="testplace", row=0)
        self.select_method_dropdown = Dropdown(select_method_dropdown_options, placeholder="testplace", row=1)
        self.add_item(self.select_num_dropdown)
        self.add_item(self.select_method_dropdown)
        self.add_item(DeleteButton("メンバー選択メッセージ"))

    # 決定ボタン
    @discord.ui.button(label="決定", style=discord.ButtonStyle.green, custom_id="Dropdown:dicide", row=2)
    async def dicide(self, interaction: discord.Interaction, button: discord.ui.Button):

        # デフォルトの選択肢が選ばれたときvaluesが返すのは空リストなのでその処理
        if self.select_num_dropdown.values:
            select_num = int(self.select_num_dropdown.values[0].replace("人", ""))

        else:
            select_num = int(self.default_label_select_num.replace("人", ""))

        if self.select_method_dropdown.values:
            select_method = self.select_method_dropdown.values[0]

        else:
            select_method = self.default_label_select_method

        # print(select_num, select_method)

        # ボイスチャンネルに入っているメンバー
        voice_channel_members = []

        # 発言者がボイスチャンネルに入っているか
        if interaction.user.voice:
            # 発言した人が所属しているボイスチャンネルの名前
            author_voice_channel_name = interaction.user.voice.channel.name

            async for member in interaction.user.guild.fetch_members(limit=150):
                # ボイスチャンネルに入っているひと
                if member.voice:
                    # インタラクションした人と同じチャンネルにいるかつミュートしていない人
                    if author_voice_channel_name == member.voice.channel.name and (not member.voice.self_mute) and not (member.bot):
                        voice_channel_members.append(member)

            if len(voice_channel_members) < select_num:
                member_select_message = f"選択人数よりボイスチャンネル内にいる人が少ないよ！\n選択人数: {select_num}人\nボイスチャンネル人数 (ミュートを除く): {len(voice_channel_members)}人"
                embed = discord.Embed(title="エラー", description=member_select_message, colour=discord.Colour.red())

            else:

                sotie_num_message = ""
                if select_method == "選出回数を考慮する":
                    # key:diplay_name, value:1の辞書を作成
                    # 退出したメンバー
                    exit_members = set(self.channel_member_sotie_dict[author_voice_channel_name].keys()) - set([member.display_name for member in voice_channel_members])
                    if exit_members:
                        for member_name in exit_members:
                            del self.channel_member_sotie_dict[author_voice_channel_name][member_name]
                    # print(self.channel_member_sotie_dict[author_voice_channel_name])

                    # 新しく入ったメンバー
                    for member in voice_channel_members:
                        self.channel_member_sotie_dict[author_voice_channel_name].setdefault(member.display_name, 1)
                    # print(self.channel_member_sotie_dict[author_voice_channel_name])

                    # 連続で出撃する回数を求める
                    if len(self.channel_member_sotie_dict[author_voice_channel_name]) > select_num:
                        sotie_num = select_num / (len(self.channel_member_sotie_dict[author_voice_channel_name]) - select_num)
                        sotie_num = int(Decimal(str(sotie_num)).quantize(Decimal("0"), rounding=ROUND_HALF_UP))
                        sotie_num_message = f"現在の構成では{sotie_num}回連続で出撃することになります！\n"

                    # 出撃回数をindex, 要素をdisplay_nameとした配列を定義(100回連続出撃まで対応)
                    sotie_num_member_list = [[] for _ in range(20)]

                    # 出撃回数が記録された辞書からdisplay_name, 出撃回数を記録
                    for member_name, sortie_num in self.channel_member_sotie_dict[author_voice_channel_name].items():
                        sotie_num_member_list[sortie_num].append(member_name)

                    # 出撃するメンバーを記録する配列
                    select_members_list = []
                    # カウンタ
                    cnt = 0

                    # 選択人数になるまで出撃回数が低いほうからメンバーを取り出していく
                    for inspection_members in sotie_num_member_list:

                        cnt += len(inspection_members)
                        if cnt > select_num:
                            break

                        else:
                            select_members_list.extend(inspection_members)

                    # 出撃回数が多いが、出撃しなければならない人数を計算
                    fill_member_num = select_num - len(select_members_list)

                    # 出撃する人をランダムで選出
                    fill_members_list = random.sample(inspection_members, fill_member_num)

                    # ランダムで選出された人を追加
                    select_members_list.extend(fill_members_list)

                    # ボイスチャットにいるメンバーに対して
                    for member in voice_channel_members:

                        # メンバーが選出メンバーの中にいた時
                        if member.display_name in select_members_list:

                            self.channel_member_sotie_dict[author_voice_channel_name][member.display_name] += 1

                            # 足して1の人(新しく入った人)の処理
                            if self.channel_member_sotie_dict[author_voice_channel_name][member.display_name] == 1:
                                self.channel_member_sotie_dict[author_voice_channel_name][member.display_name] += 1

                        else:
                            self.channel_member_sotie_dict[author_voice_channel_name][member.display_name] = 1

                    # 表示処理
                    member_select_message = ""
                    first_flag = True
                    for member_name in select_members_list:
                        if first_flag:
                            member_select_message += f"__{member_name}　({self.channel_member_sotie_dict[author_voice_channel_name][member_name] - 1}回目)__\n"
                            first_flag = False
                        else:
                            member_select_message += f"{member_name}　({self.channel_member_sotie_dict[author_voice_channel_name][member_name] - 1}回目)\n"

                elif select_method == "選出回数を考慮しない":
                    member_select_message = ""
                    selected_members = random.sample(voice_channel_members, select_num)  # ランダムサンプル

                    first_flag = True
                    for member in selected_members:
                        if first_flag:
                            member_select_message += f"__{member.display_name}__\n"
                            first_flag = False
                        else:
                            member_select_message += f"{member.display_name}\n"

                # embed記述
                embed = discord.Embed(title="メンバー選択", description=f"{select_num}人のメンバーを選択しました！\n{sotie_num_message}", color=0x00FF00)
                embed.add_field(name="メンバー", value=member_select_message)
                embed.set_footer(text="※下線がついている人はホストをお願いします")

        else:
            member_select_message = "メンバー選択する人はボイスチャンネルに入ってください！"
            embed = discord.Embed(title="エラー", description=member_select_message, colour=discord.Colour.red())

        for option in self.select_num_dropdown.options:
            if option.label == f"{select_num}人":
                option.default = True

            else:
                option.default = False

        for option in self.select_method_dropdown.options:
            if option.label == select_method:
                option.default = True

            else:
                option.default = False

        await interaction.response.edit_message(view=self, embed=embed)
