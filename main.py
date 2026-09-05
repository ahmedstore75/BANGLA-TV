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

    # ১. বাংলাদেশী চ্যানেল (১ নম্বর স্থানে থাকবে)
    bd_keywords = [
        'btv', 'somoy', 'channel i', 'ekattor', 'jamuna', 'rtv', 'atn', 'ntv', 
        'independent', 'bangla vision', 'dbc', 'deepto', 'asian tv', 'desh tv', 
        'nagorik', 'boishakhi', 'maasranga', 'bijoy', 'gtv', 'gazitv', 'bangladesh',
        'duronto', 'saatv', 'sangeet bangla', 'news24', 'channel 24'
    ]
    if any(k in name for k in bd_keywords) or 'bangladesh' in category:
        return 1

    # ২. স্পোর্টস চ্যানেল (বাংলাদেশ, ইন্ডিয়া বা পাকিস্তানের অধীনস্থ)
    sports_keywords = ['sport', 'sports', 't sports', 'tsports', 'star sports', 'sony ten', 'willow', 'ptv sports', 'ten sports', 'geo super']
    if any(k in name for k in sports_keywords) or 'sports' in category:
        return 2

    # ৩. কলকাতা বাংলা চ্যানেল
    kolkata_keywords = ['star jalsha', 'zee bangla', 'colors bangla', 'sony aath', 'rupashi bangla', 'sangeet bangla', 'news18 bangla', 'tv9 bangla', 'khabor 365', 'calcutta', 'kolkata']
    if any(k in name for k in kolkata_keywords):
        return 3

    # ৪. ইন্ডিয়ান টিভি চ্যানেল
    indian_keywords = ['zee', 'star', 'sony', 'colors', 'aaj tak', 'ndtv', 'india', 'sab', 'bindass', 'pogo', 'hungama', 'discovery india', 'sun tv']
    if any(k in name for k in indian_keywords) or 'india' in category:
        return 4

    # ৫. পাকিস্তানি চ্যানেল
    pak_keywords = ['geo', 'ary', 'hum', 'ptv', 'express', 'dunya', 'samaa', 'bol', 'a-plus', 'pakistan']
    if any(k in name for k in pak_keywords) or 'pakistan' in category:
        return 5

    # ফিল্টারের বাইরে থাকা যেকোনো চ্যানেল ব্লক হবে
    return 99

def fetch_specific_country_channels():
    # শুধুমাত্র বাংলাদেশ, ইন্ডিয়া এবং পাকিস্তানের অফিশিয়াল প্লেলিস্ট সোর্স
    sources = [
        "https://iptv-org.github.io/iptv/languages/ben.m3u", # বাংলা চ্যানেল
        "https://iptv-org.github.io/iptv/countries/bd.m3u",  # বাংলাদেশ
        "https://iptv-org.github.io/iptv/countries/in.m3u",  # ইন্ডিয়া
        "https://iptv-org.github.io/iptv/countries/pk.m3u"   # পাকিস্তান
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 শুধুমাত্র BD, IN এবং PK চ্যানেল লোড করা হচ্ছে...")

    channels = []
    seen_urls = set()  # ডুপ্লিকেট ইউআরএল ফিল্টার করার জন্য

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

                # এক স্ট্রিম লিঙ্ক দুইবার আসবে না
                if stream_url and stream_url not in seen_urls:
                    raw_name = info_line.split(",")[-1].strip() if "," in info_line else "Unknown Channel"
                    clean_name = clean_channel_name(raw_name)

                    logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                    logo = logo_match.group(1) if logo_match else ""

                    group_match = re.search(r'group-title="([^"]*)"', info_line)
                    category = group_match.group(1) if group_match else "General"

                    ch_obj = {
                        "name": clean_name,
                        "logo": logo,
                        "category": category,
                        "stream_url": stream_url
                    }
                    
                    priority = get_channel_priority(ch_obj)
                    
                    # শুধুমাত্র BD, IN, PK এবং স্পোর্টস চ্যানেল রাখা হবে (অন্যান্য দেশ বাদ)
                    if priority != 99:
                        channels.append(ch_obj)
                        seen_urls.add(stream_url)
            i += 1

    # সিরিয়াল অনুযায়ী সাজানো (BD -> Sports -> Kolkata -> India -> Pakistan)
    channels.sort(key=get_channel_priority)

    # M3U জেনারেট করা
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
    print("✅ playlist.m3u সফলভাবে সেভ করা হয়েছে")

if __name__ == "__main__":
    fetch_specific_country_channels()
