import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

MY_NAME = "Ahmed Store Premium IPTV"
MAX_TOTAL_CHANNELS = 300

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
        'shopping', 'teleshopping', 'home shop', 'local', 'cable', 'radio', 'fm',
        'latin', 'latam', 'brazil', 'mexico', 'spanish', 'portuguese', 'pluto'
    ]
    if any(k in group for k in excluded) or any(k in name for k in excluded):
        return True
    return False

def check_single_stream(item):
    """
    নেটওয়ার্ক ফেল মারার ঝামেলা এড়াতে রিকুয়েস্ট টাইমআউট সেফ রাখা হয়েছে
    """
    ch_obj, res = item
    url = ch_obj['stream_url']
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return item
    except Exception:
        pass

    try:
        response = requests.get(url, headers=headers, timeout=5, stream=True, allow_redirects=True)
        if response.status_code == 200:
            return item
    except Exception:
        pass
    
    return None

def categorize_and_prioritize(channel):
    group = channel['group'].lower()
    name = channel['name'].lower()
    norm_name = normalize_text(name)

    # ১. Bangladeshi Entertainment & News
    bd_keywords = ['somoy', 'jamuna', 'ekattor', 'independent', 'channel i', 'atn', 'ntv', 'rtv', 'deepto', 'boishakhi', 'banglavision', 'deshtv', 'maasranga', 'nagorik']
    if 'bangladesh' in group or channel.get('source_country') == 'bd' or any(k in norm_name for k in bd_keywords):
        return (1, "Bangladeshi TV")

    # ২. Sports Channels
    sports_keywords = ['tsports', 't sports', 'gtv', 'gazi tv', 'star sports', 'sony sports', 'sony ten', 'ten sports', 'sports18', 'willow', 'ptv sports', 'astro sports']
    if any(normalize_text(sp) in norm_name for sp in sports_keywords):
        return (2, "Sports Channels")

    # ৩. Kolkata Bangla
    kolkata_popular = ['star jalsha', 'zee bangla', 'colors bangla', 'abp ananda', 'sony aath', 'sangeet bangla', 'zee 24 ghanta', 'news18 bangla', 'tv9 bangla']
    if 'kolkata' in group or 'west bengal' in group or any(normalize_text(k) in norm_name for k in kolkata_popular):
        return (3, "Kolkata Bangla")

    # ৪. Indian Movies
    indian_movies = ['star gold', 'sony max', 'zee cinema', 'and pictures', 'goldmines', 'b4u movies', 'colors cineplex']
    if any(normalize_text(m) in norm_name for m in indian_movies):
        return (4, "Indian Movie Channels")

    # ৫. English Movies & Entertainment
    english_movies = ['hbo', 'star movies', 'sony pix', 'movies now', '&flix', 'mnx', 'wb', 'paramount', 'axn']
    if any(normalize_text(em) in norm_name for em in english_movies):
        return (5, "English Movies & Entertainment")

    # ৬. Kids Channels
    kids_keywords = ['hungama', 'super hungama', 'pogo', 'cartoon network', 'sonic', 'nickelodeon', 'nick', 'disney']
    if any(k in norm_name for k in kids_keywords):
        return (6, "Kids Channels")

    # ৭. Documentary & Info
    doc_keywords = ['discovery', 'national geographic', 'nat geo', 'animal planet', 'history tv', 'planet earth']
    if any(normalize_text(k) in norm_name for k in doc_keywords):
        return (7, "Documentary & Info")

    # ৮. Islamic TV
    islamic_keywords = ['makkah', 'madinah', 'peace tv', 'quran', 'islam', 'madani', 'iqra']
    if any(k in norm_name for k in islamic_keywords) or 'islamic' in group:
        return (8, "Islamic TV")

    # ৯. Music Channels
    music_keywords = ['9xm', 'mtv', 'zoom', 'b4u music', 'sangeet bangla']
    if any(k in norm_name for k in music_keywords):
        return (9, "Music Channels")

    # ১০. International News
    global_news = ['bbc news', 'cnn', 'al jazeera', 'aaj tak', 'ndtv', 'india today', 'dw news']
    if any(normalize_text(news) in norm_name for news in global_news):
        return (10, "International News")

    return None

