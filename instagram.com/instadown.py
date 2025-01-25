import requests
import time
import json
import csv
from datetime import datetime


def fetch_user_pk(username):
    url = 'https://www.instagram.com/graphql/query'
    cookies = {
        'sessionid': '',
    }
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,fr;q=0.8,fr-FR;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.instagram.com',
        'priority': 'u=1, i',
        'referer': f'https://www.instagram.com/{username}/',
        'sec-ch-prefers-color-scheme': 'light',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-full-version-list': '"Google Chrome";v="131.0.6778.86", "Chromium";v="131.0.6778.86", "Not_A Brand";v="24.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"7.0.0"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-asbd-id': '129477',
        'x-fb-friendly-name': 'PolarisProfilePostsTabContentQuery_connection',
    }

    data = {
        'av': '17841470758140316',
        '__d': 'www',
        '__user': '0',
        '__a': '1',
        '__req': '13',
        '__hs': '20060.HYP:instagram_web_pkg.2.1..0.1',
        'dpr': '1',
        '__ccg': 'EXCELLENT',
        '__rev': '1018561972',
        '__s': 'tnwx9r:fywvgq:a1rrt9',
        '__hsi': '7444185873674676055',
        '__comet_req': '7',
        'jazoest': '26342',
        '__spin_r': '1018561972',
        '__spin_b': 'trunk',
        '__spin_t': '1733234588',
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'PolarisProfilePostsTabContentQuery_connection',
        'variables': '{"after": null,'
                     '"before": null,'
                     '"data": {"count": 1,'
                     '"include_relationship_info": true,'
                     '"latest_besties_reel_media": true,'
                     '"latest_reel_media": true'
                     '},'
                     '"first": 12,'
                     '"last": null,'
                     f'"username": "{username}",'  # Dynamic username
                     '"__relay_internal__pv__PolarisIsLoggedInrelayprovider": true,'
                     '"__relay_internal__pv__PolarisFeedShareMenurelayprovider": true}',
        'server_timestamps': 'true',
        'doc_id': '9163853523625797'
    }

    try:
        response = requests.post(url, data=data, cookies=cookies, headers=headers)
        response.raise_for_status()

        # Extract user PK from the correct path in the response
        data = response.json()
        user_pk = data['data']['xdt_api__v1__feed__user_timeline_graphql_connection']['edges'][0]['node']['user']['pk']

        if user_pk:
            print(f"User PK: {user_pk}")
            return user_pk
        else:
            print("User PK not found in the response")
            return None

    except requests.exceptions.RequestException as e:
        print('Error fetching user PK:', str(e))
        return None
    except (KeyError, IndexError) as e:
        print('Error parsing response:', str(e))
        return None


def get_user_id_from_username(username):
    """
    Get Instagram user ID from username using the search endpoint
    """
    search_url = f'https://www.instagram.com/web/search/topsearch/?query={username}'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
    }

    response = requests.get(search_url, headers=headers)
    data = json.loads(response.content)

    # Find the exact username match in the users list
    for user in data.get('users', []):
        if user['user']['username'].lower() == username.lower():
            return user['user']['pk']

    return None


def get_media_count(username):
    """
    Get media count for an Instagram user
    """
    user_id = fetch_user_pk(username)  # Pass username to fetch_user_pk
    if not user_id:
        return None

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,fr;q=0.8,fr-FR;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.instagram.com',
        'referer': f'https://www.instagram.com/{username}/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }

    data = {
        'av': '17841470758140316',
        '__d': 'www',
        '__user': '0',
        '__a': '1',
        '__req': '2',
        '__hs': '20060.HYP:instagram_web_pkg.2.1..0.1',
        'dpr': '1',
        '__ccg': 'EXCELLENT',
        '__rev': '1018572575',
        '__comet_req': '7',
        'jazoest': '26510',
        'lsd': '1TrJPVbKaZhhooF7RHZEfD',
        '__spin_r': '1018572575',
        '__spin_b': 'trunk',
        '__spin_t': '1733262811',
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'PolarisProfilePostsTabContentQuery_connection',
        'variables': json.dumps({"id": user_id, "render_surface": "PROFILE"}),
        'server_timestamps': 'true',
        'doc_id': '9539110062771438',
    }

    response = requests.post('https://www.instagram.com/graphql/query', headers=headers, data=data)
    return extract_media_count(response.content)


