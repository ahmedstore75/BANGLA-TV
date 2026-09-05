import requests
import json

def fetch_and_save():
    # আপনার দেওয়া ৩টি নির্দিষ্ট API লিঙ্ক
    api_list = [
        {
            "name": "Tapmad FAQs Data",
            "url": "https://www.tapmad.com/_next/data/3Zz7jRQ_anY5T5QAB07XG/legal-center/bd/faqs.json?slug=faqs",
            "logo": "https://d34080pnh6e62j.cloudfront.net/images/contentCategorythumb/1787662644_1600x2130.jpg"
        },
        {
            "name": "Branch IO Analytics Open",
            "url": "https://api2.branch.io/v1/open",
            "logo": "https://d34080pnh6e62j.cloudfront.net/images/NewVideoOnDemandThumb/1788512129_324x432-vod.jpg"
        },
        {
            "name": "Branch IO Analytics Pageview",
            "url": "https://api2.branch.io/v1/pageview",
            "logo": "https://d34080pnh6e62j.cloudfront.net/images/NewVideoOnDemandThumb/1788512398_324x432-vod.jpg"
        }
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    all_responses = {}
    m3u_lines = ["#EXTM3U\n"]

    print("🔄 এপিআই লিঙ্কগুলো থেকে ডাটা কালেক্ট করা হচ্ছে...")

    for item in api_list:
        name = item["name"]
        url = item["url"]
        logo = item["logo"]

        try:
            # লিঙ্ক থেকে লাইভ ডাটা ফেচ করা
            if "branch.io" in url:
                res = requests.post(url, json={}, headers=headers, timeout=10)
            else:
                res = requests.get(url, headers=headers, timeout=10)

            # এপিআই ডাটা সেভ করা
            if res.status_code == 200:
                try:
                    all_responses[name] = res.json()
                except Exception:
                    all_responses[name] = {"raw_response": res.text}
            else:
                all_responses[name] = {"status_code": res.status_code, "msg": "Response non-200"}

        except Exception as e:
            all_responses[name] = {"error": str(e)}

        # M3U প্লেলিস্ট লাইনে যুক্ত করা
        m3u_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="API Endpoints",{name}\n{url}\n')

    # ১. playlist.json ফাইলে আপনার দেওয়া ৩টি এপিআই-এর সম্পূর্ণ ডাটা সেভ
    with open("playlist.json", "w", encoding="utf-8") as jf:
        json.dump(all_responses, jf, indent=4, ensure_ascii=False)
    print("✅ playlist.json আপডেট হয়েছে")

    # ২. playlist.m3u ফাইলে এপিআই লিঙ্কগুলো সেভ
    with open("playlist.m3u", "w", encoding="utf-8") as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u আপডেট হয়েছে")

if __name__ == "__main__":
    fetch_and_save()
