from bs4 import BeautifulSoup
import json
import os

def extract_api_links_and_save(html_file_path):
    if not os.path.exists(html_file_path):
        print(f"❌ Error: {html_file_path} ফাইলটি পাওয়া যায়নি!")
        return

    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    api_logs = []
    m3u_lines = ["#EXTM3U\n"]

    boxes = soup.find_all('div', class_='box')
    
    for box in boxes:
        url_tag = box.find('p', class_='url')
        url = url_tag.text.strip() if url_tag else ""

        if not url:
            continue

        title_tag = box.find('p', class_='title')
        if title_tag:
            time = title_tag.contents[0].strip() if title_tag.contents else ""
            tags = [tag.text.strip() for tag in title_tag.find_all('font')]
            status = tags[0] if len(tags) > 0 else "unknown"
            res_type = tags[1] if len(tags) > 1 else ""
        else:
            time, status, res_type = "", "unknown", ""

        # API লিঙ্ক ফিল্টারিং
        is_api = (
            res_type in ['json', 'php'] or 
            '/api/' in url or 
            'api2.' in url or 
            'translate' in url or 
            '_next/data' in url or
            'matomo.php' in url
        )

        if is_api:
            api_entry = {
                'time': time,
                'status': status,
                'type': res_type if res_type else 'api',
                'url': url
            }
            api_logs.append(api_entry)

            display_name = f"API ({status.upper()}) - {time}"
            m3u_lines.append(f'#EXTINF:-1 group-title="APIs",{display_name}\n{url}\n')

    # ১. JSON ফাইল সেভ
    with open("playlist.json", 'w', encoding='utf-8') as jf:
        json.dump({"api_endpoints": api_logs}, jf, indent=4, ensure_ascii=False)
    print("✅ playlist.json আপডেট হয়েছে")

    # ২. M3U ফাইল সেভ
    with open("playlist.m3u", 'w', encoding='utf-8') as mf:
        mf.writelines(m3u_lines)
    print("✅ playlist.m3u আপডেট হয়েছে")

if __name__ == "__main__":
    # আপনার ইনপুট HTML ফাইল
    extract_api_links_and_save("network_log.html")
