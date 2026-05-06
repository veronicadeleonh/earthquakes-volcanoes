"""
Run this script manually to update the cached volcanic activity data.
Usage: python update_volcano_data.py
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def scrape_weekly_report():
    url = "https://volcano.si.edu/reports_weekly.cfm?vtab=feeds"
    response = requests.get(url)
    if not response.ok:
        print(f"Failed to fetch weekly report: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if table is None:
        print("No table found in weekly report page.")
        return None

    volcano_data = []
    headers = [th.get_text(strip=True) for th in table.find_all("th")][1:]

    for row in table.find_all("tr")[2:]:
        cols = row.find_all(["td", "th"])
        if len(cols) < len(headers):
            continue
        try:
            volcano_link = row.find("a", href=re.compile(r"#vn_"))
            if not volcano_link:
                continue
            volcano_id = volcano_link["href"].split("#vn_")[1]
            volcano_name = volcano_link.get_text(strip=True)
            start_date = cols[3].get_text(strip=True)
            report_status = row.find("a", attrs={"data-tooltip": True})
            report_text = report_status.get_text(strip=True) if report_status else None
            volcano_data.append({
                "volcano_id": volcano_id,
                "volcano_name": volcano_name,
                "start_date": start_date,
                "report_status": report_text,
            })
        except Exception as e:
            print(f"Error processing row: {e}")

    return pd.DataFrame(volcano_data)


def scrape_yearly_report():
    url = "https://volcano.si.edu/faq/index.cfm?question=eruptionsbyyear&checkyear=2025"
    response = requests.get(url)
    if not response.ok:
        print(f"Failed to fetch yearly report: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if table is None:
        print("No table found in yearly report page.")
        return None

    headers = [th.text.strip() for th in table.find_all("th")]
    data = []
    for row in table.find_all("tr")[1:]:
        row_data = [td.text.strip() for td in row.find_all("td")]
        if row_data:
            data.append(row_data)

    df = pd.DataFrame(data, columns=headers)
    df.columns = [col.lower() for col in df.columns]
    return df


if __name__ == "__main__":
    print("Updating weekly report...")
    weekly = scrape_weekly_report()
    if weekly is not None and not weekly.empty:
        path = os.path.join(DATA_DIR, "weekly_report_raw.csv")
        weekly.to_csv(path, index=False)
        print(f"Saved {len(weekly)} rows to {path}")
    else:
        print("Skipping weekly report update (site may be blocking requests).")

    print("\nUpdating yearly report...")
    yearly = scrape_yearly_report()
    if yearly is not None and not yearly.empty:
        path = os.path.join(DATA_DIR, "yearly_report_raw.csv")
        yearly.to_csv(path, index=False)
        print(f"Saved {len(yearly)} rows to {path}")
    else:
        print("Skipping yearly report update (site may be blocking requests).")
