import discord
from collections import deque, Counter
from decimal import Decimal, ROUND_HALF_UP
import sys
import random
from ..selects.dropdown import Dropdown
import asyncio
from ..button.delete import DeleteButton

TEAM_NAME = ["A", "B", "C", "D", "E"]
sys.setrecursionlimit(300000)


def judge_rate(rate):  # レート（数字）からレート（記号）に変更する関数
    RatingList = ["S-", "A+", "A", "A-"]

    if rate >= 2700:
        rating = RatingList[0]
    elif rate >= 2400:
        rating = RatingList[1]
    elif rate >= 2100:
        rating = RatingList[2]
    elif rate >= 1950:
        rating = RatingList[3]
    else:
        rating = "A-未満"

    return rating


def list_subtraction(subtrahend_list, minuend_list):

    result_list = []
    result_dict = {}
    subtrahend_dict = Counter(subtrahend_list)
    minuend_dict = Counter(minuend_list)

    for ele in subtrahend_list:
        result_dict[ele] = subtrahend_dict[ele] - minuend_dict[ele]

    for key, value in result_dict.items():
        for i in range(value):
            result_list.append(key)

    return result_list


def rec(r_dp, a, i, j, route, ans):

    if i == 0:
        if j == 0:
            ans.append(list(route))

        return ans

    if r_dp[i - 1][j] != float("inf"):
        rec(r_dp, a, i - 1, j, route, ans)

    if j - a[i - 1] >= 0 and r_dp[i - 1][j - a[i - 1]] != float("inf"):
        route.append(a[i - 1])
        rec(r_dp, a, i - 1, j - a[i - 1], route, ans)
        route.popleft()


def Partial_sum_dp(N, total_sum, target_list):
    dp = [[float("inf") for _ in range(total_sum + 1)] for _ in range(N + 1)]
    dp[0][0] = 0

    for i in range(N):
        for j in range(total_sum):
            dp[i + 1][j] = min(dp[i + 1][j], dp[i][j])
            if j >= target_list[i]:
                dp[i + 1][j] = min(dp[i + 1][j], dp[i][j - target_list[i]] + 1)

    return dp


