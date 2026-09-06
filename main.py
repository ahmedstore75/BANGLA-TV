import requests
import json
import re

def clean_channel_name(name):
    # ব্র্যাকেট (), [], {} এবং ভেতরের নাম মুছে পরিষ্কার নাম তৈরি করা
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def is_excluded_channel(channel):
    name = channel['name'].lower()
    category = channel['category'].lower()
    
    # তেলেগু চ্যানেল চেনার কিউয়ার্ড
    telugu_keywords = [
        'telugu', 'gemini tv', 'gemini movies', 'gemini music', 'gemini comedy',
        'etv telugu', 'etv plus', 'etv cinema', 'etv life', 'etv abhirami',
        'sakshi', 'v6 news', 'tv9 telugu', 'ntv telugu', 't news', '10tv',
        'abn andhra jyothi', 'bhakthi tv', 'svbc', 'raj news telugu', 'mahaa news',
        'hmtv', 'prime9 news', 'studio n', 'cvr news', 'tollywood'
    ]

    # তামিল চ্যানেল চেনার কিউয়ার্ড
    tamil_keywords = [
        'tamil', 'sun tv', 'sun music', 'sun news', 'vijay tv', 'star vijay',
        'kalignar', 'jaya tv', 'polimer', 'zee tamil', 'colors tamil', 'raj tv',
        'thanthi tv', 'news7 tamil', 'puthiya thalaimurai', 'vendhar tv', 'captain tv',
        'vasanth tv', 'seithigal', 'mk tv', 'j invasion', 'tamizh'
    ]

    if 'telugu' in category or 'tamil' in category:
        return True
    if any(k in name for k in telugu_keywords):
        return True
    if any(k in name for k in tamil_keywords):
        return True

    return False

def get_channel_priority(channel):
    name = channel['name'].lower()
    category = channel['category'].lower()

    # ১. বাংলাদেশী সব ধরনের চ্যানেল (১ম অগ্রাধিকার - সবার উপরে)
    bd_keywords = [
        'btv', 'somoy', 'channel i', 'ekattor', 'jamuna', 'rtv', 'atn', 'ntv', 
        'independent', 'bangla vision', 'banglavision', 'dbc', 'deepto', 'asian tv', 
        'desh tv', 'nagorik', 'boishakhi', 'maasranga', 'bijoy', 'gtv', 'gazitv', 
        'bangladesh', 'duronto', 'saatv', 'saa tv', 'sangeet bangla', 'news24', 
        'channel 24', 'mohana', 'channel9', 'channel 9', 'my tv', 'mytv', 'nexus', 
        'titas', 'chotoder', 'ananda', 'bengal', 'shomoy', 'bd'
    ]
    
    # যদি নামে বা ক্যাটাগরিতে বাংলাদেশের চিহ্ন থাকে তবে সরাসরি পজিশন ১
    if any(k in name for k in bd_keywords) or 'bangladesh' in category or 'bd' in category:
        return 1

    # ২. স্পোর্টস চ্যানেল
    sports_keywords = ['sport', 'sports', 't sports', 'tsports', 'star sports', 'sony ten', 'willow', 'ptv sports', 'ten sports', 'geo super', 'cric']
    if any(k in name for k in sports_keywords) or 'sports' in category:
        return 2

    # ৩. কলকাতা বাংলা চ্যানেল
    kolkata_keywords = ['star jalsha', 'zee bangla', 'colors bangla', 'sony aath', 'rupashi bangla', 'sangeet bangla', 'news18 bangla', 'tv9 bangla', 'khabor 365', 'calcutta', 'kolkata']
    if any(k in name for k in kolkata_keywords) or 'bangla' in category:
        return 3

    # ৪. ইন্ডিয়ান টিভি চ্যানেল
    indian_keywords = ['zee', 'star', 'sony', 'colors', 'aaj tak', 'ndtv', 'india', 'sab', 'bindass', 'pogo', 'hungama', 'discovery']
    if any(k in name for k in indian_keywords) or 'india' in category:
        return 4

    # ৫. পাকিস্তানি চ্যানেল
    pak_keywords = ['geo', 'ary', 'hum', 'ptv', 'express', 'dunya', 'samaa', 'bol', 'a-plus', 'pakistan']
    if any(k in name for k in pak_keywords) or 'pakistan' in category:
        return 5

    return 6

def fetch_channels():
    sources = [
        "https://iptv-org.github.io/iptv/countries/bd.m3u",   # বাংলাদেশী চ্যানেল সবার আগে প্রসেস হবে
        "https://iptv-org.github.io/iptv/languages/ben.m3u",  # বাংলা চ্যানেল সোর্স
        "https://iptv-org.github.io/iptv/countries/in.m3u",
        "https://iptv-org.github.io/iptv/countries/pk.m3u"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 বাংলাদেশী চ্যানেলকে ১০০% উপরে রেখে ফিল্টার করা হচ্ছে...")

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

                    if not is_excluded_channel(ch_obj):
                        channels.append(ch_obj)
                        seen_urls.add(stream_url)
            i += 1

    # সর্টিং অ্যালগরিদম রান করা (BD Channels -> Sports -> Kolkata Bangla -> India -> Pakistan)
    channels.sort(key=get_channel_priority)

    # M3U ফাইল তৈরি
    m3u_lines = ["#EXTM3U\n"]
    for ch in channels:
        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["category"]}",{ch["name"]}\n{ch["stream_url"]}\n')

    # ১. playlist.json তৈরি
    json_data = {
        "status": "success",
        "total_channels": len(channels),
        "channels": channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json আপডেট করা হয়েছে (মোট চ্যানেল: {len(channels)})")

    # ২. playlist.m3u তৈরি
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u সফলভাবে আপডেট করা হয়েছে")

if __name__ == "__main__":
    fetch_channels()
