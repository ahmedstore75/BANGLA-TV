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

    # ১. Bangladeshi TV
    bd_real_channels = [
        'somoy', 'jamuna', 'ekattor', 'independent', 'channel i', 'atn bangla', 'atn news', 
        'ntv', 'rtv', 'deepto', 'boishakhi', 'banglavision', 'desh tv', 'maasranga', 
        'nagorik', 'channel 24', 'dbc news', 'bvnews', 'saatv', 'asian tv', 'ebangla', 'duronto'
    ]
    if channel.get('source_country') == 'bd' or any(normalize_text(k) in norm_name for k in bd_real_channels):
        return (1, "1. Bangladeshi TV")

    # ২. Sports Channels
    sports_keywords = ['tsports', 't sports', 'gtv', 'gazi tv', 'star sports', 'sony sports', 'sony ten', 'ten sports', 'sports18', 'willow', 'ptv sports', 'astro sports']
    if any(normalize_text(sp) in norm_name for sp in sports_keywords):
        return (2, "2. Sports Channels")

    # ৩. Indian Bangla (Kolkata)
    kolkata_popular = ['star jalsha', 'zee bangla', 'colors bangla', 'abp ananda', 'sony aath', 'sangeet bangla', 'zee 24 ghanta', 'news18 bangla', 'tv9 bangla', 'aakash aath']
    if 'kolkata' in group or 'west bengal' in group or any(normalize_text(k) in norm_name for k in kolkata_popular):
        return (3, "3. Kolkata Bangla")

    # ৪. Indian & English Movies
    movie_keywords = [
        'star gold', 'sony max', 'zee cinema', 'and pictures', 'goldmines', 'b4u movies', 'colors cineplex',
        'hbo', 'star movies', 'sony pix', 'movies now', '&flix', 'mnx', 'wb', 'paramount', 'axn'
    ]
    if any(normalize_text(m) in norm_name for m in movie_keywords):
        return (4, "4. Indian & English Movies")

    # ৫. Islamic TV
    islamic_keywords = ['makkah', 'madinah', 'peace tv', 'quran', 'islam', 'madani', 'iqra', 'alhuda']
    if any(k in norm_name for k in islamic_keywords) or 'islamic' in group:
        return (5, "5. Islamic TV")

    # ৬. Music Channels
    music_keywords = ['9xm', 'mtv', 'zoom', 'b4u music', 'sangeet bangla', 'mnet']
    if any(k in norm_name for k in music_keywords):
        return (6, "6. Music Channels")

    # ৭. Documentary & Information
    doc_keywords = ['discovery', 'national geographic', 'nat geo', 'animal planet', 'history tv', 'planet earth']
    if any(normalize_text(k) in norm_name for k in doc_keywords):
        return (7, "7. Documentary & Info")

    # ৮. Kids Channels
    kids_keywords = ['hungama', 'super hungama', 'pogo', 'cartoon network', 'sonic', 'nickelodeon', 'nick', 'disney']
    if any(k in norm_name for k in kids_keywords):
        return (8, "8. Kids Channels")

    # ৯. International News
    global_news = ['bbc news', 'cnn', 'al jazeera', 'aaj tak', 'ndtv', 'india today', 'dw news', 'france 24']
    if any(normalize_text(news) in norm_name for news in global_news):
        return (9, "9. International News")

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

    print("🔄 সোর্স ফেচ করা হচ্ছে...")

    candidate_channels = []
    seen_urls = set()
    seen_channel_names = set()

    for url, country_code in sources:
        try:
            response = requests.get(url, headers=headers, timeout=10)
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

    print(f"⚡ {len(candidate_channels)} টি চ্যানেল প্রসেস করা হচ্ছে...")

    working_channels = []
    
    with ThreadPoolExecutor(max_workers=30) as executor:
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

    print(f"\n✅ প্লেলিস্ট তৈরি সফল হয়েছে! মোট চ্যানেল: {total_count}")

if __name__ == "__main__":
    fetch_and_generate_playlist()
