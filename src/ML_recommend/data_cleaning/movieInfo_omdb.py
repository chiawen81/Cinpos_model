"""
目標：清洗 OMDb JSON 檔，整理為結構化 CSV
輸入：data/raw/movieInfo_omdb/*.json
輸出：data/processed/movieInfo_omdb/movieInfo_omdb.csv
"""

import os
import json
import pandas as pd
from common.path_utils import MOVIEINFO_OMDb_RAW, MOVIEINFO_OMDb_PROCESSED
from common.file_utils import ensure_dir


def extract_field(data: dict, *keys):
    """多層安全取值"""
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def clean_omdb_json_to_csv():
    ensure_dir(MOVIEINFO_OMDb_PROCESSED)
    rows = []

    for file in os.listdir(MOVIEINFO_OMDb_RAW):
        if not file.endswith(".json"):
            continue
        path = os.path.join(MOVIEINFO_OMDb_RAW, file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        rows.append(
            {
                "gov_id": extract_field(data, "crawl_note", "gov_id"),
                "title_zh": extract_field(data, "crawl_note", "title_zh"),
                "title_en": extract_field(data, "crawl_note", "title_en"),
                "imdb_id": extract_field(data, "crawl_note", "imdb_id"),
                "Year": data.get("Year"),
                "Runtime": data.get("Runtime"),
                "Genre": data.get("Genre"),
                "Language": data.get("Language"),
                "Country": data.get("Country"),
                "Director": data.get("Director"),
                "Writer": data.get("Writer"),
                "Actors": data.get("Actors"),
                "Plot": data.get("Plot"),
                "Awards": data.get("Awards"),
                "Poster": data.get("Poster"),
                "imdbRating": data.get("imdbRating"),
                "imdbVotes": data.get("imdbVotes"),
                "Metascore": data.get("Metascore"),
                "source": extract_field(data, "crawl_note", "source"),
                "fetched_at": extract_field(data, "crawl_note", "fetched_at"),
            }
        )

    df = pd.DataFrame(rows)
    output_path = os.path.join(MOVIEINFO_OMDb_PROCESSED, "movieInfo_omdb.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ 已輸出 CSV：{output_path}")


if __name__ == "__main__":
    clean_omdb_json_to_csv()
