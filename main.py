import requests
import json

def generate_playlist():
    # ১. আপনার প্রদানকৃত নেটওয়ার্ক লগ থেকে সংগৃহীত নির্দিষ্ট API লিঙ্কসমূহ
    target_apis = [
        {"name": "Tapmad Web Settings", "url": "https://backend-api.tapmad.com/api/getMobileAppSettings/V1/en/web", "logo": "https://d34080pnh6e62j.cloudfront.net/images/channels/ChannelFeaturedAppthumb/1788571269540x302.jpg"},
        {"name": "User Preference Header", "url": "https://backend-api.tapmad.com/api/getUserPrefernceHeader", "logo": "https://d34080pnh6e62j.cloudfront.net/images/contentCategorythumb/1786009775_1600x2130.jpg"},
        {"name": "Legal Contact Data", "url": "https://www.tapmad.com/_next/data/3Zz7jRQ_anY5T5QAB07XG/legal-center/bd/contact.json?slug=contact", "logo": "https://d34080pnh6e62j.cloudfront.net/images/contentCategorythumb/1786524277_1600x2130.jpg"},
        {"name": "Legal FAQs Data", "url": "https://www.tapmad.com/_next/data/3Zz7jRQ_anY5T5QAB07XG/legal-center/bd/faqs.json?slug=faqs", "logo": "https://d34080pnh6e62j.cloudfront.net/images/contentCategorythumb/1787662644_1600x2130.jpg"},
        {"name": "Legal About Data", "url": "https://www.tapmad.com/_next/data/3Zz7jRQ_anY5T5QAB07XG/legal-center/bd/about.json?slug=about", "logo": "https://d34080pnh6e62j.cloudfront.net/images/NewVideoOnDemandCategorythumb/1788551903_324x432-vod-copy.jpg"},
        {"name": "Google Translate Log API", "url": "https://translate.googleapis.com/element/log?format=json&hasfast=true&authuser=0", "logo": "https://www.gstatic.com/images/branding/product/2x/translate_24dp.png"},
        {"name": "Branch IO Analytics Pageview", "url": "https://api2.branch.io/v1/pageview", "logo": "https://d34080pnh6e62j.cloudfront.net/images/NewVideoOnDemandThumb/1788512398_324x432-vod.jpg"},
        {"name": "Branch IO Analytics Open", "url": "https://api2.branch.io/v1/open", "logo": "https://d34080pnh6e62j.cloudfront.net/images/NewVideoOnDemandThumb/1788512129_324x432-vod.jpg"}
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    fetched_json_data = {}
    m3u_lines = ["#EXTM3U\n"]

    print("🔄 এপিআই থেকে ডেটা লোড করা হচ্ছে...")

    # ২. প্রতিটা API-তে হিট করে লাইভ রেসপন্স সংগ্রহ করা
    for item in target_apis:
        api_name = item["name"]
        api_url = item["url"]
        logo_url = item["logo"]

        try:
            res = requests.get(api_url, headers=headers, timeout=8)
            if res.status_code == 200:
                try:
                    fetched_json_data[api_name] = res.json()
                except Exception:
                    fetched_json_data[api_name] = {"status_code": 200, "response_text": "Non-JSON or binary data response"}
            else:
                fetched_json_data[api_name] = {"status_code": res.status_code}
        except Exception as e:
            fetched_json_data[api_name] = {"error": str(e)}

        # M3U৮ ফরম্যাটে লোগো সহ লাইন তৈরি
        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="Tapmad APIs",{api_name}\n{api_url}\n')

    # ৩. playlist.json ফাইল সেভ
    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(fetched_json_data, jf, indent=4, ensure_ascii=False)
    print("✅ playlist.json সফলভাবে আপডেট হয়েছে")

    # ৪. playlist.m3u ফাইল সেভ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u সফলভাবে লোগো সহ সেভ হয়েছে")

if __name__ == "__main__":
    generate_playlist()
