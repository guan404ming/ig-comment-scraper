import requests
import json
import time

# 全局變數
CSRFTOKEN = "YOUR_CSRFTOKEN"
SESSION_ID = "YOUR_SESSION_ID"
DS_USER_ID = "YOUR_DS_USER_ID"
HEADERS = {
    "Origin": "https://www.instagram.com",
    "Cookie": f'csrftoken={CSRFTOKEN}; sessionid={SESSION_ID}; ds_user_id={DS_USER_ID};',
    "Content-Type": "application/x-www-form-urlencoded",
}
RAPID_API_KEY = "YOUR_RAPID_API_KEY"

# 貼文相關全域變數
all_comments = []
media_id = ""
code = ""


def get_media_id():
    global media_id, code
    input_url = input("請輸入網址： ")
    url = "https://instagram-scraper-api2.p.rapidapi.com/v1/post_info"
    querystring = {"code_or_id_or_url": input_url, "include_insights": "true"}

    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    media_id = response.json()["data"]["id"].split("_")[0]
    code = response.json()["data"]["code"]

    return


def fetch_comments(parent_comment_id=None, end_cursor=None):
    """
    發送 API 請求，獲取 IG 留言（含子留言）
    """
    url = "https://www.instagram.com/graphql/query"

    # 設定 doc_id (主留言 vs. 子留言)
    doc_id = 7823865067713647 if parent_comment_id is None else 26661277556852035

    # 組裝 API 變數
    variables = {
        "after": end_cursor,
        "before": None,
        "first": 10,
        "last": None,
        "media_id": media_id,
        "sort_order": "popular",
        "__relay_internal__pv__PolarisIsLoggedInrelayprovider": True,
    }

    # 若是子留言請求，調整參數
    if parent_comment_id:
        variables = {
            "after": None,
            "before": None,
            "media_id": media_id,
            "parent_comment_id": parent_comment_id,
            "is_chronological": None,
            "first": None,
            "last": None,
            "sort_order":"popular",
            "__relay_internal__pv__PolarisIsLoggedInrelayprovider": True,
        }

    # 發送請求
    payload = f"doc_id={doc_id}&variables={json.dumps(variables)}"
    response = requests.post(url, headers=HEADERS, data=payload)

    # 檢查請求是否成功
    if response.status_code != 200:
        print(f"⚠️ API 請求失敗，狀態碼: {response.status_code}")
        return None
    
    print(f'{"[PARENT]" if not parent_comment_id else "    [CHILD]"} Fetch with: {variables}')

    return response.json()


def process_comments(data, parent_comment_id=None):
    """
    處理 API 回應的留言數據，解析留言並獲取子留言
    """
    global all_comments

    # 檢查資料是否有效
    key = (
        "xdt_api__v1__media__media_id__comments__connection"
        if parent_comment_id is None
        else "xdt_api__v1__media__media_id__comments__parent_comment_id__child_comments__connection"
    )

    comments_data = data.get("data", {}).get(key, {})

    if not comments_data:
        print("⚠️ API 回應格式異常，無法解析")
        return None

    # 取得留言列表
    comments = comments_data.get("edges", [])
    for comment in comments:
        all_comments.append(comment)  # 儲存留言
        
        print(f"🔍 當前留言數量：{len(all_comments)}")

        # 檢查是否有子留言
        if comment["node"]["child_comment_count"] and comment["node"]["child_comment_count"] > 0:
            print(f'🔍 發現 {comment["node"].get("child_comment_count", None)} 則子留言，開始擷取...')
            get_comments(parent_comment_id=comment["node"]["pk"])

    # 分頁處理
    page_info = comments_data.get("page_info", {})
    has_next_page = page_info.get("has_next_page", False)
    end_cursor = None

    if page_info.get("end_cursor"):
        try:
            end_cursor = page_info["end_cursor"]
        except json.JSONDecodeError:
            pass

    print(f'{"[PARENT]" if not parent_comment_id else "    [CHILD]"} Res: {page_info}')

    return has_next_page, end_cursor


def get_comments(parent_comment_id=None):
    """
    主函數：遞迴獲取所有留言（含子留言）
    """
    end_cursor = None

    while True:
        data = fetch_comments(parent_comment_id, end_cursor)

        if not data:
            break

        has_next_page, end_cursor = process_comments(
            data, parent_comment_id
        )

        with open(f"{code}.json", "w", encoding="utf-8") as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=4)

        if not has_next_page:
            print("🚀 沒有更多留言，結束請求")
            break

        time.sleep(2)  # 避免請求過於頻繁


def print_comment(comment):
    """
    格式化輸出留言
    """
    user = comment["node"]["user"]["username"]
    text = comment["node"]["text"]
    likes = comment["node"]["comment_like_count"]
    print(f"👤 {user}: {text} ❤️ {likes} likes")


# 執行程式
get_media_id()
get_comments()

for comment in all_comments:
    print_comment(comment)
