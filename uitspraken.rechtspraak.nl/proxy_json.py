import requests
import os
import json
import sys
import time
import random
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def exponential_backoff(attempt, max_delay=5):
    """Calculate delay with exponential backoff and jitter, capped at 5 minutes"""
    delay = min(max_delay, (2 ** attempt) + random.uniform(0, 1))
    print(delay)
    time.sleep(delay)

def fetch_with_local_ip(base_url, line, output_dir):
    """Fetch data using local IP address without proxy"""
    url = f"{base_url}{line.strip()}"
    attempt = 0
    
    while True:  # Infinite retry loop
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("UitspraakTekst") is None:
                return False
            
            sanitized_filename = line.strip().replace("/", "_").replace("\\", "_").replace(":", "_") + ".json"
            output_file = os.path.join(output_dir, sanitized_filename)
            
            with open(output_file, "w") as json_file:
                json.dump(data, json_file, indent=4)
            return True
            
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Attempt {attempt + 1} failed for {line.strip()} with local IP: {str(e)}. Retrying...")
            exponential_backoff(attempt)
            attempt += 1

def fetch_with_proxy(base_url, line, output_dir, port):
    """Fetch data using proxy"""
    username = 'username'  # Replace with actual credentials
    password = 'pass'
    proxy_host = 'dc.smartproxy.com'
    
    proxy = f"http://{username}:{password}@{proxy_host}:{port}"
    proxies = {
        'http': proxy,
        'https': proxy
    }
    
    url = f"{base_url}{line.strip()}"
    attempt = 0
    
    while True:  # Infinite retry loop
        try:
            response = requests.get(url, proxies=proxies, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if data.get("UitspraakTekst") is None:
                return False
            
            sanitized_filename = line.strip().replace("/", "_").replace("\\", "_").replace(":", "_") + ".json"
            output_file = os.path.join(output_dir, sanitized_filename)
            
            with open(output_file, "w") as json_file:
                json.dump(data, json_file, indent=4)
            return True
            
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Attempt {attempt + 1} failed for {line.strip()} with port {port}: {str(e)}. Retrying...")
            exponential_backoff(attempt)
            attempt += 1

def process_chunk(base_url, lines, output_dir, port, counter, use_local_ip=False):
    successful = 0
    failed = 0
    
    for line in lines:
        if line.strip():
            if use_local_ip:
                success = fetch_with_local_ip(base_url, line, output_dir)
            else:
                success = fetch_with_proxy(base_url, line, output_dir, port)
            
            if success:
                successful += 1
            else:
                failed += 1
            counter.value += 1
    
    return successful, failed

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <output_dir>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    base_url = "https://uitspraken.rechtspraak.nl/api/document/?id="
    num_proxy_workers = 100  # Number of proxy processes
    total_workers = num_proxy_workers + 1  # Add one more for local IP

    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(input_file, "r") as file:
            lines = file.readlines()[2:]  # Skip first two lines
            lines = [line for line in lines if line.strip()]

        total_lines = len(lines)
        
        # Calculate chunk sizes for proxy workers and local IP
        proxy_chunk_size = (total_lines * num_proxy_workers) // total_workers // num_proxy_workers
        local_chunk_size = total_lines - (proxy_chunk_size * num_proxy_workers)
        
        # Split lines into chunks
        proxy_chunks = []
        remaining_lines = lines[:]
        
        # Create chunks for proxy workers
        for _ in range(num_proxy_workers):
            if len(remaining_lines) >= proxy_chunk_size:
                chunk = remaining_lines[:proxy_chunk_size]
                proxy_chunks.append(chunk)
                remaining_lines = remaining_lines[proxy_chunk_size:]
        
        # Remaining lines go to local IP worker
        local_chunk = remaining_lines

        print(f"Processing {total_lines} lines using {total_workers} workers...")
        print(f"Lines per proxy worker: {proxy_chunk_size}")
        print(f"Lines for local IP: {len(local_chunk)}")
        print("Starting processing...\n")

        with Manager() as manager:
            counter = manager.Value('i', 0)
            total_successful = 0
            total_failed = 0

            with ProcessPoolExecutor(max_workers=total_workers) as executor:
                with tqdm(total=total_lines, desc="Processing", unit="lines") as pbar:
                    futures = []
                    
                    # Submit proxy tasks
                    for i, chunk in enumerate(proxy_chunks):
                        port = 10001 + i  # Ports from 10001 to 10100
                        futures.append(
                            executor.submit(process_chunk, base_url, chunk, output_dir, port, counter, False)
                        )
                    
                    # Submit local IP task
                    futures.append(
                        executor.submit(process_chunk, base_url, local_chunk, output_dir, None, counter, True)
                    )

                    # Monitor progress
                    while any(not future.done() for future in futures):
                        current = counter.value
                        pbar.n = current
                        pbar.refresh()

                    # Collect results
                    for future in futures:
                        successful, failed = future.result()
                        total_successful += successful
                        total_failed += failed

        print(f"\nFinal results:")
        print(f"Total successfully processed: {total_successful}")
        print(f"Total failed to process: {total_failed}")
        print(f"Total completion rate: {(total_successful / total_lines) * 100:.2f}%")

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' does not exist.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
