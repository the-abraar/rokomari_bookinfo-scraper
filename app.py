import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re

st.set_page_config(page_title="Rokomari Scraper Pro", page_icon="📚")

st.title("📚 Rokomari Book Scraper")
st.markdown("If you get 'N/A', it means the site is temporarily blocking the server. Try again in a few minutes.")

# Input area
input_type = st.radio("Choose Input Method:", ("Paste Links", "Upload .txt File"))

raw_links = ""
if input_type == "Paste Links":
    raw_links = st.text_area("Paste links here (one per line):", height=200)
else:
    uploaded_file = st.file_uploader("Upload links.txt", type="txt")
    if uploaded_file is not None:
        raw_links = uploaded_file.getvalue().decode("utf-8")

if st.button("Start Scraping"):
    urls = list(dict.fromkeys(re.findall(r'(https?://www.rokomari.com/book/\d+/\S+)', raw_links)))
    
    if not urls:
        st.error("No valid Rokomari book links found! (Make sure they look like rokomari.com/book/...)")
    else:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Real-world browser headers to bypass simple bot detection
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
            "Referer": "https://www.google.com/"
        }

        for i, url in enumerate(urls):
            status_text.text(f"Scraping {i+1}/{len(urls)}: {url.split('/')[-1]}")
            try:
                # Add a small timeout and verify SSL
                res = requests.get(url, headers=headers, timeout=15)
                
                if res.status_code != 200:
                    results.append({"Book Name": "Blocked/Error", "Writer": res.status_code, "Original Price": "-", "Publisher": "-", "URL": url})
                    continue

                soup = BeautifulSoup(res.content, "html.parser")

                # --- 1. BOOK NAME (Try Meta Tag first, then H1) ---
                name_tag = soup.find("meta", property="og:title")
                if name_tag:
                    # name_tag is "Book Name - Author | Rokomari.com"
                    name = name_tag["content"].split(" - ")[0].strip()
                else:
                    name = soup.select_one("div.details-book-main-info__header h1")
                    name = name.get_text(strip=True) if name else "N/A"

                # --- 2. WRITER ---
                author = soup.select_one("p.details-book-info__content-author a")
                author = author.get_text(strip=True) if author else "N/A"

                # --- 3. PRICE (Original Price Logic) ---
                orig_price_tag = soup.select_one("strike.original-price")
                if orig_price_tag:
                    price = orig_price_tag.get_text(strip=True)
                else:
                    # Fallback to selling price if no discount exists
                    sell_price_tag = soup.select_one("span.sell-price")
                    price = sell_price_tag.get_text(strip=True) if sell_price_tag else "N/A"

                # --- 4. PUBLISHER (Try Meta Tag brand first) ---
                pub_tag = soup.find("meta", property="product:brand")
                if pub_tag:
                    publisher = pub_tag["content"]
                else:
                    publisher = "N/A"
                    for row in soup.find_all("tr"):
                        if "Publisher" in row.get_text():
                            publisher = row.find_all("td")[-1].get_text(strip=True)
                            break

                results.append({
                    "Book Name": name, 
                    "Writer": author, 
                    "Original Price": price, 
                    "Publisher": publisher, 
                    "URL": url
                })
            except Exception as e:
                results.append({"Book Name": "Error", "Writer": str(e), "Original Price": "-", "Publisher": "-", "URL": url})
            
            progress_bar.progress((i + 1) / len(urls))
            # Critical: Increase delay slightly to avoid being flagged as a bot
            time.sleep(1.5) 

        df = pd.DataFrame(results)
        st.dataframe(df)

        csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="📥 Download CSV for Excel",
            data=csv,
            file_name="rokomari_extracted.csv",
            mime="text/csv",
        )
