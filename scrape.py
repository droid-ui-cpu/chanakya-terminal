import json
import xml.etree.ElementTree as ET
import urllib.parse
import urllib.request
import time
from datetime import datetime

DATA_FILE = "data.json"

try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
except Exception:
    db = {"ministers": [], "signals": []}

REGULATORY_TAGS = {
    "inaugurat": ("Visit / Inauguration", "STAGE 1", "badge-stage1"),
    "bhoomi pujan": ("Plant Foundation", "STAGE 1", "badge-stage1"),
    "qco": ("QCO Order", "STAGE 4", "badge-stage4"),
    "quality control": ("Quality Norms", "STAGE 2", "badge-stage2"),
    "bis": ("BIS Standard", "STAGE 2", "badge-stage2"),
    "pli": ("PLI Allocation", "STAGE 3", "badge-stage3"),
    "almm": ("ALMM Inclusion", "STAGE 4", "badge-stage4"),
    "anti-dumping": ("Tariff Protection", "STAGE 3", "badge-stage3"),
    "tender": ("Procurement Tender", "STAGE 3", "badge-stage3")
}

COMPANY_TICKER_MAP = {
    "optiemus": "OPTIEMUSINF", "corning": "OPTIEMUSINF", "dixon": "DIXON",
    "kaynes": "KAYNES", "cg power": "CGPOWER", "waaree": "WAAREE",
    "premier energies": "PREMIERENE", "suzlon": "SUZLON", "balrampur": "BALRAMCHIN",
    "relaxo": "RELAXO", "campus activewear": "CAMPUS", "ok play": "OKPLAY",
    "hal": "HAL", "hindustan aeronautics": "HAL", "bel": "BEL",
    "bharat electronics": "BEL", "mazagon": "MAZDOCK", "cochin shipyard": "COCHINSHIP",
    "larsen": "LT", "l&t": "LT", "irb": "IRB", "titagarh": "TITAGARH",
    "rvnl": "RVNL", "irctc": "IRCTC", "tata steel": "TATASTEEL",
    "jsw steel": "JSWSTEEL", "sail": "SAIL", "indigo": "INDIGO",
    "spicejet": "SPICEJET", "adani ports": "ADANIPORTS", "reliance": "RELIANCE",
    "ongc": "ONGC", "bhel": "BHEL", "ireda": "IREDA"
}

# Clustered search queries that reliably hit policy-relevant headlines
SEARCH_CLUSTERS = [
    '("Ashwini Vaishnaw" OR "MeitY" OR "Optiemus" OR "Dixon") (inaugurates OR plant OR PLI OR BIS)',
    '("Pralhad Joshi" OR "MNRE" OR "Waaree" OR "Solar ALMM") (mandate OR tender OR renewable)',
    '("Piyush Goyal" OR "DPIIT" OR "QCO" OR "Quality Control Order") (shoes OR toys OR imports)',
    '("Rajnath Singh" OR "Defence Acquisition Council" OR "HAL" OR "BEL") (approval OR order OR AoN)',
    '("Nitin Gadkari" OR "NHAI" OR "HAM project" OR "highway tender") (concession OR contract)',
    '("Hardeep Singh Puri" OR "MoPNG" OR "gas allocation" OR "ethanol blending") (mandate OR price)'
]

new_signals = []
existing_titles = {s.get("title", "").strip().lower() for s in db.get("signals", [])}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*"
}

for query in SEARCH_CLUSTERS:
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            root = ET.fromstring(resp.read())
            
            for item in root.findall(".//item")[:4]:
                title = item.find("title").text if item.find("title") is not None else ""
                clean_title = title.strip()
                if not clean_title or clean_title.lower() in existing_titles:
                    continue
                
                link = item.find("link").text if item.find("link") is not None else "#"
                title_lower = clean_title.lower()
                
                matched = ("General Policy", "STAGE 1", "badge-cyan")
                for key, val in REGULATORY_TAGS.items():
                    if key in title_lower:
                        matched = val
                        break
                
                detected = set()
                for keyword, ticker in COMPANY_TICKER_MAP.items():
                    if keyword in title_lower:
                        detected.add(ticker)
                
                new_signals.append({
                    "date": datetime.now().strftime("%d %b %Y"),
                    "category": matched[0],
                    "title": clean_title,
                    "minister": "Union Executive / Regulatory Body",
                    "impact": f"Dynamic alert flagged. Sensitive tickers: {', '.join(detected) if detected else 'Cross-reference sector exposure'}",
                    "stage": matched[1],
                    "badge": matched[2],
                    "dynamic_tickers": list(detected),
                    "url": link
                })
                existing_titles.add(clean_title.lower())
    except Exception as e:
        print(f"Cluster query failed: {e}")
    time.sleep(1)

db["signals"] = (new_signals + db.get("signals", []))[:100]

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print(f"Scrape completed: Added {len(new_signals)} new dynamic signal(s).")
