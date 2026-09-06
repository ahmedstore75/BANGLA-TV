import requests
import json
import re

def clean_channel_name(name):
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def normalize_text(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def is_excluded_channel(channel):
    name = channel['name'].lower()
    group = channel['group'].lower()
    
    # তেলেগু, তামিল এবং অপ্রয়োজনীয় টেস্ট/লোকাল চ্যানেল ফিল্টারিং
    excluded = [
        'telugu', 'tamil', 'gemini', 'vijay', 'sun tv', 'kalignar', 'etv telugu', 'sakshi',
        'test', 'dummy', 'promo', 'sample', 'stream'
    ]
    if any(k in group for k in ['telugu', 'tamil']) or any(k in name for k in excluded):
        return True
    return False

def categorize_and_prioritize(channel):
    group = channel['group'].lower()
    name = channel['name'].lower()
    norm_name = normalize_text(name)

    # ১. বাংলাদেশ (সুনির্দিষ্ট পপুলার টিভি চ্যানেল)
    if 'bangladesh' in group or channel.get('source_country') == 'bd':
        if not any(ex in name for ex in ['abp', 'uk', 'india', 'sangeet bangla', 'hope channel', 'enterr10']):
            bd_popular = [
                'somoy tv', 'somoy news', 'ekattor tv', 'jamuna tv', 'channel i', 'ntv', 
                'atn bangla', 'atn news', 'rtv', 'independent tv', 'banglavision', 'dbc news', 
                'channel 24', 'gtv', 'gazi tv', 'deepto tv', 'maasranga', 'nagorik tv', 
                'boishakhi tv', 'btv', 'btv world', 'titas tv', 'bengal tv'
            ]
            sub_p = 0 if any(normalize_text(pop) in norm_name for pop in bd_popular) else 1
            return (1, sub_p, "Bangladeshi TV")

    # ২. স্পোর্টস (সুনির্দিষ্ট আসল স্পোর্টস চ্যানেল)
    sports_keywords = ['sport', 'sports', 'cricket', 'kabaddi']
    if any(k in group for k in sports_keywords) or any(k in name for k in ['t sports', 'star sports', 'sony sports', 'sony ten', 'ten sports', 'willow', 'ptv sports', 'dd sports']):
        sports_popular = [
            'tsports', 't sports', 'starsports1', 'starsports2', 'starsports', 'sonysports', 
            'sonyten1', 'sonyten2', 'sonyten3', 'sonyten5', 'tensports', 'willowtv', 'ptvsports', 'ddsports'
        ]
        sub_p = 0 if any(normalize_text(pop) == norm_name or normalize_text(pop) in norm_name for pop in sports_popular) else 1
        return (2, sub_p, "Sports Channels")

    # ৩. কলকাতা বাংলা (Enterr10 Bangla সহ)
    kolkata_popular = [
        'star jalsha', 'star jalsha movies', 'zee bangla', 'zee bangla cinema', 'colors bangla', 
        'abp ananda', 'sony aath', 'sangeet bangla', 'zee 24 ghanta', 'enterr10 bangla', 
        'news18 bangla', 'tv9 bangla', 'aakash aath', 'rupashi bangla'
    ]
    if 'kolkata' in group or 'west bengal' in group or any(normalize_text(k) in norm_name for k in kolkata_popular):
        sub_p = 0 if any(normalize_text(pop) in norm_name for pop in kolkata_popular) else 1
        return (3, sub_p, "Kolkata Bangla")

    # ৪. কিডস
    if 'kid' in group or 'animation' in group or any(k in name for k in ['pogo', 'hungama', 'cartoon network', 'nick', 'disney', 'sonic']):
        return (4, 0, "Kids Channels")

    # ৫. ডকুমেন্টারি
    if 'documentary' in group or any(k in name for k in ['discovery', 'national geographic', 'nat geo', 'history tv', 'animal planet']):
        return (5, 0, "Documentary")

    # ৬. মিউজিক
    if 'music' in group or any(k in name for k in ['mnet', 'mtv', '9xm', 'zoom', 'b4u music']):
        return (6, 0, "Music Channels")

    # ৭. ইন্ডিয়ান অরিজিনাল পপুলার ও মুভি চ্যানেল (এখানে আজেবাজে চ্যানেল ফিল্টার হবে)
    indian_popular = [
        'star plus', 'sony entertainment television', 'set india', 'colors tv', 'zee tv', 'sab tv', 'star bharat',
        'star movies', 'mnx', 'hbo', 'movies now', 'sony pix', 'wb', 
        'star gold', 'star gold hd', 'star gold 2', 'sony max', 'sony max hd', 'sony max 2', 
        'zee cinema', 'zee cinema hd', 'goldmines', 'goldmines movies', 'b4u movies', 
        'b4u bhojpuri', 'bhojpuri cinema', 'zee anmol cinema', 'colors cineplex', 
        'aaj tak', 'ndtv india', 'india today'
    ]
    
    # স্ট্রিক্ট ম্যাচিং: পপুলার লিস্টে থাকলে sub_p = 0 (উপরে থাকবে), না থাকলে sub_p = 1 (নিচে যাবে)
    if 'india' in group or channel.get('source_country') == 'in':
        is_popular = any(normalize_text(pop) == norm_name or normalize_text(pop) in norm_name for pop in indian_popular)
        sub_p = 0 if is_popular else 1
        return (7, sub_p, "Indian Channels")

    # ৮. পাকিস্তান
    if 'pakistan' in group or channel.get('source_country') == 'pk':
        pak_popular = ['geo tv', 'ary digital', 'hum tv', 'ptv sports', 'geo news', 'ary news', 'samaa']
        sub_p = 0 if any(normalize_text(pop) in norm_name for pop in pak_popular) else 1
        return (8, sub_p, "Pakistani Channels")

    return (7, 2, "Indian Channels")

def fetch_channels_by_group():
    sources = [
        ("https://iptv-org.github.io/iptv/countries/bd.m3u", "bd"),
        ("https://iptv-org.github.io/iptv/languages/ben.m3u", "ben"),
        ("https://iptv-org.github.io/iptv/countries/in.m3u", "in"),
        ("https://iptv-org.github.io/iptv/countries/pk.m3u", "pk")
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 আজেবাজে চ্যানেল ফিল্টার করে শুধুমাত্র আসল পপুলার চ্যানেলগুলোকে উপরে সাজানো হচ্ছে...")

    channels = []
    seen_urls = set()

    for url, country_code in sources:
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
                    group = group_match.group(1) if group_match else "General"

                    ch_obj = {
                        "name": clean_name if clean_name else raw_name,
                        "logo": logo,
                        "group": group,
                        "stream_url": stream_url,
                        "source_country": country_code
                    }

                    if not is_excluded_channel(ch_obj):
                        channels.append(ch_obj)
                        seen_urls.add(stream_url)
            i += 1

    # সর্টিং
    channels.sort(key=lambda x: categorize_and_prioritize(x)[:2])

    m3u_lines = ["#EXTM3U\n"]
    json_channels = []

    for ch in channels:
        p, sub_p, display_group = categorize_and_prioritize(ch)

        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{display_group}",{ch["name"]}\n{ch["stream_url"]}\n')
        
        json_channels.append({
            "name": ch["name"],
            "logo": ch["logo"],
            "group": display_group,
            "stream_url": ch["stream_url"]
        })

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump({"status": "success", "total_channels": len(json_channels), "channels": json_channels}, jf, indent=4, ensure_ascii=False)

    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)

    print(f"✅ সফলভাবে সর্বমোট {len(json_channels)} টি চ্যানেল ফিল্টার করা হয়েছে!")

if __name__ == "__main__":
    fetch_channels_by_group()