def extract_media_count(response_content):
    """
    Extract media count from response JSON
    """
    try:
        data = json.loads(response_content)
        return data['data']['user']['media_count']
    except (json.JSONDecodeError, KeyError):
        return None


def fetch_instagram_data(total_posts=200, username="bbcnews"):
    # Create CSV filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f'instagram_posts_{username}_{timestamp}.csv'

    # Create and open CSV file
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['code', 'caption_text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        url = 'https://www.instagram.com/graphql/query'
        cookies = {
            'sessionid': '',
        }
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9,fr;q=0.8,fr-FR;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'priority': 'u=1, i',
            'referer': f'https://www.instagram.com/{username}/',
            'sec-ch-prefers-color-scheme': 'light',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-full-version-list': '"Google Chrome";v="131.0.6778.86", "Chromium";v="131.0.6778.86", "Not_A Brand";v="24.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"7.0.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-asbd-id': '129477',
            'x-fb-friendly-name': 'PolarisProfilePostsTabContentQuery_connection',
        }

        base_data = {
            'av': '17841470758140316',
            '__d': 'www',
            '__user': '0',
            '__a': '1',
            '__req': '13',
            '__hs': '20060.HYP:instagram_web_pkg.2.1..0.1',
            'dpr': '1',
            '__ccg': 'EXCELLENT',
            '__rev': '1018561972',
            '__s': 'tnwx9r:fywvgq:a1rrt9',
            '__hsi': '7444185873674676055',
            '__comet_req': '7',
            'jazoest': '26342',
            '__spin_r': '1018561972',
            '__spin_b': 'trunk',
            '__spin_t': '1733234588',
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'PolarisProfilePostsTabContentQuery_connection',
            'server_timestamps': 'true',
            'doc_id': '9163853523625797'
        }

        posts_retrieved = 0
        last_post_id = None
        all_post_data = []
        first_request = True

        while posts_retrieved < total_posts:
            if first_request:
                variables_str = ('{"after": null,'
                                 '"before": null,'
                                 '"data": {"count": 12,'
                                 '"include_relationship_info": true,'
                                 '"latest_besties_reel_media": true,'
                                 '"latest_reel_media": true'
                                 '},'
                                 '"first": 12,'
                                 '"last": null,'
                                 f'"username": "{username}",'
                                 '"__relay_internal__pv__PolarisIsLoggedInrelayprovider": true,'
                                 '"__relay_internal__pv__PolarisFeedShareMenurelayprovider": true}')
            else:
                variables_str = (f'{{"after": "{last_post_id}",'
                                 '"before": null,'
                                 '"data": {"count": 12,'
                                 '"include_relationship_info": true,'
                                 '"latest_besties_reel_media": true,'
                                 '"latest_reel_media": true'
                                 '},'
                                 '"first": 12,'
                                 '"last": null,'
                                 f'"username": "{username}",'
                                 '"__relay_internal__pv__PolarisIsLoggedInrelayprovider": true,'
                                 '"__relay_internal__pv__PolarisFeedShareMenurelayprovider": true}')

            current_data = base_data.copy()
            current_data['variables'] = variables_str

            try:
                response = requests.post(url, data=current_data, cookies=cookies, headers=headers)
                response.raise_for_status()
                data = response.json()

                edges = data.get('data', {}).get('xdt_api__v1__feed__user_timeline_graphql_connection', {}).get('edges',
                                                                                                                [])

                if not edges:
                    print("No more posts available")
                    break

                for edge in edges:
                    if posts_retrieved >= total_posts:
                        break

                    node = edge.get('node', {})
                    caption = node.get('caption', {})

                    # Prepare row for CSV
                    row = {
                        'code': node.get('code'),
                        'caption_text': caption.get('text')
                    }

                    if row['code']:
                        writer.writerow(row)
                        all_post_data.append(row)
                        posts_retrieved += 1
                        print(f"Saved post {posts_retrieved} of {total_posts}")

                if edges:
                    last_post_id = edges[-1]['node']['id']

                first_request = False
                time.sleep(0.01)

            except requests.exceptions.RequestException as e:
                print('Error fetching data:', str(e))
                break

        print(f"\nRetrieved and saved {posts_retrieved} posts out of requested {total_posts}")
        print(f"Data saved to: {csv_filename}")

    return all_post_data


# Usage
username = "bbcnews"
count = get_media_count(username)
fetch_instagram_data(count)
