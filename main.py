import requests
import json
import re

def clean_channel_name(name):
    # ব্র্যাকেট (), [], {} এবং ভেতরের লেখা মুছে পরিষ্কার নাম তৈরি করা
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

    # ১. বাংলাদেশ (গ্রুপ টাইটেল বা সোর্স অনুযায়ী)
    if 'bangladesh' in group or channel.get('source_country') == 'bd':
        # ABP Ananda, Sangeet Bangla বা UK ভার্সন ফিল্টার
        if not any(ex in name for ex in ['abp', 'uk', 'india', 'sangeet bangla', 'hope channel']):
            return 1

    # ২. স্পোর্টস (গ্রুপ টাইটেল 'sports' হলে)
    if 'sports' in group or any(k in name for k in ['t sports', 'star sports', 'sony sports', 'ten sports', 'ptv sports', 'willow']):
        return 2

    # ৩. কলকাতা/পশ্চিমবঙ্গ বাংলা চ্যানেল
    if 'kolkata' in group or 'west bengal' in group or 'bangla' in group or any(k in name for k in ['star jalsha', 'zee bangla', 'colors bangla', 'abp ananda', 'sony aath', 'sangeet bangla']):
        return 3

    # ৪. ইন্ডিয়া (জাতীয়/অন্যান্য)
    if 'india' in group or channel.get('source_country') == 'in':
        return 4

    # ৫. পাকিস্তান
    if 'pakistan' in group or channel.get('source_country') == 'pk':
        return 5

    return 6

def fetch_channels_by_group():
    # সুনির্দিষ্ট কান্ট্রি সোর্স
    sources = [
        ("https://iptv-org.github.io/iptv/countries/bd.m3u", "bd"),
        ("https://iptv-org.github.io/iptv/languages/ben.m3u", "ben"),
        ("https://iptv-org.github.io/iptv/countries/in.m3u", "in"),
        ("https://iptv-org.github.io/iptv/countries/pk.m3u", "pk")
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 Group-Title ফিল্টার করে চ্যানেল সাজানো হচ্ছে...")

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

                    # group-title এক্সট্র্যাক্ট করা
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

    # সর্টিং অগ্রাধিকার
    channels.sort(key=get_channel_priority)

    # M3U আউটপুট (গ্রুপ টাইটেল সহ সেভ হবে)
    m3u_lines = ["#EXTM3U\n"]
    json_channels = []

    for ch in channels:
        p = get_channel_priority(ch)
        # গ্রুপ টাইটেল পুনর্নির্ধারণ যাতে প্লেয়ারে সুন্দর দেখায়
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

    print(f"✅ সফলভাবে {len(json_channels)} টি চ্যানেল গ্রুপ ট্যাগ সহ সেভ করা হয়েছে!")

if __name__ == "__main__":
    fetch_channels_by_group()
