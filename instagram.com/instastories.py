from instaloader import Instaloader, Profile
import csv
from datetime import datetime

# Initialize Instaloader with minimal settings
L = Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False
)

# Your cookies dict
cookies = {
}

# Load session from cookies
L.context.update_cookies(cookies)

# Update CSRF token and headers
L.context._session.headers.update({
    'X-CSRFToken': cookies['csrftoken'],
    'X-Instagram-AJAX': '1',
    'Origin': 'https://www.instagram.com',
    'Referer': 'https://www.instagram.com/',
})

# Test if login worked and get username
username = L.test_login()
if username is None:
    raise Exception("Login failed. Check cookies.")
else:
    print(f"Successfully logged in as {username}")
    L.context.username = username

# Get the profile
target_username = "bbcnews"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"instagram_stories_{target_username}_{timestamp}.csv"

try:
    profile = Profile.from_username(L.context, target_username)
    print(f"Got profile: {profile.username} (ID: {profile.userid})")

    # Create CSV file and write header
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Username', 'Created At', 'Media ID', 'Media Type', 'Media URL', 'Video URL'])

        # Get stories
        stories = L.get_stories([profile.userid])
        for story in stories:
            print(f"\nProcessing stories from {story.owner_username}")
            print(f"Total items: {story.itemcount}")

            for item in story.get_items():
                # Prepare row data
                row_data = [
                    story.owner_username,
                    item.date_local,
                    item.mediaid,
                    'Video' if item.is_video else 'Image',
                    item.url,
                    item.video_url if item.is_video else ''
                ]

                # Write to CSV
                csvwriter.writerow(row_data)

                # Print progress
                print(f"Saved story item: {item.mediaid}")

    print(f"\nStories data saved to {csv_filename}")

except Exception as e:
    print(f"Error: {str(e)}")
