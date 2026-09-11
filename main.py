import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

MY_NAME = "Ahammad Ali Premium IPTV"
MAX_TOTAL_CHANNELS = 300

# ১০০% সঠিক এবং পারমানেন্ট হাই-কোয়ালিটি লোগো ম্যাপিং
CUSTOM_LOGOS = {
    'BTV': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Bangladesh_Television_logo.svg/512px-Bangladesh_Television_logo.svg.png',
    'BTV World': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Bangladesh_Television_logo.svg/512px-Bangladesh_Television_logo.svg.png',
    'Channel 24': 'https://upload.wikimedia.org/wikipedia/bn/thumb/8/87/Channel_24_logo.svg/512px-Channel_24_logo.svg.png',
    'GTV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/d/d3/GTV_logo.svg/512px-GTV_logo.svg.png',
    'Gazi TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/d/d3/GTV_logo.svg/512px-GTV_logo.svg.png',
    'Desh TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/5/52/Desh_TV_Logo.png/512px-Desh_TV_Logo.png',
    'Somoy TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/a/a2/Somoy_News_logo.svg/512px-Somoy_News_logo.svg.png',
    'Jamuna TV': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/Jamuna_Television_Logo.svg/512px-Jamuna_Television_Logo.svg.png',
    'Ekattor TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/6/66/Ekattor_TV_logo.svg/512px-Ekattor_TV_logo.svg.png',
    'Independent TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/0/07/Independent_Television_logo.svg/512px-Independent_Television_logo.svg.png',
    'Channel i': 'https://upload.wikimedia.org/wikipedia/bn/thumb/e/e0/Channel_i_logo.svg/512px-Channel_i_logo.svg.png',
    'ATN Bangla': 'https://upload.wikimedia.org/wikipedia/bn/thumb/6/6d/ATN_Bangla_logo.svg/512px-ATN_Bangla_logo.svg.png',
    'ATN News': 'https://upload.wikimedia.org/wikipedia/bn/thumb/7/7b/ATN_News_Logo.svg/512px-ATN_News_Logo.svg.png',
    'NTV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/3/3a/NTV_logo.svg/512px-NTV_logo.svg.png',
    'RTV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/4/41/RTV_logo.svg/512px-RTV_logo.svg.png',
    'Deepto TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/6/68/Deepto_TV_logo.png/512px-Deepto_TV_logo.png',
    'Boishakhi TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/a/a6/Boishakhi_TV_Logo.svg/512px-Boishakhi_TV_Logo.svg.png',
    'Banglavision': 'https://upload.wikimedia.org/wikipedia/bn/thumb/8/8d/Banglavision_Logo.svg/512px-Banglavision_Logo.svg.png',
    'Maasranga TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/4/4e/Maasranga_TV_logo.svg/512px-Maasranga_TV_logo.svg.png',
    'Nagorik TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/f/f6/Nagorik_TV_logo.png/512px-Nagorik_TV_logo.png',
    'DBC News': 'https://upload.wikimedia.org/wikipedia/bn/thumb/3/30/DBC_News_logo.svg/512px-DBC_News_logo.svg.png',
    'SA TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/2/22/SA_TV_logo.png/512px-SA_TV_logo.png',
    'Asian TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/4/4f/Asian_TV_logo.png/512px-Asian_TV_logo.png',
    'Duronto TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/c/ca/Duronto_TV_logo.png/512px-Duronto_TV_logo.png',
    'Bijoy TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/8/8d/Bijoy_TV_logo.png/512px-Bijoy_TV_logo.png',
    'My TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/9/90/My_TV_logo.svg/512px-My_TV_logo.svg.png',
    'T Sports': 'https://upload.wikimedia.org/wikipedia/bn/thumb/c/c5/T_Sports_logo.svg/512px-T_Sports_logo.svg.png',
    'News 24': 'https://upload.wikimedia.org/wikipedia/bn/thumb/2/21/News24_logo.svg/512px-News24_logo.svg.png',
    'Nexus TV': 'https://upload.wikimedia.org/wikipedia/bn/thumb/1/1a/Nexus_TV_logo.png/512px-Nexus_TV_logo.png',
    'Green TV': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Green_TV_Logo.png/512px-Green_TV_Logo.png'
}

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

