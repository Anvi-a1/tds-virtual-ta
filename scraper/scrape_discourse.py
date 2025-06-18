"""
Usage:
    python scraper/scrape_discourse.py \
        --base-url "https://discourse.onlinedegree.iitm.ac.in" \
        --category-path "courses/tds-kb/34" \
        --start-date "2025-01-01" \
        --end-date "2025-04-14" \
        --output-dir "data/discourse_threads" \
        --cookies "_forum_session=your_session_cookie; _t=your_token" \
"""

import os
import json
import argparse
from datetime import datetime, timezone
from math import ceil

import requests
from dateutil.parser import isoparse


def get_cli_args():
    parser = argparse.ArgumentParser(description="Fetch Discourse threads in a date range")

    parser.add_argument("--base-url", required=True, help="Base URL of the Discourse site")
    parser.add_argument("--category-path", required=True, help="Category path (e.g., courses/xyz/34)")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", required=True, help="Directory to save thread files")

    auth = parser.add_argument_group("Authentication (choose one)")
    auth.add_argument("--cookies", help="Raw Cookie header for authentication")
    auth.add_argument("--api-key", help="API key (requires --api-username)")
    auth.add_argument("--api-username", help="API username (requires --api-key)")

    return parser.parse_args()


def prepare_headers(cli_args):
    headers = {"User-Agent": "Discourse-Thread-Downloader"}

    if cli_args.api_key and cli_args.api_username:
        headers["Api-Key"] = cli_args.api_key
        headers["Api-Username"] = cli_args.api_username
    elif cli_args.cookies:
        headers["Cookie"] = cli_args.cookies
    else:
        raise ValueError("Authentication required: provide either cookies or API credentials")

    return headers


def make_output_folder(path_to_dir):
    os.makedirs(path_to_dir, exist_ok=True)


def fetch_data_from_url(url, headers, params=None):
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def is_in_date_window(created_at_str, start_time, end_time):
    created_time = isoparse(created_at_str).astimezone(timezone.utc)
    return start_time <= created_time <= end_time


def collect_discourse_threads(cli_args):
    start_time = datetime.fromisoformat(cli_args.start_date).replace(tzinfo=timezone.utc)
    end_time = datetime.fromisoformat(cli_args.end_date).replace(tzinfo=timezone.utc, hour=23, minute=59, second=59)

    headers = prepare_headers(cli_args)
    make_output_folder(cli_args.output_dir)

    page_counter = 0
    total_saved = 0

    print(f"Scanning threads in /c/{cli_args.category_path}.json between {start_time.date()} and {end_time.date()}")

    while True:
        cat_url = f"{cli_args.base_url}/c/{cli_args.category_path}.json"
        json_response = fetch_data_from_url(cat_url, headers=headers, params={"page": page_counter, "per_page": 100})

        topic_list = json_response.get("topic_list", {}).get("topics", [])
        if not topic_list:
            break

        for thread_meta in topic_list:
            created_at = thread_meta.get("created_at")
            if not created_at or not is_in_date_window(created_at, start_time, end_time):
                continue

            thread_id = thread_meta["id"]
            thread_title = thread_meta.get("title", "untitled").replace("/", "_")
            file_name = f"thread_{thread_id}.json"
            save_path = os.path.join(cli_args.output_dir, file_name)

            if os.path.exists(save_path):
                print(f"[skip] {file_name} already exists")
                continue

            thread_url = f"{cli_args.base_url}/t/{thread_id}.json"
            thread_json = fetch_data_from_url(thread_url, headers=headers)

            all_posts = thread_json.get("post_stream", {}).get("posts", [])
            total_post_count = thread_json.get("posts_count", len(all_posts))
            initial_page_size = len(all_posts)

            # Handle pagination
            if total_post_count > initial_page_size:
                pages_needed = ceil(total_post_count / initial_page_size)
                for p in range(2, pages_needed + 1):
                    paged = fetch_data_from_url(thread_url, headers=headers, params={"page": p})
                    all_posts.extend(paged.get("post_stream", {}).get("posts", []))

            thread_json["post_stream"]["posts"] = all_posts

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(thread_json, f, indent=2, ensure_ascii=False)

            print(f"[saved] {file_name} ({len(all_posts)} posts)")
            total_saved += 1

        page_counter += 1

    print(f"\n✔ Completed. {total_saved} threads saved to '{cli_args.output_dir}'.")


def main():
    args = get_cli_args()
    try:
        collect_discourse_threads(args)
    except Exception as err:
        print(f"❌ Error: {err}")


if __name__ == "__main__":
    main()
