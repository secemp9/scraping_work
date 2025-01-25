import requests
import json
import time

# URL for the API
url = "https://uitspraken.rechtspraak.nl/api/zoek"

# Headers to include in the request
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
}

# JSON payload template
payload_template = {
    "StartRow": 0,  # Placeholder for pagination
    "PageSize": 10,  # Fixed size of 10 results per page
    "ShouldReturnHighlights": True,
    "ShouldCountFacets": True,
    "SortOrder": "Relevance",
    "SearchTerms": [],
    "Contentsoorten": [{"NodeType": 7, "Identifier": "conclusie", "level": 1}],
    "Rechtsgebieden": [],
    "Instanties": [],
    "DatumPublicatie": [],
    "DatumUitspraak": [],
    "Advanced": {
        "PublicatieStatus": "Ongedefinieerd",
        "PublicatiedatumRange": {"From": "", "To": ""},
    },
    "CorrelationId": "",
    "Proceduresoorten": [],
}


# Function to fetch data from the API
def fetch_data(start_row, page_size):
    payload = payload_template.copy()
    payload["StartRow"] = start_row
    payload["PageSize"] = page_size
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None


# Main script
if __name__ == "__main__":
    # Define the custom page size
    custom_page_size = 10000  # You can change this to your desired page size

    # Fetch the first page to get the total result count
    data = fetch_data(0, custom_page_size)
    if data:
        # Extract total results
        total_results = data.get("ResultCount", 0)
        print(f"Total Results: {total_results}", flush=True)

        # Calculate the number of increments needed
        increments_needed = (total_results + custom_page_size - 1) // custom_page_size  # Ceiling of total_results / page_size
        print(f"Number of Increments Needed: {increments_needed}", flush=True)

        # Fetch results page by page
        for i in range(increments_needed):
            time.sleep(1)  # Optional delay to prevent overloading the API
            start_row = i * custom_page_size  # Increment StartRow dynamically based on custom page size
            page_data = fetch_data(start_row, custom_page_size)
            if page_data:
                for result in page_data.get("Results", []):
                    id_field = result.get("TitelEmphasis", "ID not found")  # Replace with actual ID field if needed
                    print(f"{id_field}", flush=True)
