import requests
import json

def generate_live_playlist():
    # সরাসরি ভিডিও চলে এমন টেস্ট ও লাইভ স্ট্রিম লিংক (লোগো সহ)
    channels_data = [
        {
            "name": "BTV World Live",
            "url": "https://bd-no-relay.jagobd.com/c3VydmVyX3RpbWU9OS8yLzIwMjQgODo1OToyOSBBTSZpZD0zODcmY2hlY2tzdW09ZmI4NGU1N2Q4MDc2ZmM1NDkyZWVkYWZmZGM1NDljNGI=/btvworld-org.stream/playlist.m3u8",
            "logo": "https://upload.wikimedia.org/wikipedia/commons/2/23/BTV_World_Logo.png",
            "category": "Bangla TV"
        },
        {
            "name": "Channel i Live",
            "url": "https://bd-no-relay.jagobd.com/c3VydmVyX3RpbWU9OS8yLzIwMjQgODo1OToyOSBBTSZpZD0zODcmY2hlY2tzdW09ZmI4NGU1N2Q4MDc2ZmM1NDkyZWVkYWZmZGM1NDljNGI=/channeli-org.stream/playlist.m3u8",
            "logo": "https://upload.wikimedia.org/wikipedia/bn/0/03/Channel_i.png",
            "category": "Bangla TV"
        },
        {
            "name": "Somoy News Live",
            "url": "https://bd-no-relay.jagobd.com/c3VydmVyX3RpbWU9OS8yLzIwMjQgODo1OToyOSBBTSZpZD0zODcmY2hlY2tzdW09ZmI4NGU1N2Q4MDc2ZmM1NDkyZWVkYWZmZGM1NDljNGI=/somoytv-org.stream/playlist.m3u8",
            "logo": "https://upload.wikimedia.org/wikipedia/commons/e/e0/Somoy_TV_Logo.png",
            "category": "News"
        },
        {
            "name": "Test HLS Stream 1",
            "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
            "logo": "https://mux.com/assets/favicon.png",
            "category": "Test Streams"
        },
        {
            "name": "Big Buck Bunny HD Stream",
            "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "logo": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Big_buck_bunny_poster_big.jpg",
            "category": "Movies"
        }
    ]

    print("🔄 ভিডিও স্ট্রিম ও লোগো ডাটা প্রসেস করা হচ্ছে...")

    # ১. সম্পূর্ণ চ্যানেল ডাটা JSON ফাইল হিসেবে তৈরি
    json_output = {
        "status": "success",
        "total_channels": len(channels_data),
        "data": channels_data
    }

    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(json_output, jf, indent=4, ensure_ascii=False)
    print("✅ playlist.json আপডেট করা হয়েছে")

    # ২. আসল M3U৮ প্লেলিস্ট ফাইল তৈরি
    m3u_lines = ["#EXTM3U\n"]
    for ch in channels_data:
        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["category"]}",{ch["name"]}\n{ch["url"]}\n')

    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u আপডেট করা হয়েছে")

if __name__ == "__main__":
    generate_live_playlist()
