#!/usr/bin/env python
# coding: utf-8

# In[1]:


# ------------------------------
# Cell 1 - Install dependencies
# ------------------------------
get_ipython().system('pip install -q selenium pandas webdriver-manager')


# In[2]:


# ------------------------------
# Cell 2 - Imports & helpers
# ------------------------------
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# small helper to get safe text from an element
def safe_text(elem, default="N/A"):
    try:
        t = elem.text
        return t.strip() if t else default
    except:
        return default

# helper to click an element if present
def safe_click(driver, by, val):
    try:
        el = driver.find_element(by, val)
        el.click()
        return True
    except:
        return False


# In[3]:


# ------------------------------
# Cell 3 - Driver factory
# ------------------------------
def get_driver(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")   # use new headless if supported
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # optional: speed up by disabling images (uncomment if desired)
    # prefs = {"profile.managed_default_content_settings.images": 2}
    # options.add_experimental_option("prefs", prefs)

    # instantiate driver (webdriver-manager auto-downloads compatible chromedriver)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver


# In[4]:


# ------------------------------
# Cell 4 - Scraper: Devpost (pagination)
# ------------------------------
def scrape_devpost(max_pages=10, pause=3):
    results = []
    driver = get_driver(headless=True)
    try:
        base = "https://devpost.com/hackathons"
        driver.get(base)
        time.sleep(pause)
        page = 1
        while True:
            print(f"[Devpost] scraping page {page} ...")
            time.sleep(1)
            # try several card selectors (page HTML varies)
            cards = driver.find_elements(By.CSS_SELECTOR, ".hackathon-tile") \
                    or driver.find_elements(By.CSS_SELECTOR, ".challenge-card") \
                    or driver.find_elements(By.CSS_SELECTOR, ".project-card")  # fallback
            if not cards:
                print("[Devpost] no cards found on this page (selector may have changed).")
            for c in cards:
                try:
                    title = safe_text(c.find_element(By.TAG_NAME, "h3")) if c else "N/A"
                except:
                    title = "N/A"
                try:
                    link = c.find_element(By.TAG_NAME, "a").get_attribute("href")
                except:
                    link = "N/A"
                # try different date/location selectors
                date = "N/A"
                location = "N/A"
                try:
                    date = safe_text(c.find_element(By.CSS_SELECTOR, ".submission-period"))
                except:
                    try:
                        date = safe_text(c.find_element(By.CSS_SELECTOR, ".dates"))
                    except:
                        pass
                try:
                    location = safe_text(c.find_element(By.CSS_SELECTOR, ".challenge-location"))
                except:
                    try:
                        location = safe_text(c.find_element(By.CSS_SELECTOR, ".location"))
                    except:
                        pass

                results.append({
                    "Source": "Devpost",
                    "Title": title,
                    "Date": date,
                    "Location": location,
                    "Link": link,
                    "ScrapedAt": datetime.utcnow().isoformat()
                })

            # next page attempt: Devpost uses "Next" link text or page param
            page += 1
            if page > max_pages:
                break
            # try clicking "Next" links
            try:
                # many Devpost pages use anchor with rel=next or a next button with text
                next_btn = driver.find_element(By.LINK_TEXT, "Next »")
                next_btn.click()
                time.sleep(pause)
            except:
                # fallback: try to navigate by adding ?page=X
                try:
                    driver.get(f"{base}?page={page}")
                    time.sleep(pause)
                except:
                    break
    except WebDriverException as e:
        print("Devpost scraping driver error:", e)
    finally:
        driver.quit()
    print(f"[Devpost] done, found {len(results)} items")
    return results


# In[10]:


# ------------------------------
# Cell 5 - Scraper: MLH (Major League Hacking)
# ------------------------------
# def scrape_mlh(pause=3):
#     results = []
#     driver = get_driver(headless=True)
#     try:
#         url = "https://mlh.io/seasons/2025/events"
#         driver.get(url)
#         time.sleep(pause)
#         print("[MLH] loaded page")
#         # events on MLH often have container with class 'event' or 'event-wrapper'
#         cards = driver.find_elements(By.CSS_SELECTOR, ".event") \
#                 or driver.find_elements(By.CSS_SELECTOR, ".event-wrapper") \
#                 or driver.find_elements(By.CSS_SELECTOR, ".event-card")
#         for c in cards:
#             try:
#                 title = safe_text(c.find_element(By.TAG_NAME, "h3"))
#             except:
#                 title = "N/A"
#             try:
#                 link = c.find_element(By.TAG_NAME, "a").get_attribute("href")
#             except:
#                 link = "N/A"
            # date/location may be in p.event-date or span.event-location
    #         date = "N/A"
    #         location = "N/A"
    #         try:
    #             date = safe_text(c.find_element(By.CSS_SELECTOR, ".event-date"))
    #         except:
    #             pass
    #         try:
    #             location = safe_text(c.find_element(By.CSS_SELECTOR, ".event-location"))
    #         except:
    #             pass
    #         results.append({
    #             "Source": "MLH",
    #             "Title": title,
    #             "Date": date,
    #             "Location": location,
    #             "Link": link,
    #             "ScrapedAt": datetime.utcnow().isoformat()
    #         })
    # except WebDriverException as e:
    #     print("MLH scraping driver error:", e)
    # finally:
    #     driver.quit()
    # print(f"[MLH] done, found {len(results)} items")
    # return results
def mlh_scraper(driver):
    print("START: MLH")
    url = "https://mlh.io/seasons/2025/events"  # Adjust season if needed
    driver.get(url)
    time.sleep(3)

    hackathons = []
    events = driver.find_elements(By.CSS_SELECTOR, ".event-wrapper")
    for e in events:
        try:
            title = e.find_element(By.CSS_SELECTOR, "h3").text.strip()
            date = e.find_element(By.CSS_SELECTOR, ".event-date").text.strip()
            location = e.find_element(By.CSS_SELECTOR, ".event-location").text.strip()
            link = e.find_element(By.TAG_NAME, "a").get_attribute("href")
            hackathons.append({
                "Title": title,
                "Date": date,
                "Location": location,
                "Link": link,
                "Platform": "MLH",
                "ScrapedAt": datetime.utcnow().isoformat()
            })
        except:
            continue

    print(f"[MLH] done, found {len(hackathons)} items")
    return hackathons



# In[14]:


# ------------------------------
# Cell 6 - Scraper: Hackathon.com (online city)
# ------------------------------
# def scrape_hackathon_com(pause=3):
#     results = []
#     driver = get_driver(headless=True)
#     try:
#         url = "https://www.hackathon.com/city/online"
#         driver.get(url)
#         time.sleep(pause)
#         print("[Hackathon.com] loaded page")
#         # event card selectors may vary; use multiple fallbacks
#         cards = driver.find_elements(By.CSS_SELECTOR, ".event-card") \
#                 or driver.find_elements(By.CSS_SELECTOR, ".event-card__details") \
#                 or driver.find_elements(By.CSS_SELECTOR, ".card")
#         for c in cards:
#             title = "N/A"
#             try:
#                 # Many cards have an h3 or h2 title
#                 title = safe_text(c.find_element(By.TAG_NAME, "h3"))
#             except:
#                 try:
#                     title = safe_text(c.find_element(By.TAG_NAME, "h2"))
#                 except:
#                     pass
#             try:
#                 link = c.find_element(By.TAG_NAME, "a").get_attribute("href")
    #         except:
    #             link = "N/A"
    #         date = "N/A"
    #         try:
    #             date = safe_text(c.find_element(By.CSS_SELECTOR, ".event-card__date"))
    #         except:
    #             pass
    #         results.append({
    #             "Source": "Hackathon.com",
    #             "Title": title,
    #             "Date": date,
    #             "Location": "Online",
    #             "Link": link,
    #             "ScrapedAt": datetime.utcnow().isoformat()
    #         })
    # except WebDriverException as e:
    #     print("Hackathon.com scraping driver error:", e)
    # finally:
    #     driver.quit()
    # print(f"[Hackathon.com] done, found {len(results)} items")
    # return results
def hackathoncom_scraper(driver, max_pages=3):
    print("START: Hackathon.com")
    hackathons = []
    base_url = "https://www.hackathon.com/city/online"

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        print(f"[Hackathon.com] loading page {page} ...")
        driver.get(url)
        time.sleep(5)

        events = driver.find_elements(By.CSS_SELECTOR, ".event-item")
        for e in events:
            try:
                title = e.find_element(By.CSS_SELECTOR, ".event-title").text.strip()
                date = e.find_element(By.CSS_SELECTOR, ".event-date").text.strip()
                location = e.find_element(By.CSS_SELECTOR, ".event-location").text.strip()
                link = e.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

                hackathons.append({
                    "Title": title,
                    "Date": date,
                    "Location": location,
                    "Link": link,
                    "Platform": "Hackathon.com",
                    "ScrapedAt": datetime.utcnow().isoformat()
                })
            except:
                continue

    print(f"[Hackathon.com] done, found {len(hackathons)} items")
    return hackathons




# In[12]:


# ------------------------------
# Cell 7 - Scraper: Eventbrite (search results for hackathon)
# ------------------------------
# def scrape_eventbrite(max_pages=2, pause=4):
#     results = []
#     driver = get_driver(headless=True)
#     try:
#         base = "https://www.eventbrite.com/d/online/hackathon/?page="
#         for p in range(1, max_pages+1):
#             print(f"[Eventbrite] loading page {p} ...")
#             driver.get(base + str(p))
#             time.sleep(pause)
#             # cards on Eventbrite search are often .eds-event-card-content__content or similar
#             cards = driver.find_elements(By.CSS_SELECTOR, ".eds-event-card-content__primary-content") \
#                     or driver.find_elements(By.CSS_SELECTOR, ".search-event-card-wrapper") \
#                     or driver.find_elements(By.CSS_SELECTOR, ".eds-event-card-content__content")
#             for c in cards:
#                 try:
#                     # sometimes title is nested in a div or h3
#                     title = safe_text(c.find_element(By.CSS_SELECTOR, "div[data-spec='event-card__formatted-name']")) \
#                             or safe_text(c.find_element(By.TAG_NAME, "h3"))
#                 except:
    #                 try:
    #                     title = safe_text(c.find_element(By.TAG_NAME, "h3"))
    #                 except:
    #                     title = "N/A"
    #             try:
    #                 link = c.find_element(By.TAG_NAME, "a").get_attribute("href")
    #             except:
    #                 link = "N/A"
    #             date = "N/A"
    #             try:
    #                 date = safe_text(c.find_element(By.CSS_SELECTOR, "div[data-spec='event-card__date']"))
    #             except:
    #                 pass
    #             results.append({
    #                 "Source": "Eventbrite",
    #                 "Title": title,
    #                 "Date": date,
    #                 "Location": "Online",
    #                 "Link": link,
    #                 "ScrapedAt": datetime.utcnow().isoformat()
    #             })
    # except WebDriverException as e:
    #     print("Eventbrite scraping driver error:", e)
    # finally:
    #     driver.quit()
    # print(f"[Eventbrite] done, found {len(results)} items")
    # return results
def eventbrite_scraper(driver, max_pages=3):
    print("START: Eventbrite")
    hackathons = []
    base = "https://www.eventbrite.com/d/online/hackathon/"

    for page in range(1, max_pages + 1):
        print(f"[Eventbrite] loading page {page} ...")
        driver.get(f"{base}?page={page}")
        time.sleep(5)

        events = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='event-card']")
        for e in events:
            try:
                title = e.find_element(By.CSS_SELECTOR, "div.eds-event-card__formatted-name--is-clamped").text.strip()
                date = e.find_element(By.CSS_SELECTOR, "div.eds-event-card-content__sub-title").text.strip()
                link = e.find_element(By.TAG_NAME, "a").get_attribute("href")
                hackathons.append({
                    "Title": title,
                    "Date": date,
                    "Location": "Online",
                    "Link": link,
                    "Platform": "Eventbrite",
                    "ScrapedAt": datetime.utcnow().isoformat()
                })
            except:
                continue

    print(f"[Eventbrite] done, found {len(hackathons)} items")
    return hackathons



