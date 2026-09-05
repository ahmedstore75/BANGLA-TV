import requests
import json
import re

def fetch_and_generate_playlists():
    # Tapmad এর মূল API Endpoints
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
        print(f"❌ API Request Error: {e}")
        res_data = {}

    # ১. সম্পূর্ণ API রেজাল্ট JSON ফাইলে সেভ
    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(res_data, jf, indent=4, ensure_ascii=False)
    print("✅ playlist.json আপডেট হয়েছে")

    # ২. API এর ভেতর থাকা সমস্ত URL (ছবি, ব্যানার, ক্যাটাগরি, স্ট্রিম) এক্সট্র্যাক্ট করা
    m3u_lines = ["#EXTM3U\n"]
    extracted_urls = set()

    # JSON টেক্সট থেকে সব HTTP/HTTPS লিঙ্ক খুঁজে বের করা
    json_str = json.dumps(res_data)
    urls = re.findall(r'https?://[^\s"\'<>]+', json_str)

    count = 1
    for url in urls:
        # ব্যাকস্ল্যাশ ক্লিন করা
        clean_url = url.replace("\\", "")
        
        if clean_url not in extracted_urls:
            extracted_urls.add(clean_url)
            
            # ফাইলের ধরন বা নাম নির্ধারণ
            if ".jpg" in clean_url or ".png" in clean_url or ".webp" in clean_url:
                title = f"Media/Banner Image {count}"
                group = "Images"
            elif ".m3u8" in clean_url or ".mp4" in clean_url:
                title = f"Live Stream {count}"
                group = "Streams"
            else:
                title = f"API Resource {count}"
                group = "API"

            m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{title}\n{clean_url}\n')
            count += 1

    # ৩. M3U ফাইল সেভ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print(f"✅ playlist.m3u আপডেট হয়েছে (মোট লিঙ্ক: {len(extracted_urls)})")

if __name__ == "__main__":
    fetch_and_generate_playlists()
