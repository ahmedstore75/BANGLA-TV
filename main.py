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
    
    # আঞ্চলিক অখ্যাত ভারতীয় ভাষা ও অপ্রয়োজনীয় চ্যানেল ফিল্টার
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
    ১০ সেকেন্ড টাইমআউটে অ্যাক্টিভ ও ওয়ার্কিং স্ট্রিম চেক করে।
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

    # ১. বাংলাদেশের সকল চ্যানেল (Priority 1)
    if 'bangladesh' in group or channel.get('source_country') == 'bd':
        return (1, 0, "Bangladeshi TV")

    # ২. পপুলার স্পোর্টস চ্যানেল (Priority 2)
    sports_keywords = [
        't sports', 'tsports', 'gazi tv', 'gtv', 'star sports', 'sony sports', 
        'sony ten', 'ten sports', 'sports18', 'sports 18', 'willow', 'ptv sports', 
        'dd sports', 'astrosports', 'bein sports', 'supersport', 'sky sports', 'eurosport'
    ]
    unwanted_sports = ['golf', 'racing', 'poker', 'outdoor', 'hunt', 'fight', 'ufc', 'billiards', 'darts']
    
    if not any(un_sp in norm_name for un_sp in unwanted_sports):
        if any(normalize_text(sp) in norm_name for sp in sports_keywords):
            return (2, 0, "Sports Channels")

    # ৩. ইসলামিক চ্যানেল (Priority 3)
    islamic_keywords = ['islam', 'quran', 'madani', 'peace tv', 'makkah', 'madinah', 'sunnah', 'alhuda', 'iqra']
    if any(k in norm_name for k in islamic_keywords) or 'islamic' in group:
        return (3, 0, "Islamic TV")

    # ৪. ইন্ডিয়ান পপুলার মুভি চ্যানেল (Priority 4)
    indian_movies = [
        'star gold', 'sony max', 'zee cinema', 'and pictures', '&pictures',
        'goldmines', 'b4u movies', 'colors cineplex', 'zee classic', 'zee action',
        'rishtey cineplex'
    ]
    if any(normalize_text(m) in norm_name for m in indian_movies):
        return (4, 0, "Indian Movie Channels")

    # ৫. ইংলিশ পপুলার মুভি চ্যানেল (ইন্ডিয়ান মুভির ঠিক নিচে - Priority 5)
    english_movies = [
        'hbo', 'star movies', 'sony pix', 'movies now', '&flix', 'andflix',
        'mnx', 'wb', 'paramount', 'cinemax', 'sky cinema', 'film4', 'amc'
    ]
    if any(normalize_text(em) in norm_name for em in english_movies):
        return (5, 0, "English Movie Channels")

    # ৬. কলকাতা বাংলা পপুলার চ্যানেল (Priority 6)
    kolkata_popular = [
        'star jalsha', 'star jalsha movies', 'zee bangla', 'zee bangla cinema', 'colors bangla', 
        'abp ananda', 'sony aath', 'sangeet bangla', 'zee 24 ghanta', 'enterr10 bangla', 
        'news18 bangla', 'tv9 bangla', 'aakash aath'
    ]
    if 'kolkata' in group or 'west bengal' in group or any(normalize_text(k) in norm_name for k in kolkata_popular):
        return (6, 0, "Kolkata Bangla")

    # ৭. পপুলার কিডস/কার্টুন চ্যানেল (Priority 7)
    kids_keywords = ['pogo', 'hungama', 'cartoon network', 'cartoonnetwork', 'nick', 'disney', 'sonic']
    if any(k in norm_name for k in kids_keywords):
        return (7, 0, "Kids Channels")

    # ৮. পপুলার ডকুমেন্টারি ও তথ্যভিত্তিক (Priority 8)
    doc_keywords = ['discovery', 'national geographic', 'nat geo', 'natgeo', 'history tv', 'animal planet']
    if any(k in norm_name for k in doc_keywords):
        return (8, 0, "Documentary & Info")

    # ৯. পপুলার মিউজিক চ্যানেল (Priority 9)
    music_keywords = ['mnet', 'mtv', '9xm', 'zoom', 'b4u music', 'sangeet bangla']
    if any(k in norm_name for k in music_keywords):
        return (9, 0, "Music Channels")

    # ১০. আন্তর্জাতিক পপুলার নিউজ (Priority 10)
    global_news = ['bbc news', 'cnn', 'al jazeera', 'aaj tak', 'ndtv india', 'india today']
    if any(normalize_text(news) in norm_name for news in global_news):
        return (10, 0, "International News")

    return None