# In[8]:


# ------------------------------
# Cell 8 - Scraper: AngelHack (events page)
# ------------------------------
def scrape_angelhack(pause=3):
    results = []
    driver = get_driver(headless=True)
    try:
        url = "https://angelhack.com/events/"
        driver.get(url)
        time.sleep(pause)
        # AngelHack pages are often built with elementor; try to find posts / event elements
        cards = driver.find_elements(By.CSS_SELECTOR, ".elementor-post") \
                or driver.find_elements(By.CSS_SELECTOR, ".elementor-widget-container") \
                or driver.find_elements(By.CSS_SELECTOR, ".event")
        for c in cards:
            # get h3 or h2 text if present
            title = "N/A"
            try:
                title = safe_text(c.find_element(By.TAG_NAME, "h3"))
            except:
                try:
                    title = safe_text(c.find_element(By.TAG_NAME, "h2"))
                except:
                    # fallback: whole text snippet
                    try:
                        title = safe_text(c)
                    except:
                        title = "N/A"
            try:
                link = c.find_element(By.TAG_NAME, "a").get_attribute("href")
            except:
                link = url  # if no item-specific link, use the events page
            results.append({
                "Source": "AngelHack",
                "Title": title,
                "Date": "See website",
                "Location": "Varies",
                "Link": link,
                "ScrapedAt": datetime.utcnow().isoformat()
            })
    except WebDriverException as e:
        print("AngelHack scraping driver error:", e)
    finally:
        driver.quit()
    print(f"[AngelHack] done, found {len(results)} items")
    return results


