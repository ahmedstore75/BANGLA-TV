import json
import re
import requests
from concurrent.futures import ThreadPoolExecutor


def clean_channel_name(name):
    cleaned = re.sub(r"[\(\[\{].*?[\)\]\}]", "", name)
    return cleaned.strip()


def is_stream_working(url):
    """স্ট্রিমিং লিংক চালু/ওয়ার্কিং আছে কিনা তা চেক করার ফাংশন"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        # দ্রুত চেক করার জন্য timeout কম (5 সেকেন্ড) রাখা হয়েছে
        response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return True
        # কিছু সার্ভার HEAD রিকোয়েস্ট ব্লক করে, তাই GET দিয়ে পুনরায় চেষ্টা
        response = requests.get(url, headers=headers, timeout=5, stream=True)
        return response.status_code == 200
    except Exception:
        return False


def get_channel_priority(channel):
    name = channel["name"].lower()
    category = channel["category"].lower()
    country = channel["country"].lower()

    # তেলেগু, তামিল, কান্নাডা বা অন্যান্য সাউথ ইন্ডিয়ান চ্যানেল বাদ দেওয়া
    unwanted_keywords = [
        "telugu", "tamil", "kannada", "malayalam", "mora", "tv9 telugu", 
        "zee telugu", "star maa", "etv", "gemini", "sakshi", "v6", "ntv telugu"
    ]
    if any(u in name for u in unwanted_keywords):
        return 99

    # ১. বাংলাদেশী সকল চ্যানেল (সবার উপরে)
    bd_keywords = [
        "btv", "somoy", "channel i", "ekattor", "jamuna", "rtv", "atn", "ntv", 
        "independent", "bangla vision", "dbc", "deepto", "asian tv", "desh tv", 
        "nagorik", "boishakhi", "maasranga", "bijoy", "gtv", "gazitv", "bangladesh",
        "duronto", "saatv", "sangeet bangla", "news24", "channel 24"
    ]
    if country == "bd" or any(k in name for k in bd_keywords) or "bangladesh" in category:
        return 1

    # ২. পপুলার স্পোর্টস চ্যানেল (বাংলাদেশ, ভারত, পাকিস্তান ও গ্লোবাল)
    sports_keywords = [
        "sport", "sports", "t sports", "tsports", "star sports", "sony ten", 
        "sony liv", "willow", "ptv sports", "ten sports", "geo super", "a sports", 
        "eurosport", "sky sports", "bein sports", "supersport", "espn", "fox sports"
    ]
    if any(k in name for k in sports_keywords) or "sports" in category:
        return 2

    # ৩. কলকাতার পপুলার বাংলা চ্যানেল
    kolkata_keywords = [
        "star jalsha", "zee bangla", "colors bangla", "sony aath", "rupashi bangla", 
        "news18 bangla", "tv9 bangla", "khabor 365", "calcutta", "kolkata", "bangla"
    ]
    if any(k in name for k in kolkata_keywords):
        return 3

    # ৪. পপুলার হিন্দি চ্যানেল
    hindi_keywords = [
        "zee tv", "zee cinema", "zee news", "star plus", "star bharat", "star gold", 
        "sony sab", "sony tv", "sony max", "colors tv", "colors cineplex", "aaj tak", 
        "ndtv india", "india tv", "bindass", "pogo", "hungama", "discovery", "nat geo", 
        "mtv india", "nickelodeon india"
    ]
    if any(k in name for k in hindi_keywords) or "hindi" in name:
        return 4

    # ৫. পপুলার পাকিস্তানি চ্যানেল
    pak_keywords = ["geo news", "geo tv", "ary digital", "ary news", "hum tv", "ptv", "express news"]
    if country == "pk" and any(k in name for k in pak_keywords):
        return 5

    # অন্যান্য বা অনাকাঙ্ক্ষিত চ্যানেল বাতিল
    return 99


def process_channel(ch_obj):
    """লিংক চেক করে সচল চ্যানেলগুলো রিটার্ন করার হেল্পার"""
    if is_stream_working(ch_obj["stream_url"]):
        return ch_obj
    return None


def fetch_specific_country_channels():
    sources = [
        "https://iptv-org.github.io/iptv/countries/bd.m3u",
        "https://iptv-org.github.io/iptv/countries/in.m3u",
        "https://iptv-org.github.io/iptv/countries/pk.m3u",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print("🔄 সোর্স ফাইল থেকে চ্যানেল সংগৃহীত হচ্ছে...")

    raw_channels = []
    seen_urls = set()

    for url in sources:
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
                    raw_name = info_line.split(",")[-1].strip() if "," in info_line else "Unknown"
                    clean_name = clean_channel_name(raw_name)

                    logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                    logo = logo_match.group(1) if logo_match else ""

                    group_match = re.search(r'group-title="([^"]*)"', info_line)
                    category = group_match.group(1) if group_match else "General"

                    country_match = re.search(r'tvg-country="([^"]*)"', info_line)
                    country = country_match.group(1) if country_match else ""

                    ch_obj = {
                        "name": clean_name,
                        "logo": logo,
                        "category": category,
                        "country": country,
                        "stream_url": stream_url,
                    }

                    priority = get_channel_priority(ch_obj)

                    if priority != 99:
                        ch_obj["priority"] = priority
                        raw_channels.append(ch_obj)
                        seen_urls.add(stream_url)
            i += 1

    print(f"🔎 ফিল্টার শেষে পাওয়া মোট চ্যানেল: {len(raw_channels)}")
    print("⚡ স্ট্রিমিং লিঙ্ক সক্রিয় (Working) আছে কিনা তা চেক করা হচ্ছে (দয়া করে অপেক্ষা করুন)...")

    working_channels = []
    # থ্রেড পুলের সাহায্যে দ্রুত একাধিক লিঙ্ক চেক করা হচ্ছে
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(process_channel, raw_channels)
        for res in results:
            if res:
                working_channels.append(res)

    print(f"✅ সক্রিয় (Working) চ্যানেল পাওয়া গেছে: {len(working_channels)}")

    # সাজানোর অর্ডারিং: ১. বাংলাদেশ -> ২. স্পোর্টস -> ৩. কলকাতা বাংলা -> ৪. হিন্দি -> ৫. পাকিস্তান
    working_channels.sort(key=lambda x: x["priority"])

    # ফাইল সেভ করার আগে অপ্রয়োজনীয় প্রোপার্টি মুছে ফেলা
    for ch in working_channels:
        ch.pop("priority", None)
        ch.pop("country", None)

    # M3U ফাইলে সংরক্ষণ
    m3u_lines = ["#EXTM3U\n"]
    for ch in working_channels:
        m3u_lines.append(
            f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["category"]}",{ch["name"]}\n{ch["stream_url"]}\n'
        )

    # JSON ফাইলে সংরক্ষণ
    json_data = {
        "status": "success",
        "total_channels": len(working_channels),
        "channels": working_channels,
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)

    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)

    print("🎉 সফলভাবে `playlist.json` এবং `playlist.m3u` তৈরি ও ফিল্টার করা হয়েছে!")


if __name__ == "__main__":
    fetch_specific_country_channels()