def fetch_and_generate_playlist():
    sources = [
        ("https://iptv-org.github.io/iptv/countries/bd.m3u", "bd"),
        ("https://iptv-org.github.io/iptv/languages/ben.m3u", "ben"),
        ("https://iptv-org.github.io/iptv/countries/in.m3u", "in"),
        ("https://iptv-org.github.io/iptv/categories/sports.m3u", "sports"),
        ("https://iptv-org.github.io/iptv/categories/news.m3u", "news"),
        ("https://iptv-org.github.io/iptv/categories/religious.m3u", "religious"),
        ("https://iptv-org.github.io/iptv/categories/movies.m3u", "movies"),
        ("https://iptv-org.github.io/iptv/categories/animation.m3u", "animation"),
        ("https://iptv-org.github.io/iptv/categories/documentary.m3u", "documentary")
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 সোর্স থেকে চ্যানেল ফিল্টার করা শুরু হচ্ছে...")

    candidate_channels = []
    seen_urls = set()
    seen_channel_names = set()

    # ১. অনলাইন সোর্স প্রসেসিং (ফেইল-সেফ ট্রাই ব্লকে)
    for url, country_code in sources:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            raw_data = response.text
        except Exception as e:
            print(f"⚠️ লিঙ্ক লোড হতে সমস্যা: {url}")
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
                    norm_clean_name = normalize_text(clean_name)

                    if norm_clean_name not in seen_channel_names:
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
                                seen_channel_names.add(norm_clean_name)
            i += 1

    # ২. ১০০% কাজ করবে এমন কিছু ডাইরেক্ট ইম্পর্ট্যান্ট ব্যাকআপ স্ট্রিম
    direct_backup_channels = [
        {"name": "Jamuna TV HD", "logo": "", "group": "Bangladeshi TV", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd_jamunatv.m3u8"},
        {"name": "Somoy TV", "logo": "", "group": "Bangladeshi TV", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd_somoytv.m3u8"},
        {"name": "BBC News HD", "logo": "", "group": "International News", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uk_bbcnews.m3u8"},
        {"name": "Al Jazeera English HD", "logo": "", "group": "International News", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/qa_aljazeeraenglish.m3u8"},
        {"name": "Makkah Live", "logo": "", "group": "Islamic TV", "stream_url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/sa_makkahlive.m3u8"}
    ]

    for item in direct_backup_channels:
        norm_n = normalize_text(item["name"])
        if item["stream_url"] not in seen_urls and norm_n not in seen_channel_names:
            p_val = 1 if item["group"] == "Bangladeshi TV" else (8 if item["group"] == "Islamic TV" else 10)
            candidate_channels.append((item, (p_val, item["group"])))
            seen_urls.add(item["stream_url"])
            seen_channel_names.add(norm_n)

    print(f"⚡ {len(candidate_channels)} টি চ্যানেল চেক করা হচ্ছে...")

    working_channels = []
    
    # থ্রেড সংখ্যা কমিয়ে স্পিড ও স্ট্যাবিবিলিটি নিশ্চিতকরণ
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_single_stream, item) for item in candidate_channels]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_channels.append(result)

    working_channels.sort(key=lambda x: (x[1][0], x[0]['name'].lower()))

    final_selected_channels = working_channels[:MAX_TOTAL_CHANNELS]
    total_count = len(final_selected_channels)

    m3u_header = f'#EXTM3U name="{MY_NAME} | Total: {total_count}"\n\n'
    m3u_lines = [m3u_header]
    json_channels = []

    for ch, res in final_selected_channels:
        p_val, display_group = res

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

    print(f"\n✅ প্রসেস সফলভাবে শেষ হয়েছে!")
    print(f"📌 মোট প্লেলিস্টে যুক্ত হওয়া অ্যাক্টিভ চ্যানেল: {total_count} টি")

if __name__ == "__main__":
    fetch_and_generate_playlist()
