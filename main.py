import requests
import json

def fetch_live_channels_api():
    # IPTV-Org এর অফিশিয়াল বাংলা চ্যানেল ডাটা API
    api_url = "https://iptv-org.github.io/iptv/languages/ben.json"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 এপিআই থেকে সরাসরি লাইভ চ্যানেল ডাটা লোড করা হচ্ছে...")

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        raw_channels = response.json()
    except Exception as e:
        print(f"❌ এপিআই থেকে ডাটা আনতে ব্যর্থ হয়েছে: {e}")
        return

    processed_channels = []
    m3u_lines = ["#EXTM3U\n"]

    # এপিআই এর ভেতরে থাকা চ্যানেল, লোগো এবং স্ট্রিম লিংক পার্স করা
    for item in raw_channels:
        name = item.get("name", "").strip()
        stream_url = item.get("url", "").strip()
        logo = item.get("logo", "").strip()
        category = item.get("category", "Bangla TV").strip()

        # শুধুমাত্র যেসব লিংকে ভিডিও স্ট্রিম আছে সেগুলো যুক্ত হবে
        if name and stream_url:
            channel_obj = {
                "name": name,
                "logo": logo,
                "category": category,
                "stream_url": stream_url
            }
            processed_channels.append(channel_obj)

            # M3U৮ প্লেলিস্টের জন্য লোগো ও লিঙ্ক ফরম্যাটিং
            m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{category}",{name}\n{stream_url}\n')

    # ১. playlist.json ফাইলে সম্পূর্ণ এপিআই ডাটা সেভ
    json_data = {
        "status": "success",
        "total_channels": len(processed_channels),
        "channels": processed_channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json আপডেট হয়েছে (মোট ডাটা: {len(processed_channels)})")

    # ২. playlist.m3u ফাইলে প্লেলিস্ট সেভ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u সফলভাবে লোগো ও ভিডিও লিংক সহ সেভ হয়েছে")

if __name__ == "__main__":
    fetch_live_channels_api()
