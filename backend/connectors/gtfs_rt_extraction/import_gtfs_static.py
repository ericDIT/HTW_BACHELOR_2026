from datetime import date
import zipfile
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


from dotenv import load_dotenv
from utils.data_lake_management import ensure_data_lake_dir, load_into_dl

load_dotenv()

#Structure in Data Lake
#
#gtfs / static / year / month
#     / rt     / year / month / day

#This has to be the normal gtfs zip-file
DATA_LAKE_PATH = os.getenv("DATA_LAKE_PATH")
if not DATA_LAKE_PATH:
    raise RuntimeError("Missing required env var DATA_LAKE_PATH")

IMPORT_STATIC_GTFS_PATH = os.path.join(DATA_LAKE_PATH, "_imports", "gtfs.zip")
DIR_TYPE = "gtfs_static"
today = date.today().strftime("%Y-%m-%d")
year, month, day = today.split("-")

if not os.path.exists(IMPORT_STATIC_GTFS_PATH):
    raise FileNotFoundError(
        f"GTFS static ZIP not found at {IMPORT_STATIC_GTFS_PATH}. "
        f"Place the downloaded gtfs.zip there first."
    )

success_dict = {}
dl_dir, stop_name_safe = ensure_data_lake_dir(None, year, month, None, DIR_TYPE)

with zipfile.ZipFile(IMPORT_STATIC_GTFS_PATH, "r") as z:
    txt_files = [name for name in z.namelist() if name.endswith(".txt")]
    for txt_file in txt_files:
        with z.open(txt_file) as f:
            content = f.read()
            text = content.decode("utf-8")
        dl_load_successful = load_into_dl(text, dl_dir, stop_name_safe, today, txt_file, dir_type=DIR_TYPE)
        success_dict[txt_file] = dl_load_successful
        print(f"Loading {txt_file} successful: {dl_load_successful}")

print(f"\nSummary: {sum(success_dict.values())}/{len(success_dict)} files loaded successfully.")
if not all(success_dict.values()):
    failed = [name for name, ok in success_dict.items() if not ok]
    print(f"Failed files: {failed}")