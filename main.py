import requests
import json
import re

def clean_channel_name(name):
    # ফার্স্ট ব্র্যাকেট (), থার্ড ব্র্যাকেট [] এবং তাদের ভেতরের সব লেখা মুছে ফেলা
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def get_channel_priority(channel):
    name = channel['name'].lower()
    category = channel['category'].lower()
    url = channel['stream_url'].lower()

    # ১. বাংলাদেশী চ্যানেল
    bd_keywords = ['btv', 'somoy', 'channel i', 'ekattor', 'jamuna', 'rtv', 'atn', 'ntv', 'independent', 'bangla vision', 'dbc', 'deepto', 'asian tv', 'desh tv', 'nagorik', 'boishakhi', 'maasranga', 'bijoy', 'gtv', 'gazitv', 'bangladesh']
    if any(k in name for k in bd_keywords) or 'bangladesh' in category:
        return 1

    # ২. স্পোর্টস চ্যানেল
    sports_keywords = ['sport', 'sports', 't sports', 'tsports', 'star sports', 'sony ten', 'willow', 'ptv sports', 'astro', 'cricket', 'football', 'eurosport']
    if any(k in name for k in sports_keywords) or 'sports' in category:
        return 2

    # ৩. কলকাতা বাংলা চ্যানেল
    kolkata_keywords = ['star jalsha', 'zee bangla', 'colors bangla', 'sony aath', 'rupashi bangla', 'sangeet bangla', 'news18 bangla', 'tv9 bangla', 'khabor 365', 'calcutta', 'kolkata']
    if any(k in name for k in kolkata_keywords):
        return 3

    # ৪. ইন্ডিয়ান চ্যানেল
    indian_keywords = ['zee', 'star', 'sony', 'colors', 'aaj tak', 'ndtv', 'india', 'sab', 'bindass', 'pogo', 'hungama', 'discovery india']
    if any(k in name for k in indian_keywords) or 'india' in category:
        return 4

    # ৫. অন্যান্য চ্যানেল
    return 5

def fetch_and_organize_channels():
    m3u_url = "https://iptv-org.github.io/iptv/languages/ben.m3u"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 চ্যানেল ডাটা ফেচ ও ফিল্টার করা হচ্ছে...")

    try:
        response = requests.get(m3u_url, headers=headers, timeout=15)
        response.raise_for_status()
        raw_data = response.text
    except Exception as e:
        print(f"❌ ডাটা আনতে সমস্যা হয়েছে: {e}")
        return

    channels = []
    seen_urls = set()  # ডুপ্লিকেট লিঙ্ক ফিল্টার করার জন্য

    lines = raw_data.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            info_line = line
            stream_url = ""
            if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                stream_url = lines[i + 1].strip()
                i += 1

            # ডুপ্লিকেট ইউআরএল চেক (এক স্ট্রিমিং লিঙ্ক একবারই যুক্ত হবে)
            if stream_url and stream_url not in seen_urls:
                raw_name = info_line.split(",")[-1].strip() if "," in info_line else "Unknown Channel"
                clean_name = clean_channel_name(raw_name)

                logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                logo = logo_match.group(1) if logo_match else ""

                group_match = re.search(r'group-title="([^"]*)"', info_line)
                category = group_match.group(1) if group_match else "General"

                if clean_name:
                    channels.append({
                        "name": clean_name,
                        "logo": logo,
                        "category": category,
                        "stream_url": stream_url
                    })
                    seen_urls.add(stream_url)
        i += 1

    # সিরিয়াল অনুযায়ী সর্টিং/অর্ডার করা (BD -> Sports -> Kolkata -> India -> Others)
    channels.sort(key=get_channel_priority)

    # M3U লাইন জেনারেট করা
    m3u_lines = ["#EXTM3U\n"]
    for ch in channels:
        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["category"]}",{ch["name"]}\n{ch["stream_url"]}\n')

    # ১. playlist.json সেভ করা
    json_data = {
        "status": "success",
        "total_channels": len(channels),
        "channels": channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json ফিল্টার করে সাজানো হয়েছে (মোট চ্যানেল: {len(channels)})")

    # ২. playlist.m3u সেভ করা
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u সাজানো সিরিয়াল অনুযায়ী সেভ হয়েছে")

if __name__ == "__main__":
    fetch_and_organize_channels()
