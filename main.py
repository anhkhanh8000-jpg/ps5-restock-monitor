import os
import time
import requests
from datetime import datetime

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

PRODUCTS = {
    "PS5 Pro bản thường": os.getenv("PS5_PRO_URL"),
    "PS5 Pro 30th Anniversary": os.getenv("PS5_30TH_URL"),
}

CHECK_INTERVAL = 300  # 5 phút

headers = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
        "Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
}

last_status = {}


def send_discord(message):
    if not DISCORD_WEBHOOK:
        print("Chưa cấu hình Discord Webhook!")
        return

    try:
        r = requests.post(
            DISCORD_WEBHOOK,
            json={"content": message},
            timeout=20
        )
        r.raise_for_status()
    except Exception as e:
        print("Discord error:", e)


def check_amazon(name, url):
    if not url:
        print(f"{name}: chưa cấu hình link")
        return None

    try:
        r = requests.get(url, headers=headers, timeout=30)
        html = r.text.lower()

        if r.status_code != 200:
            print(name, "HTTP", r.status_code)
            return None

        # Các dấu hiệu hết hàng
        unavailable = [
            "currently unavailable",
            "currently out of stock",
            "在庫切れ",
            "現在在庫切れです",
            "入荷予定はありません",
        ]

        # Các dấu hiệu có hàng
        available = [
            "カートに入れる",
            "今すぐ買う",
            "add to cart",
            "buy now",
        ]

        if any(word.lower() in html for word in unavailable):
            return False

        if any(word.lower() in html for word in available):
            return True

        return None

    except Exception as e:
        print(f"Error checking {name}: {e}")
        return None


def monitor():
    print("PS5 Restock Monitor started!")

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\nChecking at {now}")

        for name, url in PRODUCTS.items():
            if not url:
                continue

            status = check_amazon(name, url)

            if status is None:
                print(name, "Không xác định được trạng thái")
                continue

            print(name, "CÓ HÀNG" if status else "HẾT HÀNG")

            previous = last_status.get(name)

            # Chỉ báo khi chuyển từ hết hàng sang có hàng
            if status is True and previous is not True:
                message = (
                    f"🚨 **PS5 RESTOCK ALERT!**\n"
                    f"🎮 Sản phẩm: {name}\n"
                    f"🟢 Có dấu hiệu đặt mua được!\n"
                    f"🔗 {url}"
                )
                send_discord(message)

            last_status[name] = status

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor()
