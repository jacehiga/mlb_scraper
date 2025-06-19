from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
from datetime import datetime
import traceback

# Set up headless browser
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--disable-notifications")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 10)

# ESPN scoreboard URL for a specific day
url = "https://www.espn.com/mlb/scoreboard/_/date/20250618"
driver.get(url)

# Dismiss cookie/overlay if it exists
try:
    overlay = driver.find_element(By.CLASS_NAME, "onetrust-close-btn-container")
    overlay.click()
    time.sleep(1)
except:
    pass

# Wait for visible "Box Score" links
WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((
        By.XPATH,
        "//a[normalize-space()='Box Score']"
    ))
)



# Collect all unique visible Box Score hrefs
buttons_raw = driver.find_elements(
    By.XPATH, "//section[contains(@class, 'Scoreboard')]//a[normalize-space()='Box Score']"
)

box_links = []
seen_hrefs = set()
for btn in buttons_raw:
    if not btn.is_displayed():
        continue
    href = btn.get_attribute("href")
    if href and href not in seen_hrefs:
        box_links.append(href)
        seen_hrefs.add(href)

print(f"✅ Found {len(box_links)} unique visible 'Box Score' buttons.")

page_date = "2025-06-18"
results = []

# Visit each game one at a time
for i, href in enumerate(box_links):
    try:
        # Reload scoreboard and click the Box Score link
        driver.get(url)
        wait.until(EC.presence_of_all_elements_located((
            By.XPATH,
            "//section[contains(@class, 'Scoreboard') and not(contains(@style, 'display: none'))]//a[normalize-space()='Box Score']"
        )))
        time.sleep(1)

        game_id = href.split("/")[-1]
        button = driver.find_element(By.XPATH, f"//a[contains(@href, '{game_id}') and normalize-space()='Box Score']")
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", button)
        print(f"▶️ Clicked Box Score button {i + 1}: {href}")

        # Wait for the linescore table to be visible
        time.sleep(2)  # allow ESPN JS to render
        try:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((
                    By.XPATH,
                    "//table[.//th[text()='R'] and .//th[text()='H'] and .//th[text()='E']]"
                ))
            )
        except:
            with open(f"failed_game_{i+1}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.save_screenshot(f"failed_game_{i + 1}.png")
            print(f"⚠️  Box score not available or still loading for game {i + 1}. Skipping.")
            continue

        # Step 4: Extract linescore
        print("→ Extracting linescore...")
        linescore_rows = driver.find_elements(By.XPATH, "//table[contains(@class, 'linescore')]//tr")
        linescore = []
        for row in linescore_rows:
            cells = row.find_elements(By.TAG_NAME, "td") or row.find_elements(By.TAG_NAME, "th")
            row_data = [cell.text.strip() for cell in cells]
            if row_data:
                linescore.append(row_data)

        # Step 5: Extract player stats
        print("→ Extracting player stats...")
        stat_tables = driver.find_elements(By.XPATH, "//div[contains(@class, 'Boxscore__Content')]//table")
        player_stats = []
        for table in stat_tables:
            rows = table.find_elements(By.TAG_NAME, "tr")
            table_data = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td") or row.find_elements(By.TAG_NAME, "th")
                table_data.append([cell.text.strip() for cell in cells])
            player_stats.append(table_data)

        # Save final result
        results.append({
            "game_index": i + 1,
            "game_date": page_date,
            "game_url": href,
            "box_score": {
                "linescore": linescore,
                "player_stats": player_stats
            }
        })
        print(f"✅ Saved game {i + 1}")

    except Exception as e:
        print(f"❌ Error on game {i + 1}:")
        traceback.print_exc()
        continue

# Save results
with open("mlb_box_scores.jsonl", "w") as f:
    for row in results:
        json.dump(row, f)
        f.write("\n")

print(f"\n🎯 Finished: {len(results)} games saved, {len(box_links) - len(results)} skipped.")
driver.quit()