# In[15]:


# ------------------------------
# Cell 9 - Run all scrapers & combine results
# ------------------------------
all_results = []

# Run Devpost (limit pages to avoid very long runs; increase if needed)
print("START: Devpost")
all_results.extend(scrape_devpost(max_pages=5, pause=3))

print("START: MLH")
all_results.extend(scrape_mlh(pause=3))

print("START: Hackathon.com")
all_results.extend(scrape_hackathon_com(pause=3))

print("START: Eventbrite")
all_results.extend(scrape_eventbrite(max_pages=2, pause=4))

print("START: AngelHack")
all_results.extend(scrape_angelhack(pause=3))

# Convert to DataFrame
df = pd.DataFrame(all_results)
print("Combined total rows (before dedupe):", len(df))
df.sample(min(5, len(df)))


# In[16]:


# ------------------------------
# Cell 10 - Clean, dedupe, save to hackathons.csv
# ------------------------------
# basic cleaning: drop exact duplicate rows, then dedupe by Title+Link
df_clean = df.drop_duplicates()
df_clean = df_clean.drop_duplicates(subset=["Title", "Link"])
# optional: reset index
df_clean = df_clean.reset_index(drop=True)

# Save CSV
output_file = "hackathons.csv"
df_clean.to_csv(output_file, index=False)
print(f"✅ Saved {len(df_clean)} unique hackathons to {output_file}")

