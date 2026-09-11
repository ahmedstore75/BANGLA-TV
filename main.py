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

# চ্যানেলের নাম বিশ্লেষণ করে নতুন গ্রুপ ও পজিশন ঠিক করার ফাংশন
def auto_detect_group_by_name(channel_name):
    norm = normalize_text(channel_name)

    # ১. বাংলাদেশি টিভি (নামে এই শব্দগুলো থাকতেই হবে)
    bd_keywords = ['somoy', 'jamuna', 'ekattor', 'independent', 'channeli', 'atn', 'ntv', 'rtv', 'deepto', 'boishakhi', 'banglavision', 'deshtv', 'maasranga', 'nagorik', 'channel24', 'dbc', 'saatv', 'asiantv', 'duronto', 'btv', 'bijoy', 'mytv', 'gazi', 'gtv', 'tsports', 'news24', 'bangla']
    
    # কিন্তু ইন্ডিয়ান বাংলা যেন বাংলাদেশি গ্রুপে না ঢুকে যায়
    indian_bangla_indicators = ['jalsha', 'zeebangla', 'colorsbangla', 'abpananda', 'sonyaath', 'sangeetbangla', 'zee24ghanta', 'news18bangla', 'tv9bangla', 'aakash']
    
    if any(k in norm for k in indian_bangla_indicators):
        return (3, "03. Kolkata Bangla")

    if any(k in norm for k in bd_keywords):
        return (1, "01. Bangladeshi TV")

    # ২. স্পোর্টস চ্যানেল
    sports_keywords = ['sport', 'sports', 'cricket', 'football', 'ten1', 'ten2', 'ten3', 'starsports', 'sonysports', 'sonyten', 'willow', 'ptvsports', 'astrosports', 'eurosport', 't sports']
    if any(k in norm for k in sports_keywords):
        return (2, "02. Sports Channels")

    # ৪. মুভি চ্যানেল
    movie_keywords = ['movie', 'movies', 'cinema', 'pictures', 'goldmines', 'cineplex', 'hbo', 'starmovies', 'pix', 'flix', 'mnx', 'action']
    if any(k in norm for k in movie_keywords):
        return (4, "04. Indian & English Movies")

    # ৫. ইসলামিক / ধর্মীয় টিভি
    islamic_keywords = ['makkah', 'madinah', 'peace', 'quran', 'islam', 'madani', 'iqra', 'sunnah', 'alhuda']
    if any(k in norm for k in islamic_keywords):
        return (5, "05. Islamic TV")

    # ৬. মিউজিক চ্যানেল
    music_keywords = ['music', '9xm', 'mtv', 'zoom', 'mh1', 'sangeet']
    if any(k in norm for k in music_keywords):
        return (6, "06. Music Channels")

    # ৭. ডকুমেন্টারি
    doc_keywords = ['discovery', 'nationalgeographic', 'natgeo', 'animalplanet', 'history', 'planet']
    if any(k in norm for k in doc_keywords):
        return (7, "07. Documentary & Info")

    # ৮. কিডস / কার্টুন
    kids_keywords = ['cartoon', 'hungama', 'pogo', 'sonic', 'nickelodeon', 'nick', 'disney', 'kids']
    if any(k in norm for k in kids_keywords):
        return (8, "08. Kids Channels")

    # ৯. আন্তর্জাতিক সংবাদ
    news_keywords = ['bbc', 'cnn', 'aljazeera', 'aajtak', 'ndtv', 'indiatoday', 'dwnews', 'france24']
    if any(k in norm for k in news_keywords):
        return (9, "09. International News")

    # কোনো ক্যাটাগরির নামের সাথে না মিললে বাদ দেওয়া হবে (যাতে 30A Lionel বা Al Janoub এর মতো আজেবাজে চ্যানেল না আসে)
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

    print("🔄 চ্যানেলের নাম স্ক্যান করে অটোমেটিক গ্রুপ তৈরি করা হচ্ছে...")

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
                        # নামে কি-ওয়ার্ড স্ক্যান করে গ্রুপ এসাইন
                        group_info = auto_detect_group_by_name(clean_name)
                        
                        if group_info is not None:
                            logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                            logo = logo_match.group(1) if logo_match else ""

                            ch_obj = {
                                "name": clean_name if clean_name else raw_name,
                                "logo": logo,
                                "stream_url": stream_url
                            }
                            candidate_channels.append((ch_obj, group_info))
                            seen_urls.add(stream_url)
                            seen_channel_names.add(norm_clean_name)
            i += 1

    print(f"⚡ নাম বিশ্লেষণ শেষে {len(candidate_channels)} টি সঠিক চ্যানেল প্রসেস করা হচ্ছে...")

    working_channels = []
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(check_single_stream, item) for item in candidate_channels]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_channels.append(result)

    # গ্রুপ ক্রমানুসারে সাজানো
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

    print(f"\n✅ চ্যানেল নাম অনুযায়ী নিখুঁত গ্রুপ তৈরি করে প্লেলিস্ট সেভ করা হয়েছে!")

if __name__ == "__main__":
    fetch_and_generate_playlist()
