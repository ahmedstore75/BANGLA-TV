import requests
import json
import re

def clean_channel_name(name):
    # ব্র্যাকেট (), [], {} এবং ভেতরের নাম মুছে পরিষ্কার নাম তৈরি করা
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def is_telugu_channel(channel):
    name = channel['name'].lower()
    category = channel['category'].lower()
    
    # তেলেগু চ্যানেল চেনার জন্য নির্দিষ্ট কিউয়ার্ড (ব্লকলিস্ট)
    telugu_keywords = [
        'telugu', 'gemini tv', 'gemini movies', 'gemini music', 'gemini comedy',
        'etv telugu', 'etv plus', 'etv cinema', 'etv life', 'etv abhirami',
        'sakshi', 'v6 news', 'tv9 telugu', 'nTV telugu', 't news', '10tv',
        'abn andhra jyothi', 'bhakthi tv', 'svbc', 'raj news telugu', 'mahaa news',
        'hMTV', 'prime9 news', 'studio n', 'cvr news', 'tollywood'
    ]

    # যদি ক্যাটাগরি বা নামের মধ্যে তেলেগু চিহ্নিত হয়
    if 'telugu' in category or any(k in name for k in telugu_keywords):
        return True
    return False

def get_channel_priority(channel):
    name = channel['name'].lower()
    category = channel['category'].lower()

    # ১. বাংলাদেশী চ্যানেল (সবার উপরে)
    bd_keywords = [
        'btv', 'somoy', 'channel i', 'ekattor', 'jamuna', 'rtv', 'atn', 'ntv', 
        'independent', 'bangla vision', 'dbc', 'deepto', 'asian tv', 'desh tv', 
        'nagorik', 'boishakhi', 'maasranga', 'bijoy', 'gtv', 'gazitv', 'bangladesh',
        'duronto', 'saatv', 'sangeet bangla', 'news24', 'channel 24', 'mohana', 'channel9'
    ]
    if any(k in name for k in bd_keywords) or 'bangladesh' in category:
        return 1

    # ২. স্পোর্টস চ্যানেল
    sports_keywords = ['sport', 'sports', 't sports', 'tsports', 'star sports', 'sony ten', 'willow', 'ptv sports', 'ten sports', 'geo super', 'cric']
    if any(k in name for k in sports_keywords) or 'sports' in category:
        return 2

    # ৩. কলকাতা বাংলা চ্যানেল
    kolkata_keywords = ['star jalsha', 'zee bangla', 'colors bangla', 'sony aath', 'rupashi bangla', 'sangeet bangla', 'news18 bangla', 'tv9 bangla', 'khabor 365', 'calcutta', 'kolkata']
    if any(k in name for k in kolkata_keywords):
        return 3

    # ৪. ইন্ডিয়ান টিভি চ্যানেল
    indian_keywords = ['zee', 'star', 'sony', 'colors', 'aaj tak', 'ndtv', 'india', 'sab', 'bindass', 'pogo', 'hungama', 'discovery', 'sun tv']
    if any(k in name for k in indian_keywords) or 'india' in category:
        return 4

    # ৫. পাকিস্তানি চ্যানেল
    pak_keywords = ['geo', 'ary', 'hum', 'ptv', 'express', 'dunya', 'samaa', 'bol', 'a-plus', 'pakistan']
    if any(k in name for k in pak_keywords) or 'pakistan' in category:
        return 5

    return 6

def fetch_channels_without_telugu():
    # চ্যানেল সোর্সসমূহ
    sources = [
        "https://iptv-org.github.io/iptv/languages/ben.m3u",
        "https://iptv-org.github.io/iptv/countries/bd.m3u",
        "https://iptv-org.github.io/iptv/countries/in.m3u",
        "https://iptv-org.github.io/iptv/countries/pk.m3u"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 তেলেগু চ্যানেল ফিল্টার করে বাকি ডাটা লোড করা হচ্ছে...")

    channels = []
    seen_urls = set()

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

                if stream_url and stream_url not in seen_urls:
                    raw_name = info_line.split(",")[-1].strip() if "," in info_line else "Unknown Channel"
                    clean_name = clean_channel_name(raw_name)

                    logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                    logo = logo_match.group(1) if logo_match else ""

                    group_match = re.search(r'group-title="([^"]*)"', info_line)
                    category = group_match.group(1) if group_match else "General"

                    ch_obj = {
                        "name": clean_name if clean_name else raw_name,
                        "logo": logo,
                        "category": category,
                        "stream_url": stream_url
                    }

                    # তেলেগু চ্যানেল হলে বাদ দেওয়া হবে
                    if not is_telugu_channel(ch_obj):
                        channels.append(ch_obj)
                        seen_urls.add(stream_url)
            i += 1

    # সিরিয়াল অনুযায়ী সর্টিং
    channels.sort(key=get_channel_priority)

    # M3U জেনারেট করা
    m3u_lines = ["#EXTM3U\n"]
    for ch in channels:
        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["category"]}",{ch["name"]}\n{ch["stream_url"]}\n')

    # ১. playlist.json সেভ
    json_data = {
        "status": "success",
        "total_channels": len(channels),
        "channels": channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json আপডেট করা হয়েছে (মোট চ্যানেল: {len(channels)})")

    # ২. playlist.m3u সেভ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u সফলতা সহকারে সেভ হয়েছে")

if __name__ == "__main__":
    fetch_channels_without_telugu()
