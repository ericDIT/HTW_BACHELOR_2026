from datetime import datetime
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
import os
import logging
from db.database import connection_pool
import re

load_dotenv()
DATA_LAKE_PATH = os.getenv("DATA_LAKE_PATH")
if not DATA_LAKE_PATH:
    raise RuntimeError(f"Missing required env var DATA_LAKE_PATH")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger(__name__)

def ensure_data_lake_dir(station_name: str, year: str, month: str, day: str, dir_type: str) -> str:

    if not station_name and not dir_type:
        log.error("No station name or directory type (dir_type) given")
        return None

    if not station_name and dir_type=="gtfs_static":
        log.info("checking for gtfs directory...")
        dir_path = os.path.join(DATA_LAKE_PATH, "gtfs", "static", year, month)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path, None

    if not station_name and dir_type=="gtfs_rt":
            log.info("checking for gtfs directory...")
            dir_path = os.path.join(DATA_LAKE_PATH, "gtfs", "rt", year, month, day)
            os.makedirs(dir_path, exist_ok=True)
            return dir_path, None


    station_name_safe = station_name.strip().replace(" ", "_")
    station_name_safe = re.sub(r"[^\w\-]", "", station_name_safe)    
    dir_path = os.path.join(DATA_LAKE_PATH, station_name_safe, year, month, day, dir_type)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path, station_name_safe

def load_into_dl(data, dl_dir: str, station_name: str, today: str, file_type: str, dir_type: str = None) -> bool:
    timestamp = datetime.now().strftime("%H%M%S")
    file_path = None

    if station_name and file_type in ("raw_planned", "raw_actual"):
        file_path = os.path.join(dl_dir, f"{station_name}_{file_type}_{today}_{timestamp}.json")
    elif dir_type == "gtfs_static":
        file_path = os.path.join(dl_dir, f"{timestamp}_{file_type}")

    if file_path is None:
        log.error(f"Could not determine file path for file_type={file_type}")
        return False

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            if dir_type == "gtfs_static":
                f.write(data)
            else:
                json.dump(data, f, ensure_ascii=False, indent=2)
        log.info(f"Successfully loaded data into the data lake in path: {file_path}")
        return True
    except (OSError, TypeError) as e:
        log.error(f"Failed to write data lake file {file_path}: {e}")
        return False