import requests
import json
import re

def clean_channel_name(name):
    # ব্র্যাকেট (), [], {} এবং ভেতরের লেখা মুছে নাম পরিষ্কার করা
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def is_excluded_channel(channel):
    name = channel['name'].lower()
    group = channel['group'].lower()
    
    # তেলেগু ও তামিল ফিল্টারিং
    excluded = ['telugu', 'tamil', 'gemini', 'vijay', 'sun tv', 'kalignar', 'etv telugu', 'sakshi']
    if any(k in group for k in ['telugu', 'tamil']) or any(k in name for k in excluded):
        return True
    return False

def get_channel_priority(channel):
    group = channel['group'].lower()
    name = channel['name'].lower()

    # ১. বাংলাদেশ (পপুলার চ্যানেলগুলো আগে)
    if 'bangladesh' in group or channel.get('source_country') == 'bd':
        if not any(ex in name for ex in ['abp', 'uk', 'india', 'sangeet bangla', 'hope channel']):
            bd_popular = [
                'somoy', 'ekattor', 'jamuna', 'channel i', 'ntv', 'atn bangla', 'rtv', 
                'independent', 'banglavision', 'dbc news', 'channel 24', 'gtv', 'gazi tv', 
                'deepto', 'maasranga', 'nagorik', 'boishakhi', 'btv'
            ]
            if any(pop in name for pop in bd_popular):
                return (1, 0)
            return (1, 1)

    # ২. স্পোর্টস (পপুলার চ্যানেলগুলো আগে)
    if 'sports' in group or any(k in name for k in ['t sports', 'star sports', 'sony sports', 'sony ten', 'ten sports', 'willow', 'ptv sports', 'dd sports']):
        sports_popular = ['t sports', 'tsports', 'star sports', 'sony sports', 'sony ten', 'ten sports', 'willow']
        if any(pop in name for pop in sports_popular):
            return (2, 0)
        return (2, 1)

    # ৩. কলকাতা/পশ্চিমবঙ্গ (পপুলার চ্যানেলগুলো আগে)
    if 'kolkata' in group or 'west bengal' in group or 'bangla' in group or any(k in name for k in ['star jalsha', 'zee bangla', 'colors bangla', 'abp ananda', 'sony aath', 'sangeet bangla']):
        kolkata_popular = ['star jalsha', 'zee bangla', 'abp ananda', 'colors bangla', 'sony aath', 'zee 24 ghanta', 'sangeet bangla']
        if any(pop in name for pop in kolkata_popular):
            return (3, 0)
        return (3, 1)

    # ৪. ইন্ডিয়ান পপুলার, মুভি ও ভোজপুরি চ্যানেল
    if 'india' in group or channel.get('source_country') == 'in':
        indian_popular = [
            'star plus', 'sony entertainment', 'colors', 'zee tv', 'sab tv', 'star bharat',
            'aaj tak', 'ndtv', 'india today', 'star movies', 'mnx', 'hbo', 'movies now', 
            'sony pix', 'wb', 'star gold', 'sony max', 'zee cinema', 'goldmines', 'goldmine',
            'b4u movies', 'b4u bhojpuri', 'bhojpuri cinema', 'zee anmol', 'pogo', 
            'hungama', 'discovery', 'national geographic'
        ]
        if any(pop in name for pop in indian_popular):
            return (4, 0)
        return (4, 1)

    # ৫. পাকিস্তান (পপুলার চ্যানেলগুলো আগে)
    if 'pakistan' in group or channel.get('source_country') == 'pk':
        pak_popular = ['geo tv', 'ary digital', 'hum tv', 'ptv sports', 'geo news', 'ary news', 'samaa']
        if any(pop in name for pop in pak_popular):
            return (5, 0)
        return (5, 1)

    return (6, 0)

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

    print("🔄 Goldmines, B4U, Bhojpuri Cinema সহ পপুলার চ্যানেল সাজানো হচ্ছে...")

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

    # সর্টিং ফিল্টার প্রয়োগ
    channels.sort(key=get_channel_priority)

    m3u_lines = ["#EXTM3U\n"]
    json_channels = []

    for ch in channels:
        p, sub_p = get_channel_priority(ch)
        
        if p == 1:
            display_group = "Bangladeshi TV"
        elif p == 2:
            display_group = "Sports Channels"
        elif p == 3:
            display_group = "Kolkata Bangla"
        elif p == 4:
            display_group = "Indian Channels"
        elif p == 5:
            display_group = "Pakistani Channels"
        else:
            display_group = ch["group"]

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

    print(f"✅ সফলভাবে {len(json_channels)} টি চ্যানেল সেভ করা হয়েছে!")

if __name__ == "__main__":
    fetch_channels_by_group()
