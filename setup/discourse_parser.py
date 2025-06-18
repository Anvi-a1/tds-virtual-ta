"""
Extract readable summaries from Discourse thread JSON files.
Handles both individual files and directories of threads.

Usage:
    python discourse_parser.py input_path [--output OUTPUT_DIR]

Examples:
    python discourse_parser.py discourse_thread.json
    python discourse_parser.py ./json_dir --output ./out_texts
"""

import sys
import json
import argparse
from pathlib import Path
from bs4 import BeautifulSoup


def strip_html(content: str) -> str:
    """Remove HTML tags and normalize line breaks."""
    parsed = BeautifulSoup(content, "html.parser")
    raw_text = parsed.get_text(separator="\n")
    lines = [line.strip() for line in raw_text.splitlines()]
    compact = []
    for line in lines:
        if line or (compact and compact[-1]):
            compact.append(line)
    return "\n".join(compact).strip()


def summarize_post(post: dict) -> str:
    """Render an individual post as a markdown-style entry."""
    timestamp = post.get("created_at", "")
    author = post.get("name") or post.get("username")
    handle = post.get("username", "")
    role = post.get("user_title", "")
    body = strip_html(post.get("cooked", ""))

    meta = f"[{timestamp}] {author} (@{handle}{': ' + role if role else ''})"
    return f"{meta}\n{body}\n"


def compile_thread(data: dict) -> str:
    """Convert all posts in a thread to a complete summary block."""
    posts = data.get("post_stream", {}).get("posts", [])
    sorted_posts = sorted(posts, key=lambda p: p.get("created_at", ""))
    return "\n".join(summarize_post(p) for p in sorted_posts)


def save_summary(data: dict, output_path: Path):
    """Write the thread summary to a text file with metadata."""
    thread_id = data.get("id", "unknown")
    thread_title = data.get("title", "Untitled")
    start_time = data.get("created_at", "")
    summary = compile_thread(data)

    try:
        with output_path.open("w", encoding="utf-8") as file:
            file.write("---\n")
            file.write(f"id:          {thread_id}\n")
            file.write(f"title:       {thread_title}\n")
            file.write(f"created_at:  {start_time}\n")
            file.write("---\n\n")
            file.write(summary)
        print(f"✔️  Written to: {output_path}")
    except Exception as e:
        print(f"❌ Error writing to {output_path}: {e}", file=sys.stderr)


def handle_file(json_file: Path, destination: Path):
    """Read one JSON file and generate its summary."""
    try:
        with json_file.open(encoding="utf-8") as f:
            thread_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to read {json_file}: {e}", file=sys.stderr)
        return

    destination.mkdir(parents=True, exist_ok=True)
    thread_id = thread_data.get("id", json_file.stem)
    output_file = destination / f"thread_{thread_id}.txt"
    save_summary(thread_data, output_file)


def main():
    parser = argparse.ArgumentParser(
        description="Transform Discourse thread JSONs into clean text summaries."
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to a single JSON file or folder of JSON files.",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("./thread_texts"),
        help="Directory where text summaries will be stored.",
    )
    args = parser.parse_args()

    if not args.input_path.exists():
        print(f"❌ Path not found: {args.input_path}", file=sys.stderr)
        sys.exit(1)

    if args.input_path.is_file():
        handle_file(args.input_path, args.output)
    else:
        files = sorted(args.input_path.glob("*.json"))
        if not files:
            print(f"⚠️  No JSON files found in {args.input_path}", file=sys.stderr)
            sys.exit(1)
        for f in files:
            handle_file(f, args.output)


if __name__ == "__main__":
    main()
