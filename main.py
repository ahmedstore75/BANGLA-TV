import requests
import json

def fetch_and_parse_tapmad():
    api_url = "https://backend-api.tapmad.com/api/getMobileAppSettings/V1/en/web"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        res_data = response.json()
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        res_data = {}

    # ১. সম্পূর্ণ API রেসপন্স JSON ফাইলে সেভ
    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(res_data, jf, indent=4, ensure_ascii=False)
    print("✅ playlist.json সফলভাবে আপডেট হয়েছে")

    # ২. M3U৮ প্লেলিস্ট তৈরি (API Structure পার্স করা)
    m3u_lines = ["#EXTM3U\n"]
    items_found = 0

    # নেস্টেড JSON থেকে মিডিয়া বা চ্যানেল ডেটা এক্সট্র্যাক্ট করা
    def extract_items(data):
        nonlocal items_found
        if isinstance(data, dict):
            # চ্যানেল বা মিডিয়া আইটেম চেক
            name = data.get("title") or data.get("name") or data.get("channel_name")
            stream_url = data.get("stream_url") or data.get("video_url") or data.get("url") or data.get("hls_url")
            logo = data.get("logo") or data.get("image") or data.get("thumbnail") or ""

            if name and stream_url and isinstance(stream_url, str) and stream_url.startswith("http"):
                m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo}",{name}\n{stream_url}\n')
                items_found += 1

            for key, val in data.items():
                extract_items(val)

        elif isinstance(data, list):
            for item in data:
                extract_items(item)

    # API থেকে স্ট্রিম ডেটা খোঁজা
    extract_items(res_data)

    # যদি স্ট্রিম লিংক না থাকে, তবে এপিআই এর অন্তর্গত অন্যান্য গুরুত্বপূর্ণ ইউআরএল যুক্ত করবে
    if items_found == 0:
        m3u_lines.append('#EXTINF:-1 group-title="Base API",Tapmad Settings API\nhttps://backend-api.tapmad.com/api/getMobileAppSettings/V1/en/web\n')

    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print(f"✅ playlist.m3u আপডেট হয়েছে (মোট আইটেম: {items_found})")

if __name__ == "__main__":
    fetch_and_parse_tapmad()
