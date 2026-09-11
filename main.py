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

def determine_new_group(channel_name):
    norm_name = normalize_text(channel_name)

    # ১. বাংলাদেশি টিভি (ম্যানুয়ালি নির্ধারিত অরিজিনাল লিস্ট)
    bd_list = [
        'somoy', 'jamuna', 'ekattor', 'independent', 'channeli', 'atnbangla', 'atnnews', 
        'ntv', 'rtv', 'deepto', 'boishakhi', 'banglavision', 'deshtv', 'maasranga', 
        'nagorik', 'channel24', 'dbcnews', 'bvnews', 'saatv', 'asiantv', 'ebangla', 
        'duronto', 'btv', 'btvworld', 'bijoytv', 'mytv', 'gazitv', 'gtv', 'tsports', 'news24'
    ]
    if any(k in norm_name for k in bd_list):
        return (1, "01. Bangladeshi TV")

    # ২. স্পোর্টস চ্যানেল
    sports_list = ['tsports', 'gtv', 'gazitv', 'starsports', 'sonysports', 'sonyten', 'tensports', 'sports18', 'willow', 'ptvsports', 'astrosports', 'skysports', 'eurosport']
    if any(sp in norm_name for sp in sports_list):
        return (2, "02. Sports Channels")

    # ৩. ইন্ডিয়ান বাংলা
    kolkata_list = ['starjalsha', 'zeebangla', 'colorsbangla', 'abpananda', 'sonyaath', 'sangeetbangla', 'zee24ghanta', 'news18bangla', 'tv9bangla', 'aakashaath']
    if any(k in norm_name for k in kolkata_list):
        return (3, "03. Kolkata Bangla")

    # ৪. মুভি (ইন্ডিয়ান ও ইংলিশ)
    movie_list = ['stargold', 'sonymax', 'zeecinema', 'andpictures', 'goldmines', 'b4umovies', 'colorscineplex', 'hbo', 'starmovies', 'sonypix', 'moviesnow', 'flix', 'mnx', 'wb', 'paramount', 'axn']
    if any(m in norm_name for m in movie_list):
        return (4, "04. Indian & English Movies")

    # ৫. ইসলামিক টিভি
    islamic_list = ['makkah', 'madinah', 'peacetv', 'quran', 'islam', 'madani', 'iqra', 'alhuda', 'sunnah', 'assunnah']
    if any(k in norm_name for k in islamic_list):
        return (5, "05. Islamic TV")

    # ৬. মিউজিক চ্যানেল
    music_list = ['9xm', 'mtv', 'zoom', 'b4umusic', 'mh1', '9xjalwa']
    if any(k in norm_name for k in music_list):
        return (6, "06. Music Channels")

    # ৭. ডকুমেন্টারি ও ইনফরমেশন
    doc_list = ['discovery', 'nationalgeographic', 'natgeo', 'animalplanet', 'historytv', 'planetearth', 'investigation']
    if any(k in norm_name for k in doc_list):
        return (7, "07. Documentary & Info")

    # ৮. কিডস চ্যানেল
    kids_list = ['hungama', 'superhungama', 'pogo', 'cartoonnetwork', 'sonic', 'nickelodeon', 'nick', 'disney']
    if any(k in norm_name for k in kids_list):
        return (8, "08. Kids Channels")

    # ৯. ইন্টারন্যাশনাল নিউজ
    news_list = ['bbcnews', 'cnn', 'aljazeera', 'aajtak', 'ndtv', 'indiatoday', 'dwnews', 'france24']
    if any(news in norm_name for news in news_list):
        return (9, "09. International News")

    # আপনার ক্যাটাগরির সাথে না মিললে চ্যানেলটি বাদ পড়বে
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

    print("🔄 নতুন কাস্টম গ্রুপ টাইটেল ফিল্টারিং চালু হচ্ছে...")

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
                        # আমি নিজে নাম দেখে নতুন গ্রুপ গ্রুপ এসাইন করছি
                        res = determine_new_group(clean_name)
                        
                        if res is not None:
                            logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                            logo = logo_match.group(1) if logo_match else ""

                            ch_obj = {
                                "name": clean_name if clean_name else raw_name,
                                "logo": logo,
                                "stream_url": stream_url
                            }
                            candidate_channels.append((ch_obj, res))
                            seen_urls.add(stream_url)
                            seen_channel_names.add(norm_clean_name)
            i += 1

    print(f"⚡ ফিল্টারকৃত {len(candidate_channels)} টি চ্যানেল টেস্ট করা হচ্ছে...")

    working_channels = []
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(check_single_stream, item) for item in candidate_channels]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_channels.append(result)

    # ১ থেকে ৯ ক্যাটাগরি সিকোয়েন্স অনুযায়ী সাজানো
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

    print(f"\n✅ সম্পূর্ণ নতুন গ্রুপ টাইটেল সহ প্লেলিস্ট তৈরি সম্পন্ন হয়েছে!")

if __name__ == "__main__":
    fetch_and_generate_playlist()
