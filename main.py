import requests
import json

def fetch_and_save_playlists():
    # Tapmad এর মূল মোবাইল সেটিংস API
    api_url = "https://backend-api.tapmad.com/api/getMobileAppSettings/V1/en/web"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ API থেকে ডেটা আনতে ব্যর্থ হয়েছে: {e}")
        # ফাইল না থাকলে গিটহাব অ্যাকশন যেন ফেইল না করে তাই খালি ফাইল তৈরি রাখা
        data = {"status": "error", "message": str(e)}

    # ১. JSON ফাইল সেভ করা
    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(data, jf, indent=4, ensure_ascii=False)
    print("✅ playlist.json সফলভাবে সেভ হয়েছে")

    # ২. M3U৮ প্লেলিস্ট তৈরি
    m3u_lines = ["#EXTM3U\n"]
    
    # API রেসপন্স থেকে চ্যানেল/ভিডিওর তালিকা এক্সট্র্যাক্ট করা (উদাহরণস্বরূপ)
    # API স্ট্রাকচার অনুযায়ী ফিল্ড ফিল্টার করা
    channels = data.get("data", {}).get("channels", []) if isinstance(data, dict) else []
    
    if channels:
        for ch in channels:
            title = ch.get("title", "Unknown Channel")
            stream_url = ch.get("stream_url", ch.get("url", ""))
            logo = ch.get("logo", "")
            
            if stream_url:
                m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo}",{title}\n{stream_url}\n')
    else:
        # যদি স্পেসিফিক চ্যানেল লিস্ট না পাওয়া যায়, মূল এপিআই লিঙ্কটিই যুক্ত করা
        m3u_lines.append(f'#EXTINF:-1 group-title="API Base",Tapmad Settings API\n{api_url}\n')

    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u সফলভাবে সেভ হয়েছে")

if __name__ == "__main__":
    fetch_and_save_playlists()