def team_divider(member_name_list, ratelist, number_of_teams):
    N = len(ratelist)

    rate_all_sum = sum(ratelist)

    rate_member_dict = {}
    member_rate_dict = {}

    for member, rate in zip(member_name_list, ratelist):
        rate_member_dict.setdefault(rate, []).append(member)
        member_rate_dict[member] = rate

    member_num = N // number_of_teams
    member_mod = N % number_of_teams
    # print(member_num, member_mod)

    target_ratelist = ratelist.copy()

    divide_member_result = []
    divide_rate_result = []

    route = deque()
    ans = []
    cnt = 0
    M = len(target_ratelist)
    mod = 1 if member_mod > 0 else 0

    dp = Partial_sum_dp(N, rate_all_sum, ratelist)

    while len(divide_rate_result) < number_of_teams:

        rate_sum = sum(target_ratelist)
        rec(dp, target_ratelist, M, rate_sum // M * (member_num + mod) + cnt, route, ans)

        if ans:
            divide_rate_result.append(ans[0])
            M -= len(ans[0])
            target_ratelist = list_subtraction(target_ratelist, [rate for rate in ans[0]])

            team = []
            for rate in ans[0]:
                team.append(rate_member_dict[rate].pop())

            divide_member_result.append(team)

            dp = Partial_sum_dp(M, rate_sum, target_ratelist)

            route = deque()
            ans = []
            cnt = 0

            member_mod -= 1
            member_mod = max(member_mod, 0)
            if member_mod == 0:
                mod = 0

        else:
            cnt = cnt + 1

    return divide_member_result, divide_rate_result


def random_group_divider(input_list, divide_num):

    result_list = []
    q, mod = divmod(len(input_list), divide_num)
    if q < 1:

        return None

    else:
        for i in range(divide_num):

            if i < mod:
                sample_list = random.sample(input_list, q + 1)

            else:
                sample_list = random.sample(input_list, q)

            result_list.append(sample_list)
            input_list = list_subtraction(input_list, sample_list)

        return result_list


# チーム分けを行うView
class TeamDivideDropdownView(discord.ui.View):

    TEAM_DIVIDE_INIT_EMBED = discord.Embed(title="チーム決め", description="", colour=discord.Colour.blue())
    TEAM_DIVIDE_INIT_EMBED.add_field(name="チーム分けの方法", value="「ランダム」ではレーティング登録は必要ありません。", inline=False)
    TEAM_DIVIDE_INIT_EMBED.add_field(name="ボイスチャット移動", value="決定されたチームにボイスチャットを移動させます", inline=False)

    def __init__(self, member_list, rate_list):
        super().__init__(timeout=None)
        self.divided_team_list = []
        self.rate_list = rate_list
        self.member_list = member_list

        self.add_item(DeleteButton("チーム決めメッセージ", row=2))

        # Set the options that will be presented inside the dropdown
        # チーム数選択用ドロップダウンメニュー
        self.default_label_team_num = "2チーム"
        team_num_dropdown_options = [
            discord.SelectOption(label=self.default_label_team_num, description="レーティングを登録した人達を2チームに分けます", emoji="2️⃣", default=True),
            discord.SelectOption(label="3チーム", description="レーティングを登録した人達を3チームに分けます", emoji="3️⃣"),
        ]

        # チーム分けの方法選択用ドロップダウンメニュー
        self.default_label_divide_method = "レーティング平均"
        divide_method_dropdown_options = [
            discord.SelectOption(
                label=self.default_label_divide_method,
                description="各チームのレーティングの平均が同じになるようにチームを分けます(要レーティング登録)",
                emoji="⚖",
                default=True,
            ),
            discord.SelectOption(label="レーティング上下", description="レーティングが高いほうからチームを分けます(要レーティング登録)", emoji="📶"),
            discord.SelectOption(label="ランダム", description="レーティング関係なくボイスチャンネルにいる人をランダムにチームを分けます", emoji="❓"),
        ]

        self.team_num_dropdown = Dropdown(team_num_dropdown_options, placeholder="testplace", row=0)
        self.divide_method_dropdown = Dropdown(divide_method_dropdown_options, placeholder="testplace", row=1)
        self.add_item(self.team_num_dropdown)
        self.add_item(self.divide_method_dropdown)

    # 決定ボタン
    @discord.ui.button(label="決定", style=discord.ButtonStyle.green, custom_id="Dropdown:dicide", row=2)
    async def dicide(self, interaction: discord.Interaction, button: discord.ui.Button):
        # デフォルトの選択肢が選ばれたときvaluesが返すのは空リストなのでその処理
        if self.team_num_dropdown.values:
            team_num = int(self.team_num_dropdown.values[0].replace("チーム", ""))

        else:
            team_num = int(self.default_label_team_num.replace("チーム", ""))

        if self.divide_method_dropdown.values:
            divide_method = self.divide_method_dropdown.values[0]

        else:
            divide_method = self.default_label_divide_method

        # フラグ決定
        voice_exist_flag = True
        regist_exist_flag = True

        if len(self.rate_list) < team_num:
            regist_exist_flag = False

        error_flag = False
        embed = discord.Embed(title="", colour=discord.Colour.orange())
        embed.set_footer(text="※下線がついている人はホストをお願いします。")

        # 登録されているメンバーが1人以下の時の処理
        if divide_method == "レーティング平均" or divide_method == "レーティング上下":

            if regist_exist_flag:
                # レーティング平均を選択したときの処理
                if divide_method == "レーティング平均":
                    embed.title = "チーム分け結果 (レート平均)"
                    try:
                        self.divided_team_list.clear()
                        divided_member_list, divided_rate_list = team_divider(self.member_list, self.rate_list, team_num)
                        self.divided_team_list = divided_member_list
                        # print("abc", divided_member_list, divided_rate_list)

                        # 各チームの平均レーティング計算

                        for i in range(team_num):
                            team_rating = int(Decimal(float(sum(divided_rate_list[i]) / len(divided_rate_list[i]))).quantize(Decimal("0"), rounding=ROUND_HALF_UP))
                            team_members = [f"__{divided_member_list[i][0].display_name}__"]
                            team_members += [teammember.display_name for teammember in divided_member_list[i][1:]]
                            embed.add_field(name=f"チーム{TEAM_NAME[i]}【平均レート： {judge_rate(team_rating)} ({team_rating})】", value="\n".join(team_members), inline=False)

                    except Exception as e:
                        embed = discord.Embed(title="エラー", description="平均が近い組み合わせを見つけることができませんでした。", colour=discord.Colour.red())
                        print(e)
                        error_flag = True

                # レーティング上下を選択したときの処理
                if divide_method == "レーティング上下":
                    embed.title = "チーム分け結果 (レート上下)"
                    memberrate_list = sorted(zip(self.rate_list, self.member_list), key=lambda x: x[0])
                    q, mod = divmod(len(self.member_list), team_num)
                    self.divided_team_list.clear()

                    cnt = 0
                    team_divide_message = "チーム分け完了しました！\n\n"
                    for i in range(0, len(memberrate_list), q):
                        divdlist = memberrate_list[i: i + q]

                        if i + q > len(memberrate_list):
                            break

                        if cnt < mod:
                            divdlist.append(memberrate_list.pop(i + q))

                        cnt += 1

                        print(divdlist)
                        member_divsort_list = [member for rate, member in divdlist]
                        # rate_divsort_list = [rate for rate, member in divdlist]

                        self.divided_team_list.append(member_divsort_list)

                        team_rating = int(Decimal(float(sum([rate for rate, member in divdlist]) / len([rate for rate, member in divdlist]))).quantize(Decimal("0"), rounding=ROUND_HALF_UP))
                        team_members = [f"__{member_divsort_list[0].display_name}__"]
                        team_members += [teammember.display_name for teammember in member_divsort_list[1:]]
                        embed.add_field(name=f"チーム{TEAM_NAME[i // q]}【平均レート： {judge_rate(team_rating)} ({team_rating})】", value="\n".join(team_members), inline=False)

            else:
                embed = discord.Embed(title="エラー", description=f"登録されている人数ではチーム分けできないよ......\nレーティング登録人数: {len(self.rate_list)}人", colour=discord.Colour.red())
                error_flag = True

        elif divide_method == "ランダム":

            author_voice_channel = interaction.user.voice.channel.name
            voice_chat_member = []

            async for member in interaction.user.guild.fetch_members(limit=150):
                # ボイスチャンネルに入っているひと
                if member.voice:
                    # インタラクションした人と同じチャンネルにいるかつミュートしていない人
                    if author_voice_channel == member.voice.channel.name and (not member.voice.self_mute) and (not member.bot):
                        voice_chat_member.append(member)

            if len(voice_chat_member) < team_num:
                voice_exist_flag = False

            # 登録されているかボイスチャンネルに人がいる場合
            if voice_exist_flag or regist_exist_flag:

                # 登録がある場合
                if regist_exist_flag:
                    self.divided_team_list = random_group_divider(self.member_list, team_num)

                # 登録がないがボイスチャンネルに人がいる場合
                elif voice_exist_flag:
                    self.divided_team_list = random_group_divider(voice_chat_member, team_num)
                    # print(len(voice_chat_member), voice_chat_member, self.divided_team_list)

                embed.title = "チーム分け結果 (ランダム)"
                for i in range(team_num):
                    team_members = [f"__{self.divided_team_list[i][0].display_name}__"]
                    team_members += [teammember.display_name for teammember in self.divided_team_list[i][1:]]
                    embed.add_field(name=f"チーム{TEAM_NAME[i]}", value="\n".join(team_members), inline=False)

            # 登録されておらず、ボイスチャンネルにもいない場合
            else:
                team_divide_message = "ボイスチャンネル人数もしくはレート登録人数が足りません！\n"
                team_divide_message += f"レーティング登録人数: {len(self.rate_list)}人\n"
                team_divide_message += f"ボイスチャンネル参加人数 (ミュートを除く): {len(voice_chat_member)}人\n"
                embed = discord.Embed(title="エラー", description=team_divide_message, colour=discord.Colour.red())
                error_flag = True

        if not error_flag:
            for child in self.children:
                if child.custom_id == "TeamDivideDropdownView:move_voice_channel":
                    child.disabled = False

        for option in self.team_num_dropdown.options:
            if option.label == f"{team_num}チーム":
                option.default = True

            else:
                option.default = False

        for option in self.divide_method_dropdown.options:
            if option.label == divide_method:
                option.default = True

            else:
                option.default = False

        await interaction.response.edit_message(view=self, embeds=[self.TEAM_DIVIDE_INIT_EMBED, embed])

    @discord.ui.button(label="ボイスチャット移動", style=discord.ButtonStyle.blurple, custom_id="TeamDivideDropdownView:move_voice_channel", row=3, disabled=True)
    async def move_voice_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True)

        # メッセージが送られたギルド（サーバー）取得
        currentguild = interaction.user.guild
        # ボイスチャンネルの一覧を取得
        voicechannel_list = currentguild.voice_channels[1:]

        for i in range(len(self.divided_team_list)):
            for member in self.divided_team_list[i]:
                await member.edit(voice_channel=voicechannel_list[i])

            if len(self.divided_team_list) * len(self.divided_team_list[i]) > 10:
                await asyncio.sleep(7)

        button.disabled = True
        await interaction.message.edit(view=self)
        await interaction.followup.send("ボイスチャンネル移動を行いました！")
