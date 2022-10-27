import re

# 絵文字IDは読み上げない
def remove_custom_emoji(text):
    pattern = r"<:[a-zA-Z0-9_]+:[0-9]+>"  # カスタム絵文字のパターン
    return re.sub(pattern, "", text)  # 置換処理


# URLなら省略
def urlAbb(text):
    pattern = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    exist_url = False

    if re.match(pattern, text):
        exist_url = True

    return exist_url, re.sub(pattern, "URLが送信されました", text)  # 置換処理


def custom_process(text):
    pattern = r"[*_]"
    return re.sub(pattern, "", text)  # 置換処理


def str_num_limit(text):
    return text[:30] + "以下略"


# message.contentをテキストファイルに書き込み
def CreateText(inputText):
    inputText = remove_custom_emoji(inputText)  # 絵文字IDは読み上げない
    inputText = custom_process(inputText)

    exist_url, outputText = urlAbb(inputText)  # URLなら省略

    if len(outputText) > 30:
        outputText = str_num_limit(outputText)

    return outputText
