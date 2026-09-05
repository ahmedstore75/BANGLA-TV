import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_jagobd():
    url = "https://www.jagobd.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 JagoBD ওয়েবসাইট থেকে টিভি চ্যানেলের তথ্য লোড করা হচ্ছে...")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"❌ JagoBD পেজ লোড করতে ব্যর্থ হয়েছে: {e}")
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    
    channels = []
    m3u_lines = ["#EXTM3U\n"]

    # JagoBD ওয়েবসাইটের চ্যানেল গ্রিড পার্স করা
    # ওয়েবসাইটের 'a' ট্যাগ যেখানে চ্যানেলের লিংক এবং 'img' লোগো থাকে
    links = soup.find_all('a', href=True)

    for link in links:
        href = link['href']
        img = link.find('img')

        # যেসব লিংকে টিভি চ্যানেল আছে
        if img and ('/channel/' in href or '.html' in href or 'jagobd.com' in href):
            name = img.get('alt') or img.get('title') or link.text.strip()
            logo = img.get('src') or img.get('data-src') or ""

            # রিলেটিভ URL হলে Absolute URL বানানো
            if href.startswith('/'):
                channel_page_url = f"https://www.jagobd.com{href}"
            elif not href.startswith('http'):
                channel_page_url = f"https://www.jagobd.com/{href}"
            else:
                channel_page_url = href

            if logo and not logo.startswith('http'):
                logo = f"https://www.jagobd.com{logo}" if logo.startswith('/') else f"https://www.jagobd.com/{logo}"

            if name and len(name) > 2:
                # ডুপ্লিকেট চ্যানেল বাদ দেওয়া
                if not any(c['name'] == name for c in channels):
                    channels.append({
                        "name": name,
                        "logo": logo,
                        "page_url": channel_page_url
                    })

                    # M3U৮ লাইনে যোগ করা
                    m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="JagoBD Live",{name}\n{channel_page_url}\n')

    # ১. playlist.json ফাইলে সম্পূর্ণ চ্যানেল ডাটা সেভ
    json_data = {
        "source": "https://www.jagobd.com/",
        "total_channels": len(channels),
        "channels": channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json আপডেট হয়েছে (মোট চ্যানেল: {len(channels)})")

    # ২. playlist.m3u ফাইলে সব চ্যানেলের লোগো ও লিঙ্ক সেভ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print(f"✅ playlist.m3u আপডেট হয়েছে")

if __name__ == "__main__":
    scrape_jagobd()
