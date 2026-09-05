import requests
import json
import re

def clean_channel_name(name):
    # ব্র্যাকেট (), [], {} এবং ভেতরের লেখা মুছে ফেলা
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def get_channel_priority(channel):
    name = channel['name'].lower()
    category = channel['category'].lower()

    # ১. বাংলাদেশী চ্যানেল (কঠোরভাবে সবার উপরে থাকবে)
    bd_keywords = [
        'btv', 'somoy', 'channel i', 'ekattor', 'jamuna', 'rtv', 'atn', 'ntv', 
        'independent', 'bangla vision', 'dbc', 'deepto', 'asian tv', 'desh tv', 
        'nagorik', 'boishakhi', 'maasranga', 'bijoy', 'gtv', 'gazitv', 'bangladesh',
        'duronto', 'saatv', 'sangeet bangla', 'news24', 'channel 24'
    ]
    if any(k in name for k in bd_keywords) or 'bangladesh' in category:
        return 1

    # ২. স্পোর্টস চ্যানেল
    sports_keywords = ['sport', 'sports', 't sports', 'tsports', 'star sports', 'sony ten', 'willow', 'ptv sports', 'astro', 'cricket', 'football', 'eurosport', 'ten sports']
    if any(k in name for k in sports_keywords) or 'sports' in category:
        return 2

    # ৩. কলকাতা বাংলা চ্যানেল
    kolkata_keywords = ['star jalsha', 'zee bangla', 'colors bangla', 'sony aath', 'rupashi bangla', 'sangeet bangla', 'news18 bangla', 'tv9 bangla', 'khabor 365', 'calcutta', 'kolkata']
    if any(k in name for k in kolkata_keywords):
        return 3

    # ৪. ইন্ডিয়ান টিভি চ্যানেল
    indian_keywords = ['zee', 'star', 'sony', 'colors', 'aaj tak', 'ndtv', 'india', 'sab', 'bindass', 'pogo', 'hungama', 'discovery india']
    if any(k in name for k in indian_keywords) or 'india' in category:
        return 4

    # ৫. অন্যান্য আন্তর্জাতিক চ্যানেল
    return 5

def fetch_multi_source_channels():
    # চ্যানেল সংখ্যা বাড়াতে একাধিক ফ্রি এপিআই / প্লেলিস্ট সোর্স
    sources = [
        "https://iptv-org.github.io/iptv/languages/ben.m3u", # বাংলা চ্যানেল সোর্স
        "https://iptv-org.github.io/iptv/index.m3u"          # গ্লোবাল ফ্রি চ্যানেল সোর্স (চ্যানেল সংখ্যা বাড়াবে)
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 একাধিক এপিআই সোর্স থেকে ডাটা ফেচ করা হচ্ছে...")

    channels = []
    seen_urls = set()  # ইউনিক স্ট্রিমিং লিঙ্ক রাখার জন্য

    for url in sources:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                continue
            raw_data = response.text
        except Exception:
            continue

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

                # ডুপ্লিকেট লিঙ্ক ফিল্টারিং
                if stream_url and stream_url not in seen_urls:
                    raw_name = info_line.split(",")[-1].strip() if "," in info_line else "Unknown Channel"
                    clean_name = clean_channel_name(raw_name)

                    logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                    logo = logo_match.group(1) if logo_match else ""

                    group_match = re.search(r'group-title="([^"]*)"', info_line)
                    category = group_match.group(1) if group_match else "General"

                    # শুধু বাংলা, স্পোর্টস ও প্রিমিয়াম ক্যাটাগরির সাথে ম্যাচ হলে নিবে (যাতে অপ্রয়োজনীয় বিদেশী চ্যানেল বেশি না জমে)
                    ch_obj = {
                        "name": clean_name,
                        "logo": logo,
                        "category": category,
                        "stream_url": stream_url
                    }
                    
                    priority = get_channel_priority(ch_obj)
                    
                    # প্রথম ৫ প্রকার ক্যাটাগরির যেকোনো একটিতে পড়লে তা প্লেলিস্টে যোগ হবে
                    if priority <= 4 or "ben" in url:
                        channels.append(ch_obj)
                        seen_urls.add(stream_url)
            i += 1

    # সিরিয়াল অনুযায়ী সুনির্দিষ্ট সর্টিং (BD -> Sports -> Kolkata -> India -> Others)
    channels.sort(key=get_channel_priority)

    # M3U ফরম্যাটিং
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
    print(f"✅ playlist.json আপডেট করা হয়েছে (মোট চ্যানেল: {len(channels)})")

    # ২. playlist.m3u সেভ করা
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u আপডেট করা হয়েছে")

if __name__ == "__main__":
    fetch_multi_source_channels()
