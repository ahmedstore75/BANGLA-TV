import json
import re
import requests


def clean_channel_name(name):
    # ফার্স্ট, থার্ড এবং কার্লি ব্র্যাকেটের ভেতরের অংশ মুছে ফেলার নিয়ম
    cleaned = re.sub(r"[\(\[\{].*?[\)\]\}]", "", name)
    # অতিরিক্ত স্পেস পরিষ্কার করা
    return cleaned.strip()


def get_channel_priority(channel):
    name = channel["name"].lower()
    category = channel["category"].lower()
    country = channel["country"].lower()

    # ১. বাংলাদেশী সকল চ্যানেল (প্রথম অগ্রাধিকার)
    if country == "bd" or "bangladesh" in category:
        return 1

    # ২. কলকাতার বাংলা চ্যানেল (Star Jalsha, Zee Bangla ইত্যাদি)
    kolkata_keywords = [
        "star jalsha",
        "zee bangla",
        "colors bangla",
        "sony aath",
        "rupashi bangla",
        "sangeet bangla",
        "news18 bangla",
        "tv9 bangla",
        "khabor 365",
        "calcutta",
        "kolkata",
        "bangla",
    ]
    if country == "in" and any(k in name for k in kolkata_keywords):
        return 2

    # ৩. হিন্দি ও পপুলার ইন্ডিয়ান চ্যানেল
    indian_popular = [
        "zee",
        "star",
        "sony",
        "colors",
        "aaj tak",
        "ndtv",
        "india",
        "sab",
        "bindass",
        "pogo",
        "hungama",
        "discovery",
        "national geographic",
        "tlc",
        "mtv",
        "nickelodeon",
    ]
    if country == "in" and any(k in name for k in indian_popular):
        return 3

    # ৪. পপুলার স্পোর্টস চ্যানেল (বাংলাদেশ, ভারত, পাকিস্তান এবং গ্লোবাল)
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
        "beIN sports",
        "supersport",
        "espn",
        "fox sports",
    ]
    if any(k in name for k in sports_keywords) or "sports" in category:
        return 4

    # ৫. ফিল্টারের বাইরে থাকা সব চ্যানেল বাতিল
    return 99


def fetch_specific_country_channels():
    # চ্যানেল ডাটা এবং ক্যাটাগরিভিত্তিক সোর্স
    sources = [
        "https://iptv-org.github.io/iptv/countries/bd.m3u",  # বাংলাদেশ (সব)
        "https://iptv-org.github.io/iptv/countries/in.m3u",  # ইন্ডিয়া
        "https://iptv-org.github.io/iptv/countries/pk.m3u",  # পাকিস্তান
        "https://iptv-org.github.io/iptv/categories/sports.m3u",  # গ্লোবাল স্পোর্টস
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 নির্দিষ্ট নিয়ম অনুযায়ী চ্যানেল ফিল্টার এবং প্রসেস করা হচ্ছে...")

    channels = []
    seen_urls = set()  # স্ট্রিমিং লিঙ্ক যেন ডুপ্লিকেট না হয়

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

                # নেক্সট লাইন থেকে স্ট্রিম URL নেওয়া
                if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                    stream_url = lines[i + 1].strip()
                    i += 1

                # নিখুঁত ইউনিক চেক (এক লিঙ্ক প্লেলিস্টে একবারই যোগ হবে)
                if stream_url and stream_url not in seen_urls:
                    raw_name = (
                        info_line.split(",")[-1].strip()
                        if "," in info_line
                        else "Unknown Channel"
                    )
                    clean_name = clean_channel_name(raw_name)

                    # মেটাডাটা এক্সট্রাক্ট করা (লোগো, ক্যাটাগরি, কান্ট্রি)
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

                    # প্রযোজ্য নিয়ম না মানলে ফিল্টার বাতিল (priority 99 ব্লকড)
                    if priority != 99:
                        ch_obj["priority"] = priority
                        channels.append(ch_obj)
                        seen_urls.add(stream_url)
            i += 1

    # প্রিওরিটি অনুযায়ী সাজানো (BD -> Kolkata -> India Popular -> Sports)
    channels.sort(key=lambda x: x["priority"])

    # ফাইল এক্সপোর্টের সময় প্রিওরিটি ফিল্ড বাদ দেওয়া
    for ch in channels:
        ch.pop("priority", None)
        ch.pop("country", None)

    # M3U জেনারেট করা
    m3u_lines = ["#EXTM3U\n"]
    for ch in channels:
        m3u_lines.append(
            f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["category"]}",{ch["name"]}\n{ch["stream_url"]}\n'
        )

    # ১. playlist.json সংরক্ষণ
    json_data = {
        "status": "success",
        "total_channels": len(channels),
        "channels": channels,
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json ফিল্টার করা হয়েছে (মোট চ্যানেল: {len(channels)})")

    # ২. playlist.m3u সংরক্ষণ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u সফলভাবে তৈরি করা হয়েছে")


if __name__ == "__main__":
    fetch_specific_country_channels()