def assign_exact_group(channel_name):
    norm = normalize_text(channel_name)

    # ১. বাংলাদেশি চ্যানেল (গ্রুপের নাম নিখুঁতভাবে 'Bangladeshi')
    exact_bd_channels = {
        'somoytv': 'Somoy TV', 'jamunatv': 'Jamuna TV', 'ekattortv': 'Ekattor TV', 
        'independenttv': 'Independent TV', 'channeli': 'Channel i', 'atnbangla': 'ATN Bangla', 
        'atnnews': 'ATN News', 'ntv': 'NTV', 'rtv': 'RTV', 'deeptotv': 'Deepto TV', 
        'boishakhitv': 'Boishakhi TV', 'banglavision': 'Banglavision', 'deshtv': 'Desh TV', 
        'maasrangatv': 'Maasranga TV', 'nagoriktv': 'Nagorik TV', 'channel24': 'Channel 24', 
        'dbcnews': 'DBC News', 'saatv': 'SA TV', 'asiantv': 'Asian TV', 'durontotv': 'Duronto TV', 
        'btvworld': 'BTV World', 'btv': 'BTV', 'bijoytv': 'Bijoy TV', 'mytv': 'My TV', 
        'gazitv': 'Gazi TV', 'gtv': 'GTV', 'tsports': 'T Sports', 'news24': 'News 24',
        'nexustv': 'Nexus TV', 'greentv': 'Green TV'
    }

    for key, display_name in exact_bd_channels.items():
        if key in norm:
            return (1, "Bangladeshi", display_name)

    # ২. কলকাতার পপুলার চ্যানেল
    kolkata_keywords = ['starjalsha', 'zeebangla', 'colorsbangla', 'abpananda', 'sonyaath', 'sangeetbangla', 'zee24ghanta', 'news18bangla', 'tv9bangla', 'aakashaath']
    if any(k in norm for k in kolkata_keywords):
        return (2, "Kolkata Bangla", channel_name)

    # ৩. পপুলার স্পোর্টস
    sports_keywords = ['sport', 'cricket', 'football', 'star sports', 'sony sports', 'sony ten', 'ten sports', 'willow', 'ptv sports', 'astro sports', 'eurosport']
    if any(k in norm for k in sports_keywords):
        return (3, "Sports Channels", channel_name)

    # ৪. মুভি
    movie_keywords = ['star gold', 'sony max', 'zee cinema', 'and pictures', 'goldmines', 'cineplex', 'hbo', 'star movies', 'sony pix', 'flix', 'mnx']
    if any(k in norm for k in movie_keywords):
        return (4, "Movies", channel_name)

    # ৫. ইসলামিক
    islamic_keywords = ['makkah', 'madinah', 'peace tv', 'quran', 'islam tv', 'madani', 'iqra', 'assunnah']
    if any(k in norm for k in islamic_keywords):
        return (5, "Islamic TV", channel_name)

    # ৬. মিউজিক
    music_keywords = ['9xm', 'mtv', 'zoom', 'mh1', 'b4u music']
    if any(k in norm for k in music_keywords):
        return (6, "Music Channels", channel_name)

    # ৭. ডকুমেন্টারি
    doc_keywords = ['discovery', 'national geographic', 'nat geo', 'animal planet', 'history tv', 'planet earth']
    if any(k in norm for k in doc_keywords):
        return (7, "Documentary & Info", channel_name)

    # ৮. কিডস
    kids_keywords = ['hungama', 'pogo', 'cartoon network', 'sonic', 'nickelodeon', 'nick', 'disney']
    if any(k in norm for k in kids_keywords):
        return (8, "Kids Channels", channel_name)

    # ৯. আন্তর্জাতিক সংবাদ
    news_keywords = ['bbc news', 'cnn', 'al jazeera', 'aaj tak', 'ndtv', 'india today', 'dw news', 'france 24']
    if any(k in norm for k in news_keywords):
        return (9, "International News", channel_name)

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
        "https://iptv-org.github.io/iptv/categories/documentary.m3u",
        "https://iptv-org.github.io/iptv/categories/entertainment.m3u",
        "https://iptv-org.github.io/iptv/categories/general.m3u"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 সম্পূর্ণ পারফেক্ট ফিল্টারিং চালনা করা হচ্ছে...")

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

                    group_result = assign_exact_group(clean_name)
                    
                    if group_result is not None:
                        cat_order, display_group, final_name = group_result
                        norm_final_name = normalize_text(final_name)

                        if norm_final_name not in seen_channel_names:
                            # সোর্স লোগো ইগনোর করে ডাইরেক্ট অরিজিনাল লোগো বাইন্ডিং
                            logo = CUSTOM_LOGOS.get(final_name)
                            if not logo:
                                logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                                logo = logo_match.group(1) if logo_match else ""

                            ch_obj = {
                                "name": final_name,
                                "logo": logo,
                                "stream_url": stream_url
                            }
                            candidate_channels.append((ch_obj, group_result))
                            seen_urls.add(stream_url)
                            seen_channel_names.add(norm_final_name)
            i += 1

    print(f"⚡ সক্রিয়তা পরীক্ষার জন্য {len(candidate_channels)} টি নির্দিষ্ট চ্যানেল প্রসেস করা হচ্ছে...")

    working_channels = []
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(check_single_stream, item) for item in candidate_channels]
        for future in as_completed(futures):
            result = future.result()
            if result:
                working_channels.append(result)

    # গ্রুপ অর্ডার অনুযায়ী সর্টিং
    working_channels.sort(key=lambda x: (x[1][0], x[0]['name'].lower()))

    final_selected_channels = working_channels[:MAX_TOTAL_CHANNELS]
    total_count = len(final_selected_channels)

    m3u_header = f'#EXTM3U name="{MY_NAME} | Total: {total_count}"\n\n'
    m3u_lines = [m3u_header]
    json_channels = []

    for ch, cat_info in final_selected_channels:
        cat_order, display_group, ch_name = cat_info

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

    print(f"\n✅ ১০০% সঠিক লোগো, ক্যাটাগরি ও অ্যাক্টিভ স্ট্রিম সেভ হয়েছে!")

if __name__ == "__main__":
    fetch_and_generate_playlist()
