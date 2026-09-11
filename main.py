import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

MY_NAME = "Ahmed Store Premium IPTV"
MAX_TOTAL_CHANNELS = 300  # ২৫০+ বা ৩০০ চ্যানেলের প্রফেশনাল প্লেলিস্ট

def clean_channel_name(name):
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def normalize_text(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def is_excluded_channel(channel):
    name = channel['name'].lower()
    group = channel['group'].lower()
    
    # অপ্রয়োজনীয় রিজিওনাল ভাষা ও স্প্যাম বাদ দেওয়া
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
    ১০ সেকেন্ড টাইমআউটে শুধু লাইভ এবং একটি মাত্র ভ্যালিড লিংক ফিল্টার করে
    """
    ch_obj, res = item
    url = ch_obj['stream_url']
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.head(url, headers=headers, timeout=8, allow_redirects=True)
        if response.status_code == 200:
            return item
        
        response = requests.get(url, headers=headers, timeout=8, stream=True, allow_redirects=True)
        if response.status_code == 200:
            return item
    except Exception:
        pass
    
    return None

def categorize_and_prioritize(channel):
    group = channel['group'].lower()
    name = channel['name'].lower()
    norm_name = normalize_text(name)

    # ১. Bangladeshi TV
    if 'bangladesh' in group or channel.get('source_country') == 'bd':
        return (1, "Bangladeshi TV")

    # ২. Sports Channels
    sports_keywords = [
        't sports', 'tsports', 'gazi tv', 'gtv', 'star sports', 'sony sports', 
        'sony ten', 'ten sports', 'sports18', 'sports 18', 'willow', 'ptv sports', 
        'dd sports', 'astrosports', 'bein sports', 'supersport', 'sky sports', 'eurosport'
    ]
    unwanted_sports = ['golf', 'racing', 'poker', 'outdoor', 'hunt', 'fight', 'ufc', 'billiards', 'darts']
    if not any(un_sp in norm_name for un_sp in unwanted_sports):
        if any(normalize_text(sp) in norm_name for sp in sports_keywords):
            return (2, "Sports Channels")

    # ৩. Kolkata Bangla
    kolkata_popular = [
        'star jalsha', 'star jalsha movies', 'zee bangla', 'zee bangla cinema', 'colors bangla', 
        'abp ananda', 'sony aath', 'sangeet bangla', 'zee 24 ghanta', 'enterr10 bangla', 
        'news18 bangla', 'tv9 bangla', 'aakash aath'
    ]
    if 'kolkata' in group or 'west bengal' in group or any(normalize_text(k) in norm_name for k in kolkata_popular):
        return (3, "Kolkata Bangla")

    # ৪. Indian Movie Channels
    indian_movies = [
        'star gold', 'sony max', 'zee cinema', 'and pictures', '&pictures',
        'goldmines', 'b4u movies', 'colors cineplex', 'zee classic', 'zee action',
        'rishtey cineplex'
    ]
    if any(normalize_text(m) in norm_name for m in indian_movies):
        return (4, "Indian Movie Channels")

    # ৫. English Movies & Entertainment
    english_movies = [
        'hbo', 'star movies', 'sony pix', 'movies now', '&flix', 'andflix',
        'mnx', 'wb', 'paramount', 'cinemax', 'sky cinema', 'film4', 'amc', 'axn'
    ]
    if any(normalize_text(em) in norm_name for em in english_movies):
        return (5, "English Movies & Entertainment")

    # ৬. Asian/Indian Kids Channels
    kids_keywords = ['hungama', 'super hungama', 'pogo', 'cartoon network', 'cartoonnetwork', 'sonic', 'nickelodeon', 'nick', 'disney', 'sony yay']
    if any(k in norm_name for k in kids_keywords):
        return (6, "Kids Channels")

    # ৭. Documentary & Info
    doc_popular_keywords = [
        'discovery', 'national geographic', 'nat geo', 'natgeo', 
        'animal planet', 'history tv', 'history channel', 'planet earth'
    ]
    if any(normalize_text(k) in norm_name for k in doc_popular_keywords):
        return (7, "Documentary & Info")

    # ৮. Islamic TV
    islamic_keywords = ['islam', 'quran', 'madani', 'peace tv', 'makkah', 'madinah', 'sunnah', 'alhuda', 'iqra']
    if any(k in norm_name for k in islamic_keywords) or 'islamic' in group:
        return (8, "Islamic TV")

    # ৯. Music Channels
    music_keywords = ['mnet', 'mtv', '9xm', 'zoom', 'b4u music', 'sangeet bangla', 'mh1']
    if any(k in norm_name for k in music_keywords):
        return (9, "Music Channels")

    # ১০. International News
    global_news = [
        'bbc news', 'bbc world news', 'cnn', 'cnn international', 'al jazeera', 
        'al jazeera english', 'aaj tak', 'ndtv india', 'ndtv 24x7', 'india today', 'dw news', 'france 24'
    ]
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

    print("🔄 বাংলাদেশ পপুলার ক্যাটাগরি ফিল্টার করা হচ্ছে...")

    candidate_channels = []
    seen_urls = set()
    seen_channel_names = set() # একটি চ্যানেল এবং লিংক একবারের বেশি সেভ না হওয়ার জন্য

    for url, country_code in sources:
        try:
            response = requests.get(url, headers=headers, timeout=12)
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

                # লিংক ও নাম ডুপ্লিকেট না হওয়া নিশ্চিতকরণ
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

    print(f"⚡ মোট {len(candidate_channels)} টি প্রফেশনাল ইউনিক চ্যানেল ফিল্টার করা হয়েছে। লাইভ স্ট্রিমিং লিঙ্ক চেক করা হচ্ছে...")

    working_channels = []
    
    with ThreadPoolExecutor(max_workers=80) as executor:
        futures = [executor.submit(check_single_stream, item) for item in candidate_channels]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_channels.append(result)

    # ক্যাটাগরি ক্রম অনুযায়ী সাজানো
    working_channels.sort(key=lambda x: (x[1][0], x[0]['name'].lower()))

    # ৩০০টি ইউনিক পপুলার চ্যানলের লিমিট
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

    print(f"\n✅ OTT স্টাইলের প্লেলিস্ট পুরোপুরি রেডি!")
    print(f"📌 মোট ইউনিক স্যাটেলাইট চ্যানেল সংখ্যা: {total_count} টি")

if __name__ == "__main__":
    fetch_and_generate_playlist()
