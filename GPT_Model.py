# GPT_Model.py
import os
import random
import base64
import openai

###############################################################################
# Replace with your actual OpenAI API key or any environment variable logic.
###############################################################################
openai.api_key = os.getenv('OpenAI_API_KEY')  # Make sure you have set OpenAI_API_KEY in your environment

client = openai


def get_random_image_paths(path, n):
    """
    函式說明： 從 path 收集所有 .jpg/.jpeg/.png 檔案，
    (1) 如果圖片數量大於等於 n，則隨機抽取 n 張
    (2) 如果少於 n，則回傳全部找到的圖片路徑。
    """
    image_files = []

    # 走訪所有子資料夾與檔案
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(root, file))

    # 若沒有找到任何圖片
    if not image_files:
        raise FileNotFoundError("No JPG or PNG image found in the dataset directory.")

    # 若圖片數量比 n 少，就回傳全部；否則隨機取 n 張
    if len(image_files) <= n:
        return image_files
    else:
        return random.sample(image_files, n)


def model_response(base64_image, path=None):
    """
    函式說明： 
    將圖片 (以 Base64 形式) 以及 Prompt 輸入模型，並**回傳**模型回覆文字 (而非直接印出)。
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Replace with your custom model name
        stream=True,
        temperature=1.2,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "圖中有那些物件?",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            },
            {
                "role": "system",
                "content": "針對圖片中的物件逐一回覆"
            }
        ],
    )

    # 收集串流回覆
    collected = []
    for reply in response:
        chunk = reply.choices[0].delta.content or ''
        collected.append(chunk)

    # 將所有 chunk 合併成完整回覆
    final_response = ''.join(collected)
    return final_response


def base64_response(path, n):
    """
    函式說明： 
    將某資料夾下的圖片路徑轉為 Base64 格式後呼叫 model_response，
    這是你先前隨機抽取 n 張的流程 (可保留或自行省略)。
    """
    random_images = get_random_image_paths(path, n)

    results = []
    for img_path in random_images:
        with open(img_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        reply = model_response(base64_image)
        result = (
            f"資料來源： {path}\n"
            f"照片檔名： {img_path}\n"
            f"模型回覆： {reply}\n"
            + ("-" * 79)
        )
        results.append(result)

    # 這個函式可以回傳所有的文字結果給 Flask，或直接列印
    return "\n\n".join(results)