# show top rows
df_clean.head(30)


# In[17]:


import pandas as pd
from datetime import datetime

# Load the scraped CSV
df = pd.read_csv("hackathons.csv")

print("Raw rows:", len(df))

# -------------------------------
# 1. Drop duplicates
# -------------------------------
df = df.drop_duplicates(subset=["Title", "Link"])
print("After dropping duplicates:", len(df))

# -------------------------------
# 2. Parse dates & drop invalid ones
# -------------------------------
def parse_date(x):
    try:
        return pd.to_datetime(x, errors="coerce")
    except:
        return pd.NaT

df["Date"] = df["Date"].apply(parse_date)

# Drop rows with no valid date
df = df.dropna(subset=["Date"])
print("After removing invalid dates:", len(df))

# -------------------------------
# 3. Keep only upcoming hackathons
# -------------------------------
today = pd.Timestamp(datetime.now().date())
df = df[df["Date"] >= today]
print("After filtering past events:", len(df))

# -------------------------------
# 4. Sort by date
# -------------------------------
df = df.sort_values("Date").reset_index(drop=True)

# -------------------------------
# 5. Save cleaned CSV
# -------------------------------
df.to_csv("clean_hackathons.csv", index=False)
print("✅ Saved clean_hackathons.csv with", len(df), "upcoming hackathons")


