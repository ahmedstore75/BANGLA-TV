import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

MY_NAME = "Ahammad Ali Premium IPTV"
MAX_TOTAL_CHANNELS = 300

def clean_channel_name(name):
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def normalize_text(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def check_single_stream(item):
    ch_obj, cat_info = item
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

def get_group_only(channel_name):
    norm = normalize_text(channel_name)

    # ১. বাংলাদেশি টিভি (শুধু গ্রুপ নির্ধারণ হবে, নাম পরিবর্তন হবে না)
    bd_keywords = [
        'somoy', 'jamuna', 'ekattor', 'independent', 'channeli', 'atnbangla', 
        'atnnews', 'ntv', 'rtv', 'deepto', 'boishakhi', 'banglavision', 'deshtv', 
        'maasranga', 'nagorik', 'channel24', 'dbcnews', 'satv', 'asiantv', 'duronto', 
        'btv', 'bijoytv', 'mytv', 'gazitv', 'gtv', 'tsports', 'news24', 'nexus', 'greentv'
    ]
    if any(k in norm for k in bd_keywords):
        return (1, "Bangladeshi")

    # ২. কলকাতার বাংলা
    kolkata_keywords = ['starjalsha', 'zeebangla', 'colorsbangla', 'abpananda', 'sonyaath', 'sangeetbangla', 'zee24ghanta', 'news18bangla', 'tv9bangla', 'aakashaath']
    if any(k in norm for k in kolkata_keywords):
        return (2, "Kolkata Bangla")

    # ৩. স্পোর্টস
    sports_keywords = ['sport', 'cricket', 'football', 'star sports', 'sony sports', 'sony ten', 'ten sports', 'willow', 'ptv sports', 'astro sports', 'eurosport']
    if any(k in norm for k in sports_keywords):
        return (3, "Sports Channels")

    # ৪. মুভি
    movie_keywords = ['star gold', 'sony max', 'zee cinema', 'and pictures', 'goldmines', 'cineplex', 'hbo', 'star movies', 'sony pix', 'flix', 'mnx']
    if any(k in norm for k in movie_keywords):
        return (4, "Movies")

    # ৫. ইসলামিক
    islamic_keywords = ['makkah', 'madinah', 'peace tv', 'quran', 'islam tv', 'madani', 'iqra', 'assunnah']
    if any(k in norm for k in islamic_keywords):
        return (5, "Islamic TV")

    # ৬. মিউজিক
    music_keywords = ['9xm', 'mtv', 'zoom', 'mh1', 'b4u music']
    if any(k in norm for k in music_keywords):
        return (6, "Music Channels")

    # ৭. ডকুমেন্টারি
    doc_keywords = ['discovery', 'national geographic', 'nat geo', 'animal planet', 'history tv', 'planet earth']
    if any(k in norm for k in doc_keywords):
        return (7, "Documentary & Info")

    # ৮. কিডস
    kids_keywords = ['hungama', 'pogo', 'cartoon network', 'sonic', 'nickelodeon', 'nick', 'disney']
    if any(k in norm for k in kids_keywords):
        return (8, "Kids Channels")

    # ৯. আন্তর্জাতিক নিউজ
    news_keywords = ['bbc news', 'cnn', 'al jazeera', 'aaj tak', 'ndtv', 'india today', 'dw news', 'france 24']
    if any(k in norm for k in news_keywords):
        return (9, "International News")

    return None

def fetch_and_generate_playlist():
    sources = [
        "https://iptv-org.github.io/iptv/languages/ben.m3u",
        "https://iptv-org.github.io/iptv/countries/in.m3u",
        "https://iptv-org.github.io/iptv/categories/sports.m3u",
        "https://iptv-org.github.io/iptv/categories/news.m3u",
        "https://iptv-org.github.io/iptv/categories/religious.m3u",
        "https://iptv-org.github.io/iptv/categories/movies.m3u",
        "https://iptv-org.github.io/iptv/categories/animation.m3u",
        "https://iptv-org.github.io/iptv/categories/documentary.m3u",
        "https://iptv-org.github.io/iptv/categories/entertainment.m3u",
        "https://iptv-org.github.io/iptv/categories/general.m3u"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 সোর্সের অরিজিনাল নাম ও লোগো বজায় রেখে জেনারেট হচ্ছে...")

    candidate_channels = []
    seen_urls = set()
    seen_channel_names = set()

    for url in sources:
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
                    # সোর্সের নাম এবং লোগো হুবহু সংগ্রহ
                    raw_name = info_line.split(",")[-1].strip() if "," in info_line else "Unknown Channel"
                    original_name = clean_channel_name(raw_name)

                    group_result = get_group_only(original_name)
                    
                    if group_result is not None:
                        norm_name = normalize_text(original_name)

                        if norm_name not in seen_channel_names:
                            logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                            logo = logo_match.group(1) if logo_match else ""

                            ch_obj = {
                                "name": original_name, # অরিজিনাল নাম অপরিবর্তিত
                                "logo": logo,          # অরিজিনাল লোগো লিঙ্ক অপরিবর্তিত
                                "stream_url": stream_url
                            }
                            candidate_channels.append((ch_obj, group_result))
                            seen_urls.add(stream_url)
                            seen_channel_names.add(norm_name)
            i += 1

    print(f"⚡ সক্রিয়তার জন্য {len(candidate_channels)} টি চ্যানেল চেক হচ্ছে...")

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

    for ch, cat_info in final_selected_channels:
        cat_order, display_group = cat_info

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

    print(f"\n✅ ১০০% অরিজিনাল নাম, লোগো এবং সঠিক গ্রুপ নিয়ে ফাইল সেভ হয়েছে!")

if __name__ == "__main__":
    fetch_and_generate_playlist()
