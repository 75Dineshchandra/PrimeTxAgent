import os
import requests
import pandas as pd

DATASET_DOI = "10.7910/DVN/IXA7BM"
API_URL = f"https://dataverse.harvard.edu/api/datasets/:persistentId/versions/:latest/files?persistentId=doi:{DATASET_DOI}"
DEST = "primekg_data"
os.makedirs(DEST, exist_ok=True)

print(f" Fetching file list for DOI: {DATASET_DOI}")
resp = requests.get(API_URL)
resp.raise_for_status()
files = resp.json().get("data", [])

print(f" Found {len(files)} files:")
for f in files:
    label = f.get("label", "UNKNOWN")
    size = f.get("size", 0)
    print(f" • {label} ({size:,} bytes)")

#  Use direct file IDs to download
print("\n Downloading files...")
for f in files:
    label = f.get("label", "UNKNOWN")
    file_id = f.get("dataFile", {}).get("id")

    if not file_id:
        print(f"No file ID for {label}, skipping.")
        continue

    download_url = f"https://dataverse.harvard.edu/api/access/datafile/{file_id}"
    try:
        print(f" • Downloading {label} ...")
        r = requests.get(download_url, stream=True)
        r.raise_for_status()
        save_path = os.path.join(DEST, label)
        with open(save_path, "wb") as out:
            for chunk in r.iter_content(8192):
                out.write(chunk)
        print(f"   Saved to {save_path}")
    except Exception as e:
        print(f"   Failed to download {label}: {e}")

# Step 3: Convert .tab → .csv
print("\n Converting .tab files to .csv and deleting originals...")
for file in os.listdir(DEST):
    if file.endswith(".tab"):
        tab_path = os.path.join(DEST, file)
        csv_path = tab_path.replace(".tab", ".csv")
        try:
            df = pd.read_csv(tab_path, sep="\t")
            df.to_csv(csv_path, index=False)
            os.remove(tab_path)
            print(f" Converted and removed {file}")
        except Exception as e:
            print(f" Failed to convert {file}: {e}")

print("\n Done! All PrimeKG files downloaded and prepared in:", os.path.abspath(DEST))