from playwright.sync_api import sync_playwright
import re
import time
from datetime import datetime
import csv
import argparse
import urllib.parse


def process_response_data(response_json, results, max_videos):
    """Extract relevant data from the JSON response and append to results list."""
    try:
        data = response_json
        videos = data.get('itemList', [])
        for video in videos:
            if len(results) >= max_videos:
                break
            video_id = video.get('id', '')
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
    except Exception as e:
        print(f"Error processing response JSON: {e}")


def save_to_csv(results, filename="tiktok_videos.csv"):
    """Save the results to a CSV file."""
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as csv_file:
            fieldnames = [
                'url', 'video_id', 'description', 'author_username',
                'play_count', 'likes_count', 'share_count',
                'sound_name', 'create_time', 'timestamp_text'
            ]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"Data successfully saved to {filename}.")
    except Exception as e:
        print(f"Error saving to CSV: {e}")


def scroll_and_detect(page, results, max_videos):
    """Scroll through the page and detect API responses."""
    target_url_pattern = re.compile(r"https://www\.tiktok\.com/api/explore/item_list/.*")

    def handle_response(response):
        if target_url_pattern.match(response.url):
            print(f"Detected TikTok API call: {response.url}")
            try:
                response_json = response.json()
                process_response_data(response_json, results, max_videos)
            except Exception as e:
                print(f"Failed to parse JSON response: {e}")

    page.on("response", handle_response)

    scroll_position = 0
    scroll_increment = 100  # Pixels to scroll each time
    delay = 0.1  # Delay between scrolls in seconds

    while len(results) < max_videos:
        try:
            page.evaluate(f"window.scrollBy(0, {scroll_increment});")
            scroll_position += scroll_increment
            print(f"Scrolled to position: {scroll_position}")
            time.sleep(delay)
        except Exception as e:
            print(f"Error during scrolling: {e}")
            break


def main():
    parser = argparse.ArgumentParser(description="Scrape TikTok videos.")
    parser.add_argument('--max_videos', type=int, default=100, help="Maximum number of videos to scrape.")
    parser.add_argument('--keyword', type=str, default=None, help="Search keyword for TikTok videos.")
    args = parser.parse_args()

    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-features=site-per-process',
            '--no-sandbox'
        ])
        context = browser.new_context()
        context.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    """)
        page = context.new_page()

        # Determine the URL based on whether a keyword is provided
        if args.keyword:
            encoded_keyword = urllib.parse.quote(args.keyword)
            url = f"https://www.tiktok.com/search?lang=en&q={encoded_keyword}"
        else:
            url = "https://www.tiktok.com/explore?lang=en"

        page.goto(url, wait_until='networkidle')
        page.wait_for_load_state('domcontentloaded')

        try:
            scroll_and_detect(page, results, args.max_videos)
        except KeyboardInterrupt:
            print("Scrolling stopped by user.")
        finally:
            save_to_csv(results)
            browser.close()


if __name__ == "__main__":
    main()