# In[20]:


# === PREVIEW & EXPLORE CLEAN DATA ===
import pandas as pd

df = pd.read_csv("clean_hackathons.csv")

print("Total upcoming hackathons:", len(df))

print("\nBy Source:")
print(df["Source"].value_counts())

print("\nEarliest upcoming hackathon:")
print(df.sort_values("Date").head(1)[["Title", "Date", "Link"]])

print("\nLatest upcoming hackathon:")
print(df.sort_values("Date").tail(1)[["Title", "Date", "Link"]])



# In[21]:


import pandas as pd
from datetime import datetime

# Load clean data
df = pd.read_csv("clean_hackathons.csv")

# Ensure Date is datetime
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# Extract year and month
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month_name()

# Days left until hackathon
today = datetime.now()
df["DaysLeft"] = (df["Date"] - today).dt.days

# Online / Offline detection (very basic)
def classify_location(loc):
    if pd.isna(loc):
        return "Unknown"
    loc_str = str(loc).lower()
    if "online" in loc_str or "virtual" in loc_str:
        return "Online"
    else:
        return "Offline"

df["Mode"] = df["Location"].apply(classify_location)

# Save enriched dataset
df.to_csv("hackathons_final.csv", index=False)

print("✅ Enriched dataset saved as hackathons_final.csv")
print(df.head())


# In[22]:


import pandas as pd
import matplotlib.pyplot as plt

# Load enriched dataset
df = pd.read_csv("hackathons_final.csv")

# 1️⃣ Hackathons by Source
plt.figure(figsize=(6,4))
df["Source"].value_counts().plot(kind="bar")
plt.title("Hackathons by Source")
plt.xlabel("Source")
plt.ylabel("Count")
plt.show()

# 2️⃣ Hackathons by Month
plt.figure(figsize=(8,4))
df["Month"].value_counts().plot(kind="bar", color="orange")
plt.title("Hackathons by Month")
plt.xlabel("Month")
plt.ylabel("Count")
plt.show()

# 3️⃣ Days Left Distribution
plt.figure(figsize=(6,4))
df["DaysLeft"].plot(kind="hist", bins=10, rwidth=0.8)
plt.title("Distribution of Days Left until Hackathon")
plt.xlabel("Days Left")
plt.ylabel("Frequency")
plt.show()

# 4️⃣ Mode (Online vs Offline)
plt.figure(figsize=(5,4))
df["Mode"].value_counts().plot(kind="pie", autopct="%1.1f%%", startangle=90)
plt.title("Hackathon Mode")
plt.ylabel("")  # remove y-axis label
plt.show()


# In[23]:


import pandas as pd
import matplotlib.pyplot as plt

# Load enriched dataset
df = pd.read_csv("hackathons_final.csv")

# Create dashboard with subplots
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

# 1️⃣ Hackathons by Source
df["Source"].value_counts().plot(kind="bar", ax=axs[0,0], color="skyblue")
axs[0,0].set_title("Hackathons by Source")
axs[0,0].set_xlabel("Source")
axs[0,0].set_ylabel("Count")

# 2️⃣ Hackathons by Month
df["Month"].value_counts().plot(kind="bar", ax=axs[0,1], color="orange")
axs[0,1].set_title("Hackathons by Month")
axs[0,1].set_xlabel("Month")
axs[0,1].set_ylabel("Count")

# 3️⃣ Days Left Distribution
df["DaysLeft"].plot(kind="hist", bins=10, rwidth=0.8, ax=axs[1,0], color="green")
axs[1,0].set_title("Days Left Until Hackathon")
axs[1,0].set_xlabel("Days Left")
axs[1,0].set_ylabel("Frequency")

# 4️⃣ Mode (Online vs Offline)
df["Mode"].value_counts().plot(kind="pie", autopct="%1.1f%%", startangle=90, ax=axs[1,1])
axs[1,1].set_title("Hackathon Mode")
axs[1,1].set_ylabel("")

