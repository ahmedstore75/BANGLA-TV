import requests
import json
import re

def clean_channel_name(name):
    # ব্র্যাকেট (), [], {} এবং ভেতরের নাম মুছে পরিষ্কার নাম তৈরি করা
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    return cleaned.strip()

def is_excluded_channel(channel):
    name = channel['name'].lower()
    category = channel['category'].lower()
    
    # তেলেগু ও তামিল চ্যানেল চেনার কিউয়ার্ড (ব্লকলিস্ট)
    excluded_keywords = [
        'telugu', 'gemini', 'etv telugu', 'sakshi', 'v6 news', 'tv9 telugu', '10tv',
        'tamil', 'sun tv', 'sun music', 'vijay tv', 'star vijay', 'kalignar', 
        'jaya tv', 'polimer', 'zee tamil', 'colors tamil', 'raj tv', 'thanthi tv'
    ]

    if 'telugu' in category or 'tamil' in category:
        return True
    if any(k in name for k in excluded_keywords):
        return True

    return False

def get_channel_priority(channel):
    name = channel['name'].lower()
    category = channel['category'].lower()

    # ১. শুধুমাত্র বিশুদ্ধ বাংলাদেশী চ্যানেল (সবার উপরে)
    exact_bd_channels = [
        'btv', 'btv world', 'btv chittagong', 'somoy tv', 'somoy news', 'channel i', 
        'ekattor tv', 'jamuna tv', 'rtv', 'atn bangla', 'atn news', 'ntv', 'independent tv', 
        'banglavision', 'dbc news', 'deepto tv', 'asian tv', 'desh tv', 'nagorik tv', 
        'boishakhi tv', 'maasranga', 'bijoy tv', 'gtv', 'gazi tv', 'duronto tv', 
        'saatv', 'saa tv', 'news24', 'channel 24', 'mohana tv', 'channel 9', 'my tv', 
        'mytv', 'nexus tv', 'titas tv', 'chotoder tv', 'ananda tv', 'bengal tv'
    ]
    
    # ABP Ananda, Sangeet Bangla, Hope Channel ইত্যাদিকে বাংলাদেশ থেকে বাদ দেওয়া
    is_bd = any(k == name or k in name for k in exact_bd_channels)
    is_not_bd_exception = any(ex in name for ex in ['abp', 'uk', 'india', 'sangeet bangla', 'santvani', 'shubhsandesh'])

    if is_bd and not is_not_bd_exception:
        return 1

    # ২. স্পোর্টস চ্যানেল (বাংলাদেশী চ্যানেলের ঠিক পরপরই থাকবে)
    sports_keywords = [
        'sport', 'sports', 't sports', 'tsports', 'star sports', 'sony sports', 
        'sony ten', 'willow', 'ptv sports', 'ten sports', 'geo super', 'cric', 'dd sports', 'kabaddi'
    ]
    if any(k in name for k in sports_keywords) or 'sports' in category:
        return 2

    # ৩. কলকাতা বাংলা চ্যানেল (ABP Ananda, Zee Bangla, Sangeet Bangla ইত্যাদি)
    kolkata_keywords = [
        'abp ananda', 'star jalsha', 'zee bangla', 'colors bangla', 'sony aath', 
        'rupashi bangla', 'sangeet bangla', 'news18 bangla', 'tv9 bangla', 
        'khabor 365', 'calcutta', 'kolkata', 'ananda barta'
    ]
    if any(k in name for k in kolkata_keywords) or 'bangla' in category:
        return 3

    # ৪. অন্যান্য ইন্ডিয়ান চ্যানেল (Hope Channel, Santvani, Shubhsandesh ইত্যাদি)
    indian_keywords = ['zee', 'star', 'sony', 'colors', 'aaj tak', 'ndtv', 'india', 'sab', 'bindass', 'pogo', 'hungama', 'discovery', 'hope channel', 'mntv', 'santvani', 'shubhsandesh']
    if any(k in name for k in indian_keywords) or 'india' in category:
        return 4

    # ৫. পাকিস্তানি চ্যানেল
    pak_keywords = ['geo', 'ary', 'hum', 'ptv', 'express', 'dunya', 'samaa', 'bol', 'a-plus', 'pakistan']
    if any(k in name for k in pak_keywords) or 'pakistan' in category:
        return 5

    return 6

def fetch_channels():
    sources = [
        "https://iptv-org.github.io/iptv/countries/bd.m3u",
        "https://iptv-org.github.io/iptv/languages/ben.m3u",
        "https://iptv-org.github.io/iptv/countries/in.m3u",
        "https://iptv-org.github.io/iptv/countries/pk.m3u"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("🔄 সঠিক ক্যাটাগরি ও ফিল্টারিং সহ চ্যানেল লোড করা হচ্ছে...")

    channels = []
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
                    raw_name = info_line.split(",")[-1].strip() if "," in info_line else "Unknown Channel"
                    clean_name = clean_channel_name(raw_name)

                    logo_match = re.search(r'tvg-logo="([^"]*)"', info_line)
                    logo = logo_match.group(1) if logo_match else ""

                    group_match = re.search(r'group-title="([^"]*)"', info_line)
                    category = group_match.group(1) if group_match else "General"

                    ch_obj = {
                        "name": clean_name if clean_name else raw_name,
                        "logo": logo,
                        "category": category,
                        "stream_url": stream_url
                    }

                    if not is_excluded_channel(ch_obj):
                        channels.append(ch_obj)
                        seen_urls.add(stream_url)
            i += 1

    # সিরিয়াল অনুযায়ী সুনির্দিষ্ট সর্টিং করা
    channels.sort(key=get_channel_priority)

    # M3U ফাইল তৈরি
    m3u_lines = ["#EXTM3U\n"]
    for ch in channels:
        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["category"]}",{ch["name"]}\n{ch["stream_url"]}\n')

    # ১. playlist.json তৈরি
    json_data = {
        "status": "success",
        "total_channels": len(channels),
        "channels": channels
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, indent=4, ensure_ascii=False)
    print(f"✅ playlist.json ফিল্টার করা হয়েছে (মোট চ্যানেল: {len(channels)})")

    # ২. playlist.m3u তৈরি
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u সঠিক সিরিয়াল অনুযায়ী সেভ হয়েছে")

if __name__ == "__main__":
    fetch_channels()