def fetch_channels_by_group():
    sources = [
        ("https://iptv-org.github.io/iptv/countries/bd.m3u", "bd"),
        ("https://iptv-org.github.io/iptv/languages/ben.m3u", "ben"),
        ("https://iptv-org.github.io/iptv/countries/in.m3u", "in"),
        ("https://iptv-org.github.io/iptv/countries/pk.m3u", "pk"),
        ("https://iptv-org.github.io/iptv/categories/sports.m3u", "sports"),
        ("https://iptv-org.github.io/iptv/categories/religious.m3u", "religious"),
        ("https://iptv-org.github.io/iptv/categories/movies.m3u", "movies"),
        ("https://iptv-org.github.io/iptv/categories/animation.m3u", "animation"),
        ("https://iptv-org.github.io/iptv/categories/documentary.m3u", "documentary")
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 সোর্স থেকে চ্যানেল ফিল্টার করা হচ্ছে...")

    candidate_channels = []
    seen_urls = set()

    # ১. অনলাইন সোর্স প্রসেসিং
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

    # ২. ব্যাকআপ ও পপুলার কাস্টম সোর্স
    extra_channels = [
        # T Sports Multi-Source
        {"name": "T Sports HD", "logo": "https://i.imgur.com/8QGz6vX.png", "group": "Sports Channels", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd_tsports.m3u8"},
        {"name": "T Sports Live", "logo": "https://i.imgur.com/8QGz6vX.png", "group": "Sports Channels", "stream_url": "https://iptv-org.github.io/iptv/channels/bd/tsports.m3u8"},
        
        # PTV Sports Multi-Source
        {"name": "PTV Sports HD", "logo": "", "group": "Sports Channels", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/pk_ptvsports.m3u8"},
        {"name": "PTV Sports Live", "logo": "", "group": "Sports Channels", "stream_url": "https://iptv-org.github.io/iptv/channels/pk/ptvsports.m3u8"},

        # Primary Sports
        {"name": "Gazi TV (GTV)", "logo": "", "group": "Sports Channels", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd_gtv.m3u8"},
        {"name": "Star Sports 1 HD", "logo": "", "group": "Sports Channels", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in_starsports1.m3u8"},
        {"name": "Sports18 1 HD", "logo": "", "group": "Sports Channels", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in_sports18_1.m3u8"},
        {"name": "Sony Sports Ten 1 HD", "logo": "", "group": "Sports Channels", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in_sonyten1.m3u8"},
        {"name": "Sony Sports Ten 3 HD", "logo": "", "group": "Sports Channels", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in_sonyten3.m3u8"},
        
        # Islamic Channels
        {"name": "Makkah Live", "logo": "", "group": "Islamic TV", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/sa_makkahlive.m3u8"},
        {"name": "Madinah Live", "logo": "", "group": "Islamic TV", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/sa_madinahlive.m3u8"},
        {"name": "Peace TV Bangla", "logo": "", "group": "Islamic TV", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ae_peacetvbangla.m3u8"},

        # English Movies
        {"name": "HBO HD", "logo": "", "group": "English Movie Channels", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us_hbo.m3u8"},
        {"name": "Star Movies HD", "logo": "", "group": "English Movie Channels", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in_starmovies.m3u8"}
    ]

    for extra in extra_channels:
        if extra["stream_url"] not in seen_urls:
            p_val = 2 if extra["group"] == "Sports Channels" else (3 if extra["group"] == "Islamic TV" else 5)
            candidate_channels.append((extra, (p_val, 0, extra["group"])))
            seen_urls.add(extra["stream_url"])

    print(f"⚡ {len(candidate_channels)} টি নির্দিষ্ট পপুলার চ্যানেল ফিল্টার করা হয়েছে। ১০ সেকেন্ডে অ্যাক্টিভ চেক চালু হচ্ছে...")

    working_channels = []
    
    with ThreadPoolExecutor(max_workers=80) as executor:
        futures = [executor.submit(check_single_stream, item) for item in candidate_channels]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_channels.append(result)
                print(f"  🟢 [Live]: {result[0]['name']} -> ({result[1][2]})")

    # ক্যাটাগরি প্রায়োরিটি Index (1 -> 10) অনুযায়ী সাজানো
    working_channels.sort(key=lambda x: (x[1][0], x[0]['name'].lower()))
    total_count = len(working_channels)

    # M3U এবং JSON প্লেলিস্ট তৈরি
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
