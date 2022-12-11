import re
import alkana
import romkan
import splitter

alkana.add_external_data("./alkana_dict.csv")

# reference https://mackro.blog.jp/archives/8479732.html
def replace_alphabet_to_kana(text):

    output = ""

    # search word of 3 character or more and to kana
    while word := re.search(r"[a-z-A-Z]{3,}", text):
        output += text[: word.start()] + word_to_kana(word.group())
        text = text[word.end():]

    return output + text


def word_to_kana(word):

    # if English word
    if kana := alkana.get_kana(word.lower()):
        return kana

    else:
        hiraganized_word = romkan.to_katakana(word.lower())

        # if not ro-maji
        if re.search("[a-zA-Z]+", hiraganized_word):
            output = ""
            split_result = splitter.split(word.lower())
            # if compound word
            if len(split_result) > 1:
                # to kana by each splited word
                for splited_word in split_result:
                    output += word_to_kana(splited_word)

                return output

            # if not compund word
            elif len(split_result) <= 1:
                return word

        # if ro-maji
        else:
            return hiraganized_word


# 絵文字IDは読み上げない
def remove_custom_emoji(text):
    pattern = r"<:[a-zA-Z0-9_]+:[0-9]+>"  # カスタム絵文字のパターン
    return re.sub(pattern, "", text)  # 置換処理


# URLなら省略
def urlAbb(text):
    pattern = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    if re.search(pattern, text):
        return "URLが送信されました " + re.sub(pattern, "", text)

    else:
        return text


def custom_process(text):
    pattern = r"[*_]"
    return re.sub(pattern, "", text)  # 置換処理


# message.contentをテキストファイルに書き込み
def CreateText(input_text):
    output_text = remove_custom_emoji(input_text)
    output_text = custom_process(output_text)
    output_text = urlAbb(output_text)
    output_text = replace_alphabet_to_kana(output_text)

    return output_text[:30]
