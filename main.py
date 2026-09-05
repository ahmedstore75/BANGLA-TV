import requests
import json
import re

def fetch_live_channels_api():
    # IPTV-Org এর বর্তমানে সচল বাংলা চ্যানেলের অফিশিয়াল M3U প্লেলিস্ট URL
    m3u_url = "https://iptv-org.github.io/iptv/languages/ben.m3u"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 এপিআই/অনলাইন প্লেলিস্ট থেকে সরাসরি লাইভ চ্যানেল ডাটা লোড করা হচ্ছে...")

    try:
        response = requests.get(m3u_url, headers=headers, timeout=15)
        response.raise_for_status()
        raw_data = response.text
    except Exception as e:
        print(f"❌ এপিআই থেকে ডাটা আনতে ব্যর্থ হয়েছে: {e}")
        return

    processed_channels = []
    m3u_lines = ["#EXTM3U\n"]

    # M3U ফাইলের প্রতিটি লাইন পার্স করা
    lines = raw_data.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            info_line = line
            # পরবর্তী লাইনে থাকা স্ট্রিম URL নেওয়া
            stream_url = ""
            if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                stream_url = lines[i + 1].strip()
                i += 1

            # চ্যানেলের নাম বের করা (কমা-র পর যা থাকে)
            name = info_line.split(",")[-1].strip() if "," in info_line else "Unknown Channel"

            # লোগো ইউআরএল বের করা
            logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
            logo = logo_match.group(1) if logo_match else ""

            # ক্যাটাগরি বা গ্রুপ বের করা
            group_match = re.search(r'group-title="([^"]*)"', info_line)
            category = group_match.group(1) if group_match else "Bangla TV"

            if name and stream_url:
                channel_obj = {
                    "name": name,
                    "logo": logo,
                    "category": category,
                    "stream_url": stream_url
                }
                processed_channels.append(channel_obj)

                # M3U লাইনে যোগ করা
                m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{category}",{name}\n{stream_url}\n')
        i += 1

    # ১. playlist.json ফাইলে সেভ
    json_data = {
        "status": "success",
        "total_channels": len(processed_channels),
        "channels": processed_channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json আপডেট হয়েছে (মোট ডাটা: {len(processed_channels)})")

    # ২. playlist.m3u ফাইলে সেভ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u সফলভাবে লোগো ও ভিডিও লিংক সহ সেভ হয়েছে")

if __name__ == "__main__":
    fetch_live_channels_api()
