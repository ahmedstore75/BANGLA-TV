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
    ch_obj, category_info = item
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

def match_and_assign_group(channel_name):
    norm_name = normalize_text(channel_name)

    # ১. বাংলাদেশি টিভি (জনপ্রিয় চ্যানেলগুলোর তালিকা - অগ্রাধিকারের ক্রমানুসারে)
    bd_popular = [
        'somoytv', 'jamunatv', 'ekattortv', 'independenttv', 'channeli', 'atnbangla', 'atnnews', 
        'ntv', 'rtv', 'deeptotv', 'boishakhitv', 'banglavision', 'deshtv', 'maasrangatv', 
        'nagoriktv', 'channel24', 'dbcnews', 'saatv', 'asiantv', 'durontotv', 'btv', 'btvworld', 'bijoytv', 'mytv', 'news24'
    ]
    for idx, key in enumerate(bd_popular):
        if key in norm_name:
            return (1, idx, "01. Bangladeshi TV")

    # ২. স্পোর্টস চ্যানেল
    sports_popular = ['tsports', 'gazitv', 'gtv', 'starsports', 'sonysports', 'sonyten', 'tensports', 'sports18', 'willowtv', 'ptvsports', 'astrosports']
    for idx, key in enumerate(sports_popular):
        if key in norm_name:
            return (2, idx, "02. Sports Channels")

    # ৩. ইন্ডিয়ান বাংলা
    kolkata_popular = ['starjalsha', 'zeebangla', 'colorsbangla', 'abpananda', 'sonyaath', 'sangeetbangla', 'zee24ghanta', 'news18bangla', 'tv9bangla', 'aakashaath']
    for idx, key in enumerate(kolkata_popular):
        if key in norm_name:
            return (3, idx, "03. Kolkata Bangla")

    # ৪. মুভি চ্যানেল
    movie_popular = ['stargold', 'sonymax', 'zeecinema', 'andpictures', 'goldmines', 'b4umovies', 'colorscineplex', 'hbo', 'starmovies', 'sonypix', 'moviesnow', 'flix', 'mnx']
    for idx, key in enumerate(movie_popular):
        if key in norm_name:
            return (4, idx, "04. Indian & English Movies")

    # ৫. ইসলামিক টিভি
    islamic_popular = ['makkah', 'madinah', 'peacetv', 'quran', 'islamtv', 'madani', 'iqra', 'assunnah']
    for idx, key in enumerate(islamic_popular):
        if key in norm_name:
            return (5, idx, "05. Islamic TV")

    # ৬. মিউজিক চ্যানেল
    music_popular = ['9xm', 'mtv', 'zoom', 'b4umusic', 'mh1']
    for idx, key in enumerate(music_popular):
        if key in norm_name:
            return (6, idx, "06. Music Channels")

    # ৭. ডকুমেন্টারি ও তথ্য
    doc_popular = ['discovery', 'nationalgeographic', 'natgeo', 'animalplanet', 'historytv', 'planetearth']
    for idx, key in enumerate(doc_popular):
        if key in norm_name:
            return (7, idx, "07. Documentary & Info")

    # ৮. কিডস চ্যানেল
    kids_popular = ['hungama', 'superhungama', 'pogo', 'cartoonnetwork', 'sonic', 'nickelodeon', 'nick', 'disney']
    for idx, key in enumerate(kids_popular):
        if key in norm_name:
            return (8, idx, "08. Kids Channels")

    # ৯. ইন্টারন্যাশনাল নিউজ
    news_popular = ['bbcnews', 'cnn', 'aljazeera', 'aajtak', 'ndtv', 'indiatoday', 'dwnews', 'france24']
    for idx, key in enumerate(news_popular):
        if key in norm_name:
            return (9, idx, "09. International News")

    # তালিকাভুক্ত নয় এমন চ্যানেল বাদ যাবে
    return None

def fetch_and_generate_playlist():
    sources = [
        "https://iptv-org.github.io/iptv/countries/bd.m3u",
        "https://iptv-org.github.io/iptv/languages/ben.m3u",
        "https://iptv-org.github.io/iptv/countries/in.m3u",
        "https://iptv-org.github.io/iptv/categories/sports.m3u",
        "https://iptv-org.github.io/iptv/categories/news.m3u",
        "https://iptv-org.github.io/iptv/categories/religious.m3u",
        "https://iptv-org.github.io/iptv/categories/movies.m3u",
        "https://iptv-org.github.io/iptv/categories/animation.m3u",
        "https://iptv-org.github.io/iptv/categories/documentary.m3u"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 পপুলার চ্যানেল ফিল্টারিং চালু হচ্ছে...")

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
                    raw_name = info_line.split(",")[-1].strip() if "," in info_line else "Unknown Channel"
                    clean_name = clean_channel_name(raw_name)
                    norm_clean_name = normalize_text(clean_name)

                    if norm_clean_name not in seen_channel_names:
                        category_info = match_and_assign_group(clean_name)
                        
                        if category_info is not None:
                            logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                            logo = logo_match.group(1) if logo_match else ""

                            ch_obj = {
                                "name": clean_name if clean_name else raw_name,
                                "logo": logo,
                                "stream_url": stream_url
                            }
                            candidate_channels.append((ch_obj, category_info))
                            seen_urls.add(stream_url)
                            seen_channel_names.add(norm_clean_name)
            i += 1

    print(f"⚡ ফিল্টার শেষে {len(candidate_channels)} টি মূল পপুলার চ্যানেল টেস্ট করা হচ্ছে...")

    working_channels = []
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(check_single_stream, item) for item in candidate_channels]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_channels.append(result)

    # ১. ক্যাটাগরি অর্ডার (1-9) এবং ২. চ্যানেলের পপুলারিটি পজিশন অনুযায়ী সর্টিং
    working_channels.sort(key=lambda x: (x[1][0], x[1][1]))

    final_selected_channels = working_channels[:MAX_TOTAL_CHANNELS]
    total_count = len(final_selected_channels)

    m3u_header = f'#EXTM3U name="{MY_NAME} | Total: {total_count}"\n\n'
    m3u_lines = [m3u_header]
    json_channels = []

    for ch, cat_info in final_selected_channels:
        cat_order, pop_order, display_group = cat_info

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

    print(f"\n✅ সফলভাবে পপুলার চ্যানেলগুলো সবার উপরে রেখে প্লেলিস্ট সাজানো হয়েছে!")

if __name__ == "__main__":
    fetch_and_generate_playlist()
