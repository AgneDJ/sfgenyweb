import csv
import json
import os
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

OUT_FILE = "posts.json"


def write_empty():
    if not os.path.isfile(OUT_FILE):
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    print(f"Wrote 0 items to {OUT_FILE} (empty).")


def parse_date(s: str) -> str:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return s


def to_bool(s: str) -> bool:
    return (s or "").strip().lower() in {"1", "true", "taip", "yes", "y", "t"}


def load_from_local(path: str):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_from_url(url: str):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    return list(csv.DictReader(text.splitlines()))


def normalize_row(r: dict):
    title = r.get("title") or r.get("pavadinimas") or r.get("antraste")
    date = r.get("date") or r.get("data")
    if not title or not date:
        return None
    return {
        "title": title.strip(),
        "date": parse_date(date),
        "excerpt": (r.get("excerpt") or r.get("aprasymas") or "").strip() or None,
        "image": (r.get("image") or r.get("nuotrauka") or "").strip() or None,
        "categories": [c.strip() for c in (r.get("categories") or r.get("kategorijos") or "").split(",") if c.strip()],
        "featured": to_bool(r.get("featured") or r.get("svarbiausia") or ""),
        "link": (r.get("link") or r.get("nuoroda") or "").strip() or None,
    }


def main():
    # If no arg provided, just ensure empty posts.json and exit
    if len(sys.argv) < 2:
        write_empty()
        return

    source = sys.argv[1]
    try:
        if source.lower().startswith("http"):
            rows = load_from_url(source)
        else:
            rows = load_from_local(source)
    except (HTTPError, URLError) as e:
        print(
            f"Warning: failed to fetch CSV ({e}). Creating empty posts.json instead.")
        write_empty()
        return
    except FileNotFoundError:
        print("Warning: local CSV not found. Creating empty posts.json instead.")
        write_empty()
        return

    out = []
    for r in rows:
        item = normalize_row(r)
        if item:
            out.append(item)
    out.sort(key=lambda x: x["date"], reverse=True)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(out)} items to {OUT_FILE}")


if __name__ == "__main__":
    main()
