import requests
import json
import re

def fetch_jagobd_api_channels():
    # JagoBD এর রিয়েল-টাইম এপিআই বা চ্যানেল সার্ভার লিংকসমূহ
    base_url = "https://www.jagobd.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.jagobd.com/",
        "Accept": "*/*"
    }

    print("🔄 JagoBD এপিআই ও সার্ভার থেকে চ্যানেল ডাটা ফেচ করা হচ্ছে...")

    channels = []
    m3u_lines = ["#EXTM3U\n"]

    try:
        # ১. হোমপেজের ডাটা সার্ভিস লোড করা
        res = requests.get(base_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"❌ JagoBD Server response code: {res.status_code}")
            return

        # HTML থেকে চ্যানেলের ইউনিক লিংক এবং লোগো আইডেন্টিফাই করা
        html = res.text
        # চ্যানেল লিঙ্ক এবং ইমেজ এক্সট্র্যাক্ট
        pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>\s*<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']+)["\']'
        matches = re.findall(pattern, html, re.IGNORECASE)

        seen_channels = set()

        for page_link, logo, name in matches:
            name = name.strip()
            if not name or name in seen_channels:
                continue

            # ইউআরএল ফরম্যাটিং
            if not page_link.startswith("http"):
                page_link = f"{base_url}/{page_link.lstrip('/')}"
            
            if not logo.startswith("http"):
                logo = f"{base_url}/{logo.lstrip('/')}"

            seen_channels.add(name)

            # ২. ব্যাকএন্ড স্ট্রিম এপিআই সমাধান (JagoBD Dynamic Streaming Token URL Generate)
            stream_url = ""
            try:
                ch_res = requests.get(page_link, headers=headers, timeout=6)
                if ch_res.status_code == 200:
                    # iframe বা m3u8 স্ট্রিম লিংকের রেসপন্স সন্ধান
                    iframe_match = re.search(r'iframe[^>]+src=["\']([^"\']+)["\']', ch_res.text, re.IGNORECASE)
                    m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', ch_res.text, re.IGNORECASE)
                    
                    if m3u8_match:
                        stream_url = m3u8_match.group(1)
                    elif iframe_match:
                        stream_url = iframe_match.group(1)
                        if not stream_url.startswith("http"):
                            stream_url = f"{base_url}/{stream_url.lstrip('/')}"
                    else:
                        stream_url = page_link
            except Exception:
                stream_url = page_link

            # চ্যানেল ডাটা অবজেক্ট
            ch_data = {
                "name": name,
                "logo": logo,
                "stream_url": stream_url,
                "page_url": page_link
            }
            channels.append(ch_data)

            # M3U ফরম্যাটিং
            m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="JagoBD API",{name}\n{stream_url}\n')

    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return

    # ১. playlist.json ফাইলে সমস্ত এপিআই ডাটা সেভ
    json_output = {
        "status": "success",
        "provider": "JagoBD API Service",
        "total_channels": len(channels),
        "data": channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_output, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json আপডেট হয়েছে (মোট ডাটা: {len(channels)})")

    # ২. playlist.m3u ফাইলে সেভ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u ফাইল আপডেট হয়েছে")

if __name__ == "__main__":
    fetch_jagobd_api_channels()