plt.tight_layout()
plt.show()


# In[24]:


# Show top 5 upcoming hackathons
upcoming = df.sort_values("Date").head(5)[["Title", "Date", "Location", "Mode", "Source", "Link"]]

print("📅 Top 5 Upcoming Hackathons:\n")
display(upcoming)


# In[25]:


get_ipython().system('pip install plotly')


# In[26]:


import plotly.graph_objects as go

# Sort by date and pick next 5
upcoming = df.sort_values("Date").head(5)[["Title", "Date", "Location", "Mode", "Source", "Link"]]

# Create interactive table
fig = go.Figure(data=[go.Table(
    header=dict(values=list(upcoming.columns),
                fill_color="lightblue",
                align="left"),
    cells=dict(values=[upcoming[col] for col in upcoming.columns],
               fill_color="lightgrey",
               align="left"))
])

fig.update_layout(title="📅 Top 5 Upcoming Hackathons")
fig.show()


# In[27]:


import plotly.graph_objects as go

# Sort by date and pick next 5
upcoming = df.sort_values("Date").head(5)[["Title", "Date", "Location", "Mode", "Source", "Link"]]

# Convert Link column to clickable HTML
upcoming["Link"] = upcoming["Link"].apply(lambda x: f'<a href="{x}" target="_blank">Open Link</a>')

# Create interactive table with clickable links
fig = go.Figure(data=[go.Table(
    header=dict(values=list(upcoming.columns),
                fill_color="lightblue",
                align="left"),
    cells=dict(values=[upcoming[col] for col in upcoming.columns],
               fill_color="lightgrey",
               align="left"),
    columnwidth=[200, 120, 120, 80, 100, 150]  # optional: adjust column widths
)])

fig.update_layout(title="📅 Top 5 Upcoming Hackathons (Clickable Links)")
fig.show()


# In[28]:


import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime

# Load enriched dataset
df = pd.read_csv("hackathons_final.csv")

# ===== 1️⃣ Dashboard: 4 plots =====
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

# Hackathons by Source
df["Source"].value_counts().plot(kind="bar", ax=axs[0,0], color="skyblue")
axs[0,0].set_title("Hackathons by Source")
axs[0,0].set_xlabel("Source")
axs[0,0].set_ylabel("Count")

# Hackathons by Month
df["Month"].value_counts().plot(kind="bar", ax=axs[0,1], color="orange")
axs[0,1].set_title("Hackathons by Month")
axs[0,1].set_xlabel("Month")
axs[0,1].set_ylabel("Count")

# Days Left Distribution
df["DaysLeft"].plot(kind="hist", bins=10, rwidth=0.8, ax=axs[1,0], color="green")
axs[1,0].set_title("Days Left Until Hackathon")
axs[1,0].set_xlabel("Days Left")
axs[1,0].set_ylabel("Frequency")

# Mode (Online vs Offline)
df["Mode"].value_counts().plot(kind="pie", autopct="%1.1f%%", startangle=90, ax=axs[1,1])
axs[1,1].set_title("Hackathon Mode")
axs[1,1].set_ylabel("")

plt.tight_layout()
plt.show()

# ===== 2️⃣ Interactive Table: Top 5 Upcoming Hackathons =====
upcoming = df.sort_values("Date").head(5)[["Title", "Date", "Location", "Mode", "Source", "Link"]]

# Make links clickable
upcoming["Link"] = upcoming["Link"].apply(lambda x: f'<a href="{x}" target="_blank">Open Link</a>')

# Plotly Table
table_fig = go.Figure(data=[go.Table(
    header=dict(values=list(upcoming.columns),
                fill_color="lightblue",
                align="left"),
    cells=dict(values=[upcoming[col] for col in upcoming.columns],
               fill_color="lightgrey",
               align="left"),
    columnwidth=[200, 120, 120, 80, 100, 150]
)])
table_fig.update_layout(title="📅 Top 5 Upcoming Hackathons (Clickable Links)")
table_fig.show()


# In[ ]:




