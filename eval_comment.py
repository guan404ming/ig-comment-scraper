import openai
import json
import emoji
import re

# 設置 API Key
API_KEY = "YOUR_API_KEY"


# 讀取 JSON 檔案中的評論
def load_comments(file_path):
    def is_only_emoji(text):
        """判斷文本是否只包含表情符號（emoji）"""
        text_without_emoji = re.sub(r"\s", "", text)
        return all(char in emoji.EMOJI_DATA for char in text_without_emoji)

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    comments = [
        item["node"]["text"]
        for item in data
        if "node" in item
        and "text" in item["node"]
        and not is_only_emoji(item["node"]["text"])
    ]
    return comments


def generate_prompt(comments):
    prompt = f"""
    你是一個專家評估 AI，請根據 Social Appearance Anxiety Scale (SAAS) 量表評分以下評論：
    
    所有評論: "{comments}"，將所有評論視爲不同個體進行評分，刪去僅有符號評論。並儲存成不同的 JSON，目前共有 {len(comments)} 個 comments。｀
    
    **評分標準（使用 5 點 Likert Scale，1=完全不同意，5=完全同意）：**
    
    1.  I feel comfortable with the way I appear after seeing virtual influencers' posts. (Reverse-coded) 
    2.  I feel nervous about taking pictures of myself after seeing virtual influencers' posts.
    3.  I get tense when I compare my appearance to virtual influencers in their posts.
    4.  I am concerned that people would not like me because my appearance is not as polished as virtual influencers'.
    5.  I worry that others notice flaws in my appearance after seeing how virtual influencers look.
    6.  I am concerned that people will find me unappealing compared to virtual influencers.
    7.  I am afraid that my appearance does not match the beauty standards set by virtual influencers.
    8.  I worry that my appearance will make life more difficult for me after seeing virtual influencers' posts.
    9.  I am concerned that I have missed out on opportunities because I don’t look like virtual influencers.
    10. I get nervous about interacting with others because I don’t look as perfect as virtual influencers.
    11. I feel anxious when I think others might compare my appearance to virtual influencers'.
    12. I am frequently afraid that I do not meet the beauty standards I see in virtual influencers’ posts.
    13. I worry that people will judge my appearance negatively after seeing virtual influencers.
    14. I am uncomfortable when I think others notice flaws in my appearance compared to virtual influencers.
    15. I worry that a romantic partner will/would lose interest in me because I do not look like virtual influencers.
    16. I am concerned that people think I am not good-looking after seeing virtual influencers’ posts.
    
    **請嚴格以 array of JSON 格式返回數據，items 的格式如下：**
    {{
        "original_comment": "我對於看到虛擬網紅的貼文後，對自己的外貌感到有一點點焦慮。",
        "measurement1": 3,
        "measurement2": 4,
        "measurement3": 5,
        ...
        "measurement16": 2,
        "reason": "這條評論顯示出該用戶對於外貌標準的焦慮，但程度較為適中。"
    }}
    """

    return prompt


def get_scores(comment):
    client = openai.OpenAI(
        api_key=API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/"
    )

    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {
                "role": "system",
                "content": "請根據 SAAS 量表評分評論，嚴格按照 JSON 格式輸出。請確保輸出評分可以被 python json.loads 正確解析 ",
            },
            {"role": "user", "content": generate_prompt(comment)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "SAAS_Evaluation",
                "schema": {
                    "type": "object",
                    "properties": {
                        "scores": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "original_comment": {"type": "string"},
                                    "measurement1": {"type": "string"},
                                    "measurement2": {"type": "string"},
                                    "measurement3": {"type": "string"},
                                    "measurement4": {"type": "string"},
                                    "measurement5": {"type": "string"},
                                    "measurement6": {"type": "string"},
                                    "measurement7": {"type": "string"},
                                    "measurement8": {"type": "string"},
                                    "measurement9": {"type": "string"},
                                    "measurement10": {"type": "string"},
                                    "measurement11": {"type": "string"},
                                    "measurement12": {"type": "string"},
                                    "measurement13": {"type": "string"},
                                    "measurement14": {"type": "string"},
                                    "measurement15": {"type": "string"},
                                    "measurement16": {"type": "string"},
                                    "reason": {"type": "string"},
                                },
                                "required": [
                                    "original_comment",
                                    "measurement1",
                                    "measurement2",
                                    "measurement3",
                                    "measurement4",
                                    "measurement5",
                                    "measurement6",
                                    "measurement7",
                                    "measurement8",
                                    "measurement9",
                                    "measurement10",
                                    "measurement11",
                                    "measurement12",
                                    "measurement13",
                                    "measurement14",
                                    "measurement15",
                                    "measurement16",
                                    "reason",
                                ],
                                "additionalProperties": False,
                            },
                        }
                    },
                },
            },
        },
    )

    result = response.choices[0].message.content  # 取出回應內容

    # 解析 JSON
    try:
        print(result + "\n")
        return json.loads(result)
    except json.JSONDecodeError:
        print("❌ JSON 解析錯誤")
        return None


def batch(iterable, n=10):
    """將可迭代對象拆分為大小為 n 的批次"""
    for i in range(0, len(iterable), n):
        yield iterable[i : i + n]


# 主函數
def main():
    comments_file = input("請輸入評論 JSON 檔案路徑： ")
    comments = load_comments(comments_file)
    all_scores = []

    for batch_comments in batch(comments, 20):
        scores = get_scores(batch_comments)
        all_scores.extend(scores["scores"])
        print(f"🔄 目前累積評論：{len(all_scores)}, 正在處理下一批評論...")

    output_file = f"{comments_file.replace('.json', '')}_SAAS_scores.json"
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(all_scores, json_file, ensure_ascii=False, indent=4)

    print(f"✅ 評分已成功儲存至 {output_file}")


if __name__ == "__main__":
    main()
