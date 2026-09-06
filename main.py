import requests
import json
import re

def clean_channel_name(name):
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def is_excluded_channel(channel):
    name = channel['name'].lower()
    group = channel['group'].lower()
    
    excluded = ['telugu', 'tamil', 'gemini', 'vijay', 'sun tv', 'kalignar', 'etv telugu', 'sakshi']
    if any(k in group for k in ['telugu', 'tamil']) or any(k in name for k in excluded):
        return True
    return False

def categorize_and_prioritize(channel):
    group = channel['group'].lower()
    name = channel['name'].lower()

    # ১. বাংলাদেশ
    if 'bangladesh' in group or channel.get('source_country') == 'bd':
        if not any(ex in name for ex in ['abp', 'uk', 'india', 'sangeet bangla', 'hope channel']):
            bd_popular = ['somoy', 'ekattor', 'jamuna', 'channel i', 'ntv', 'atn bangla', 'rtv', 'independent', 'banglavision', 'dbc news', 'channel 24', 'gtv', 'gazi tv', 'deepto', 'maasranga', 'nagorik', 'boishakhi', 'btv']
            sub_p = 0 if any(pop in name for pop in bd_popular) else 1
            return (1, sub_p, "Bangladeshi TV")

    # ২. স্পোর্টস
    if 'sport' in group or any(k in name for k in ['t sports', 'star sports', 'sony sports', 'sony ten', 'ten sports', 'willow', 'ptv sports', 'dd sports']):
        sports_popular = ['t sports', 'tsports', 'star sports', 'sony sports', 'sony ten', 'ten sports', 'willow']
        sub_p = 0 if any(pop in name for pop in sports_popular) else 1
        return (2, sub_p, "Sports Channels")

    # ৩. কলকাতা বাংলা
    if 'kolkata' in group or 'west bengal' in group or any(k in name for k in ['star jalsha', 'zee bangla', 'colors bangla', 'abp ananda', 'sony aath', 'sangeet bangla']):
        kolkata_popular = ['star jalsha', 'zee bangla', 'abp ananda', 'colors bangla', 'sony aath', 'zee 24 ghanta', 'sangeet bangla']
        sub_p = 0 if any(pop in name for pop in kolkata_popular) else 1
        return (3, sub_p, "Kolkata Bangla")

    # ৪. কিডস (কার্টুন চ্যানেল)
    if 'kid' in group or 'animation' in group or any(k in name for k in ['pogo', 'hungama', 'cartoon network', 'nick', 'disney', 'sonic']):
        return (4, 0, "Kids Channels")

    # ৫. ডকুমেন্টারি
    if 'documentary' in group or any(k in name for k in ['discovery', 'national geographic', 'nat geo', 'history tv', 'animal planet']):
        return (5, 0, "Documentary")

    # ৬. মিউজিক
    if 'music' in group or any(k in name for k in ['mnet', 'mtv', '9xm', 'zoOm', 'music', 'b4u music', 'sangeet']):
        return (6, 0, "Music Channels")

    # ৭. ইন্ডিয়ান চ্যানেল (পপুলারসহ)
    if 'india' in group or channel.get('source_country') == 'in':
        indian_popular = [
            'star plus', 'sony entertainment', 'colors', 'zee tv', 'sab tv', 'star bharat',
            'aaj tak', 'ndtv', 'india today', 'star movies', 'mnx', 'hbo', 'movies now', 
            'sony pix', 'wb', 'star gold', 'sony max', 'zee cinema', 'goldmines', 'goldmine',
            'b4u movies', 'b4u bhojpuri', 'bhojpuri cinema', 'zee anmol'
        ]
        sub_p = 0 if any(pop in name for pop in indian_popular) else 1
        return (7, sub_p, "Indian Channels")

    # ৮. পাকিস্তান / অন্যান্য
    if 'pakistan' in group or channel.get('source_country') == 'pk':
        pak_popular = ['geo tv', 'ary digital', 'hum tv', 'ptv sports', 'geo news', 'ary news', 'samaa']
        sub_p = 0 if any(pop in name for pop in pak_popular) else 1
        return (8, sub_p, "Pakistani Channels")

    # কোনোটিতে না মিললে ডিফল্ট ইন্ডিয়ান ক্যাটাগরিতে যুক্ত হবে (অপ্রয়োজনীয় ক্যাটাগরি এড়াতে)
    return (7, 2, "Indian Channels")

def fetch_channels_by_group():
    sources = [
        ("https://iptv-org.github.io/iptv/countries/bd.m3u", "bd"),
        ("https://iptv-org.github.io/iptv/languages/ben.m3u", "ben"),
        ("https://iptv-org.github.io/iptv/countries/in.m3u", "in"),
        ("https://iptv-org.github.io/iptv/countries/pk.m3u", "pk")
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 ক্যাটাগরি কমিয়ে সুনির্দিষ্ট ৮টি ক্যাটাগরিতে সেভ করা হচ্ছে...")

    channels = []
    seen_urls = set()

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
                        channels.append(ch_obj)
                        seen_urls.add(stream_url)
            i += 1

    # সর্টিং
    channels.sort(key=lambda x: categorize_and_prioritize(x)[:2])

    m3u_lines = ["#EXTM3U\n"]
    json_channels = []

    for ch in channels:
        p, sub_p, display_group = categorize_and_prioritize(ch)

        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{display_group}",{ch["name"]}\n{ch["stream_url"]}\n')
        
        json_channels.append({
            "name": ch["name"],
            "logo": ch["logo"],
            "group": display_group,
            "stream_url": ch["stream_url"]
        })

    # ১. playlist.json সেভ
    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump({"status": "success", "total_channels": len(json_channels), "channels": json_channels}, jf, indent=4, ensure_ascii=False)

    # ২. playlist.m3u সেভ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)

    print(f"✅ ক্যাটাগরি ক্লিন করা শেষ! মোট চ্যানেল: {len(json_channels)}")

if __name__ == "__main__":
    fetch_channels_by_group()
