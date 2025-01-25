import requests
import json
from datetime import datetime
import csv
import argparse
import pytz

def get_timezone_mapping():
    """Generate a mapping of country codes to primary timezones."""
    mapping = {}
    for country_code, timezones in pytz.country_timezones.items():
        mapping[country_code] = timezones[0]  # Use the first timezone as the primary one
    return mapping

def fetch_tiktok_videos(max_videos, country_code, tz_name):
    """Fetch TikTok videos based on the given parameters."""
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=1, i',
        'referer': 'https://www.tiktok.com/channel/trending-now?lang=en',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }

    params = {
        'WebIdLastTime': '0',
        'aid': '1988',
        'appId': '1233',
        'app_language': 'en',
        'app_name': 'tiktok_web',
        'browser_language': 'en-US',
        'browser_name': 'Mozilla',
        'browser_online': 'true',
        'browser_platform': 'Win32',
        'browser_version': '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'cacheSessionId': '1734657732550',
        'channel': 'tiktok_web',
        'cookie_enabled': 'true',
        'count': '10',
        'data_collection_enabled': 'true',
        'device_id': '7389950662370674208',
        'device_platform': 'web_pc',
        'focus_state': 'true',
        'from_page': '',
        'history_len': '7',
        'is_fullscreen': 'false',
        'is_page_visible': 'true',
        'keyword': 'trending-now',
        'odinId': '7096488108610634757',
        'offset': '0',
        'os': 'windows',
        'pageType': '11',
        'priority_region': country_code,
        'region': country_code,
        'root_referer': 'https://www.google.com/',
        'screen_height': '768',
        'screen_width': '1360',
        'trafficType': '0',
        'tz_name': tz_name,
        'user_is_login': 'true',
        'webcast_language': 'en',
    }

    offset = 0
    results = []
    seen_video_ids = set()
    has_more = True

    while has_more and len(results) < max_videos:
        print(f"Fetching offset: {offset}")
        params['offset'] = str(offset)
        response = requests.get('https://www.tiktok.com/api/seo/kap/video_list/', params=params, headers=headers)

        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"Error decoding JSON for offset {offset}. Skipping.")
            break

        has_more = data.get('hasMore', False)
        videos = data.get('videoList', [])
        for video in videos:
            if len(results) >= max_videos:
                break
            video_id = video.get('id', '')
            if video_id in seen_video_ids:
                continue
            seen_video_ids.add(video_id)

            create_time = video.get('createTime', 0)
            timestamp_text = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S') if create_time else None

            video_data = {
                'url': video.get('video', {}).get('playAddr', ''),
                'video_id': video_id,
                'description': video.get('desc', ''),
                'author_username': video.get('author', {}).get('uniqueId', ''),
                'play_count': video.get('stats', {}).get('playCount', 0),
                'likes_count': video.get('stats', {}).get('diggCount', 0),
                'share_count': video.get('stats', {}).get('shareCount', 0),
                'sound_name': video.get('music', {}).get('title', ''),
                'create_time': create_time,
                'timestamp_text': timestamp_text
            }
            results.append(video_data)

        offset += 10

    return results

def save_to_csv(results, filename):
    """Save the fetched videos to a CSV file."""
    with open(filename, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = [
            'url', 'video_id', 'description', 'author_username',
            'play_count', 'likes_count', 'share_count',
            'sound_name', 'create_time', 'timestamp_text'
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def main():
    # Generate timezone mapping dynamically
    timezone_mapping = get_timezone_mapping()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Fetch trending TikTok videos by country.")
    parser.add_argument('--max_videos', type=int, default=100, help='Maximum number of videos to fetch (default: 100)')
    parser.add_argument('--country', type=str, default='FR', help='Country code (default: FR)')
    args = parser.parse_args()

    # Determine the timezone for the country
    country_code = args.country.upper()
    tz_name = timezone_mapping.get(country_code, 'UTC')  # Default to UTC if the country code is not found

    # Fetch TikTok videos
    results = fetch_tiktok_videos(args.max_videos, country_code, tz_name)

    # Save results to CSV
    csv_filename = f"tiktok_videos_{country_code}_trending.csv"
    save_to_csv(results, csv_filename)
    print(f"Data successfully saved to {csv_filename}.")

if __name__ == "__main__":
    main()
