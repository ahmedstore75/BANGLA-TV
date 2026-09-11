import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# আপনার নাম
MY_NAME = "Ahmed Store"

def clean_channel_name(name):
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def normalize_text(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def is_excluded_channel(channel):
    name = channel['name'].lower()
    group = channel['group'].lower()
    
    excluded = [
        'telugu', 'tamil', 'kannada', 'malayalam', 'marathi', 'gujarati', 'punjabi', 'oriya', 'odia',
        'gemini', 'vijay', 'sun tv', 'kalignar', 'etv', 'sakshi', 'test', 'dummy', 'promo', 'sample', 
        'shopping', 'teleshopping', 'home shop', 'local', 'cable'
    ]
    if any(k in group for k in excluded) or any(k in name for k in excluded):
        return True
    return False

def check_single_stream(item):
    """
    ১০ সেকেন্ড টাইমআউটে অ্যাক্টিভ স্ট্রিম চেক করে।
    """
    ch_obj, res = item
    url = ch_obj['stream_url']
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            return item
        
        response = requests.get(url, headers=headers, timeout=10, stream=True, allow_redirects=True)
        if response.status_code == 200:
            return item
    except Exception:
        pass
    
    return None

def categorize_and_prioritize(channel):
    group = channel['group'].lower()
    name = channel['name'].lower()
    norm_name = normalize_text(name)

    # ১. বাংলাদেশ টিভি
    bd_popular = [
        'somoy tv', 'somoy news', 'ekattor tv', 'jamuna tv', 'channel i', 'ntv', 
        'atn bangla', 'atn news', 'rtv', 'independent tv', 'banglavision', 'dbc news', 
        'channel 24', 'gtv', 'gazi tv', 'deepto tv', 'maasranga', 'nagorik tv', 
        'boishakhi tv', 'btv', 'btv world', 'titas tv', 'bengal tv', 'sa tv', 'desh tv', 'asian tv'
    ]
    if 'bangladesh' in group or channel.get('source_country') == 'bd':
        if not any(ex in name for ex in ['abp', 'uk', 'india', 'sangeet bangla', 'hope channel', 'enterr10', 'zee', 'star']):
            sub_p = 0 if any(normalize_text(pop) in norm_name for pop in bd_popular) else 1
            return (1, sub_p, "Bangladeshi TV")

    # ২. ক্রিকেট ও ফুটবল স্পোর্টস চ্যানেল ফিল্টার
    popular_sports_allowed = [
        't sports', 'tsports', 'gazi tv', 'gtv', 'star sports', 'sony sports', 
        'sony ten', 'ten sports', 'sports18', 'sports 18', 'willow', 'ptv sports', 
        'dd sports', 'astrosports', 'astro supersport',
        'bein sports', 'supersport', 'sky sports', 'tnt sports', 'eurosport', 
        'laliga tv', 'premier sports', 'cbs sports', 'fox sports'
    ]
    
    unwanted_sports = ['golf', 'racing', 'poker', 'outdoor', 'hunt', 'fight', 'ufc', 'billiards', 'darts']
    
    if any(un_sp in norm_name for un_sp in unwanted_sports):
        return None

    if any(normalize_text(sp_kw) in norm_name for sp_kw in popular_sports_allowed):
        sub_p = 0 if any(normalize_text(pop) in norm_name for pop in ['tsports', 'starsports', 'sonysports', 'sonyten', 'beinsports', 'supersport']) else 1
        return (2, sub_p, "Cricket & Football Sports")

    # ৩. ইন্ডিয়ান মুভি চ্যানেল
    indian_movie_keywords = [
        'star gold', 'sony max', 'zee cinema', 'and pictures', 'andpictures', '&pictures',
        'goldmines', 'b4u movies', 'b4u kadak', 'colors cineplex', 'star movies', 
        'mnx', 'hbo', 'movies now', 'sony pix', 'wb', 'zee classic', 'zee action',
        'rishtey cineplex', 'bhojpuri cinema', 'b4u bhojpuri', '&flix', 'andflix'
    ]
    if any(normalize_text(m_kw) in norm_name for m_kw in indian_movie_keywords):
        popular_movies = ['stargold', 'sonymax', 'zeecinema', 'andpictures', 'b4umovies', 'goldmines', 'colorscineplex']
        sub_p = 0 if any(normalize_text(p_mov) in norm_name for p_mov in popular_movies) else 1
        return (3, sub_p, "Indian Movies")

    # ৪. কলকাতা বাংলা
    kolkata_popular = [
        'star jalsha', 'star jalsha movies', 'zee bangla', 'zee bangla cinema', 'colors bangla', 
        'abp ananda', 'sony aath', 'sangeet bangla', 'zee 24 ghanta', 'enterr10 bangla', 
        'news18 bangla', 'tv9 bangla', 'aakash aath', 'rupashi bangla'
    ]
    if 'kolkata' in group or 'west bengal' in group or any(normalize_text(k) in norm_name for k in kolkata_popular):
        sub_p = 0 if any(normalize_text(pop) in norm_name for pop in kolkata_popular) else 1
        return (4, sub_p, "Kolkata Bangla")

    # ৫. কিডস
    if 'kid' in group or 'animation' in group or any(k in name for k in ['pogo', 'hungama', 'cartoon network', 'nick', 'disney', 'sonic']):
        return (5, 0, "Kids Channels")

    # ৬. ডকুমেন্টারি
    if 'documentary' in group or any(k in name for k in ['discovery', 'national geographic', 'nat geo', 'history tv', 'animal planet']):
        return (6, 0, "Documentary")

    # ৭. মিউজিক
    if 'music' in group or any(k in name for k in ['mnet', 'mtv', '9xm', 'zoom', 'b4u music']):
        return (7, 0, "Music Channels")

    # ৮. ইন্ডিয়ান চ্যানেল
    indian_allowlist = [
        'star plus', 'sony entertainment', 'set india', 'colors', 'zee tv', 'sab tv', 'star bharat',
        'and tv', 'andtv', 'amptv', '&tv', 'b4u plus', 'zee anmol', 'dangal',
        'aaj tak', 'ndtv', 'india today', 'dd national', 'dd news'
    ]
    if any(normalize_text(allow) in norm_name for allow in indian_allowlist):
        return (8, 0, "Indian Channels")

    # ৯. পাকিস্তানি চ্যানেল
    pak_allowlist = [
        'geo tv', 'geo news', 'geo kahani', 'ary digital', 'ary news', 'ary zindagi', 
        'hum tv', 'hum news', 'ptv news', 'ptv home', 'samaa', 
        'express news', 'express entertainment', 'dunya news', 'bol news'
    ]
    if any(normalize_text(allow) in norm_name for allow in pak_allowlist):
        return (9, 0, "Pakistani Channels")

    return None

def fetch_channels_by_group():
    sources = [
        ("https://iptv-org.github.io/iptv/countries/bd.m3u", "bd"),
        ("https://iptv-org.github.io/iptv/languages/ben.m3u", "ben"),
        ("https://iptv-org.github.io/iptv/countries/in.m3u", "in"),
        ("https://iptv-org.github.io/iptv/countries/pk.m3u", "pk"),
        ("https://iptv-org.github.io/iptv/categories/sports.m3u", "sports")
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 চ্যানেল ফেচ করা হচ্ছে...")

    candidate_channels = []
    seen_urls = set()

    # ১. অনলাইন সোর্স
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
                        res = categorize_and_prioritize(ch_obj)
                        if res is not None:
                            candidate_channels.append((ch_obj, res))
                            seen_urls.add(stream_url)
            i += 1

    # ২. PTV Sports, T Sports এবং অন্যান্য পপুলার স্পোর্টস চ্যানেলের একাধিক বিকল্প সোর্স
    extra_sports = [
        # T Sports Multi-Source
        {"name": "T Sports HD", "logo": "https://i.imgur.com/8QGz6vX.png", "group": "Cricket & Football Sports", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd_tsports.m3u8"},
        {"name": "T Sports Live", "logo": "https://i.imgur.com/8QGz6vX.png", "group": "Cricket & Football Sports", "stream_url": "https://iptv-org.github.io/iptv/channels/bd/tsports.m3u8"},
        
        # PTV Sports Multi-Source
        {"name": "PTV Sports HD", "logo": "", "group": "Cricket & Football Sports", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/pk_ptvsports.m3u8"},
        {"name": "PTV Sports Live", "logo": "", "group": "Cricket & Football Sports", "stream_url": "https://iptv-org.github.io/iptv/channels/pk/ptvsports.m3u8"},

        # Gazi TV
        {"name": "Gazi TV (GTV)", "logo": "", "group": "Cricket & Football Sports", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd_gtv.m3u8"},
        
        # Star & Sony Sports
        {"name": "Star Sports 1 HD", "logo": "", "group": "Cricket & Football Sports", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in_starsports1.m3u8"},
        {"name": "Sports18 1 HD", "logo": "", "group": "Cricket & Football Sports", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in_sports18_1.m3u8"},
        {"name": "Sony Sports Ten 1 HD", "logo": "", "group": "Cricket & Football Sports", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in_sonyten1.m3u8"},
        {"name": "Sony Sports Ten 3 HD", "logo": "", "group": "Cricket & Football Sports", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in_sonyten3.m3u8"},
        {"name": "Willow Cricket HD", "logo": "", "group": "Cricket & Football Sports", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_willow.m3u8"}
    ]

    for sp in extra_sports:
        if sp["stream_url"] not in seen_urls:
            candidate_channels.append((sp, (2, 0, "Cricket & Football Sports")))
            seen_urls.add(sp["stream_url"])

    print(f"⚡ {len(candidate_channels)} টি ফিল্টারড চ্যানেল পাওয়া গেছে। ১০ সেকেন্ড টাইমআউটে লাইভ স্ট্যাটাস চেক করা হচ্ছে...")

    working_channels = []
    
    with ThreadPoolExecutor(max_workers=80) as executor:
        futures = [executor.submit(check_single_stream, item) for item in candidate_channels]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_channels.append(result)
                print(f"  🟢 [Live]: {result[0]['name']} -> ({result[1][2]})")

    working_channels.sort(key=lambda x: (x[1][0], x[1][1], x[0]['name'].lower()))
    total_count = len(working_channels)

    m3u_header = f'#EXTM3U name="{MY_NAME} IPTV | Total Channels: {total_count}"\n\n'
    m3u_lines = [m3u_header]
    json_channels = []

    for ch, res in working_channels:
        p, sub_p, display_group = res

        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{display_group}",{ch["name"]}\n{ch["stream_url"]}\n')
        
        json_channels.append({
            "name": ch["name"],
            "logo": ch["logo"],
            "group": display_group,
            "stream_url": ch["stream_url"]
        })

    json_data = {
        "playlist_name": MY_NAME,
        "total_channels": total_count,
        "status": "success",
        "channels": json_channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)

    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)

    print(f"\n✅ প্রসেসিং সম্পন্ন!")
    print(f"📌 প্লেলিস্ট: {MY_NAME}")
    print(f"📊 সেভ হওয়া মোট অ্যাক্টিভ চ্যানেল: {total_count} টি")

if __name__ == "__main__":
    fetch_channels_by_group()
