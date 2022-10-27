from io import BytesIO
import requests
import discord
from PIL import Image

def url_image_process(url, method, pil_img=None, filename="image.png", resize_rate=0.5, crop_size=400):
    # pillowで読み込み
    if pil_img is None:
        pil_img = Image.open(BytesIO(requests.get(url).content))

    if method == "crop":
        # 中心座標
        center_x = pil_img.width // 2
        center_y = pil_img.height // 2

        # トリミング
        pil_img = pil_img.crop((center_x - crop_size / 2, center_y - crop_size / 2, center_x + crop_size / 2, center_y + crop_size / 2))

    elif method == "resize":
        # リサイズ
        resize_size = (round(pil_img.width * resize_rate), round(pil_img.height * resize_rate))
        pil_img = pil_img.resize(resize_size)

    # discord用のファイルオブジェクト作成
    img_data = BytesIO()
    pil_img.save(img_data, format="png")
    img_data.seek(0)
    img_disc_file = discord.File(img_data, filename=filename)

    return img_disc_file
