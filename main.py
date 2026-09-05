import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_jagobd_full():
    base_url = "https://www.jagobd.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 JagoBD হোমপেজ থেকে চ্যানেলের তালিকা লোড করা হচ্ছে...")

    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"❌ JagoBD পেজ লোড করতে ব্যর্থ হয়েছে: {e}")
        return

    channels = []
    m3u_lines = ["#EXTM3U\n"]
    seen_names = set()

    # হোমপেজের চ্যানেল গ্রিড থেকে লিংক ও ছবি বের করা
    links = soup.find_all('a', href=True)

    for link in links:
        href = link['href']
        img = link.find('img')

        # যেসব লিংকে টিভি চ্যানেল আছে
        if img and ('/channel/' in href or '.html' in href or 'jagobd.com' in href):
            name = img.get('alt') or img.get('title') or link.text.strip()
            logo = img.get('src') or img.get('data-src') or ""

            if not name or len(name) < 2 or name in seen_names:
                continue

            # URL এবং Logo Format ঠিক করা
            if href.startswith('/'):
                channel_page_url = f"{base_url}{href}"
            elif not href.startswith('http'):
                channel_page_url = f"{base_url}/{href}"
            else:
                channel_page_url = href

            if logo and not logo.startswith('http'):
                logo = f"{base_url}{logo}" if logo.startswith('/') else f"{base_url}/{logo}"

            seen_names.add(name)

            # চ্যানেলের পেজ থেকে ভিডিও প্লেয়ার লিংক/iframe বের করা
            stream_link = channel_page_url
            try:
                ch_res = requests.get(channel_page_url, headers=headers, timeout=5)
                if ch_res.status_code == 200:
                    ch_soup = BeautifulSoup(ch_res.text, 'html.parser')
                    iframe = ch_soup.find('iframe', src=True)
                    if iframe:
                        iframe_src = iframe['src']
                        if iframe_src.startswith('http'):
                            stream_link = iframe_src
                        elif iframe_src.startswith('/'):
                            stream_link = f"{base_url}{iframe_src}"
            except Exception:
                pass # টাইমাউট হলে মূল পেজ লিঙ্কই ব্যবহার হবে

            channel_entry = {
                "name": name,
                "logo": logo,
                "stream_url": stream_link,
                "page_url": channel_page_url
            }
            channels.append(channel_entry)

            # M3U৮ ফরম্যাটে চ্যানেল লোগো ও স্ট্রিম লিঙ্ক যোগ করা
            m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="JagoBD Live",{name}\n{stream_link}\n')

    # ১. playlist.json ফাইল সেভ
    json_output = {
        "status": "success",
        "source": base_url,
        "total_channels": len(channels),
        "channels": channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_output, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json আপডেট হয়েছে (মোট চ্যানেল: {len(channels)})")

    # ২. playlist.m3u ফাইল সেভ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u লোগো সহ সেভ হয়েছে")

if __name__ == "__main__":
    scrape_jagobd_full()
