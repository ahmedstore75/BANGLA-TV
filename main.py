import json
import re
import requests


def clean_channel_name(name):
    # ফার্স্ট, থার্ড এবং কার্লি ব্র্যাকেটের ভেতরের অংশ মুছে ফেলা
    cleaned = re.sub(r"[\(\[\{].*?[\)\]\}]", "", name)
    return cleaned.strip()


def get_channel_priority(channel):
    name = channel["name"].lower()
    category = channel["category"].lower()
    country = channel["country"].lower()

    # ১. বাংলাদেশী সকল চ্যানেল (সবার উপরে থাকবে)
    bd_keywords = [
        "btv",
        "somoy",
        "channel i",
        "ekattor",
        "jamuna",
        "rtv",
        "atn",
        "ntv",
        "independent",
        "bangla vision",
        "dbc",
        "deepto",
        "asian tv",
        "desh tv",
        "nagorik",
        "boishakhi",
        "maasranga",
        "bijoy",
        "gtv",
        "gazitv",
        "bangladesh",
        "duronto",
        "saatv",
        "sangeet bangla",
        "news24",
        "channel 24",
    ]
    if country == "bd" or any(k in name for k in bd_keywords) or "bangladesh" in category:
        return 1

    # ২. স্পোর্টস চ্যানেলগুলো (বাংলাদেশ, পাকিস্তান, ভারত ও গ্লোবাল স্পোর্টস)
    sports_keywords = [
        "sport",
        "sports",
        "t sports",
        "tsports",
        "star sports",
        "sony ten",
        "sony liv",
        "willow",
        "ptv sports",
        "ten sports",
        "geo super",
        "a sports",
        "eurosport",
        "sky sports",
        "bein sports",
        "supersport",
        "espn",
        "fox sports",
    ]
    if any(k in name for k in sports_keywords) or "sports" in category:
        return 2

    # ৩. কলকাতা বাংলা চ্যানেলগুলো
    kolkata_keywords = [
        "star jalsha",
        "zee bangla",
        "colors bangla",
        "sony aath",
        "rupashi bangla",
        "news18 bangla",
        "tv9 bangla",
        "khabor 365",
        "calcutta",
        "kolkata",
    ]
    if any(k in name for k in kolkata_keywords):
        return 3

    # ৪. অন্যান্য জনপ্রিয় ইন্ডিয়ান ও পাকিস্তানি চ্যানেলগুলো
    other_popular = [
        "zee",
        "star",
        "sony",
        "colors",
        "aaj tak",
        "ndtv",
        "geo",
        "ary",
        "hum",
        "express",
        "dunya",
        "samaa",
        "bol",
        "india",
        "pakistan",
    ]
    if country in ["in", "pk"] or any(k in name for k in other_popular):
        return 4

    # ফিল্টারের বাইরে থাকা চ্যানেল বাতিল
    return 99


def fetch_specific_country_channels():
    sources = [
        "https://iptv-org.github.io/iptv/countries/bd.m3u",  # বাংলাদেশ
        "https://iptv-org.github.io/iptv/countries/in.m3u",  # ইন্ডিয়া
        "https://iptv-org.github.io/iptv/countries/pk.m3u",  # পাকিস্তান
        "https://iptv-org.github.io/iptv/categories/sports.m3u",  # গ্লোবাল স্পোর্টস
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 চ্যানেল প্রসেসিং ও নির্দিষ্ট অর্ডারে সাজানো হচ্ছে...")

    channels = []
    seen_urls = set()  # একটি লিংক যেন দুইবার যুক্ত না হয়

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

                # ইউনিক লিংক চেক
                if stream_url and stream_url not in seen_urls:
                    raw_name = (
                        info_line.split(",")[-1].strip()
                        if "," in info_line
                        else "Unknown Channel"
                    )
                    clean_name = clean_channel_name(raw_name)

                    logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                    logo = logo_match.group(1) if logo_match else ""

                    group_match = re.search(r'group-title="([^"]*)"', info_line)
                    category = group_match.group(1) if group_match else "General"

                    country_match = re.search(
                        r'tvg-country="([^"]*)"', info_line
                    )
                    country = (
                        country_match.group(1) if country_match else ""
                    )

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
                        channels.append(ch_obj)
                        seen_urls.add(stream_url)
            i += 1

    # আপনার চাহিদা অনুযায়ী অর্ডারিং: ১. বাংলাদেশ -> ২. স্পোর্টস -> ৩. কলকাতা বাংলা -> ৪. অন্যান্য
    channels.sort(key=lambda x: x["priority"])

    # অতিরিক্ত প্রোপার্টি রিমুভ করা
    for ch in channels:
        ch.pop("priority", None)
        ch.pop("country", None)

    # M3U ফরম্যাট জেনারেট করা
    m3u_lines = ["#EXTM3U\n"]
    for ch in channels:
        m3u_lines.append(
            f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["category"]}",{ch["name"]}\n{ch["stream_url"]}\n'
        )

    # JSON ফাইলে সেভ করা
    json_data = {
        "status": "success",
        "total_channels": len(channels),
        "channels": channels,
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json আপডেট করা হয়েছে (মোট চ্যানেল: {len(channels)})")

    # M3U ফাইলে সেভ করা
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u সফলভাবে তৈরি করা হয়েছে")


if __name__ == "__main__":
    fetch_specific_country_channels()
