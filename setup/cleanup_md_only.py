import os
import argparse

def purge_non_md_files(base_dir):
    """Purge non-markdown files and delete empty directories, ignoring .git paths."""
    for folder_path, subdirs, files in os.walk(base_dir, topdown=False):
        # Skip .git folders
        if '.git' in folder_path.split(os.sep):
            continue

        # Delete all files that don't end in .md
        for file in files:
            if not file.lower().endswith('.md'):
                file_path = os.path.join(folder_path, file)
                try:
                    os.remove(file_path)
                    print(f"🗑️ Deleted file: {file_path}")
                except Exception as err:
                    print(f"⚠️ Couldn't delete {file_path}: {err}")

        # Delete empty folders
        try:
            if not os.listdir(folder_path):
                os.rmdir(folder_path)
                print(f"📁 Removed empty directory: {folder_path}")
        except Exception as err:
            print(f"⚠️ Couldn't remove directory {folder_path}: {err}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Remove all files except .md and cleanup empty dirs (ignores .git)")
    parser.add_argument('path', help='Directory path to clean')
    cli_args = parser.parse_args()

    if not os.path.isdir(cli_args.path):
        print(f"❌ Provided path is not a valid directory: {cli_args.path}")
    else:
        purge_non_md_files(cli_args.path)
        print("✅ Directory cleanup finished.")

