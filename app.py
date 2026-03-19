import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
import io

st.set_page_config(page_title="Rokomari Scraper", page_icon="📚")

st.title("📚 Rokomari Book Scraper")
st.markdown("Paste your book links below, and I'll extract the Name, Writer, Original Price, and Publisher.")

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
    # Extract links using regex
    urls = list(dict.fromkeys(re.findall(r'(https?://www.rokomari.com/book/\S+)', raw_links)))
    
    if not urls:
        st.error("No valid Rokomari book links found!")
    else:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"}

        for i, url in enumerate(urls):
            status_text.text(f"Scraping {i+1} of {len(urls)}: {url.split('/')[-1]}")
            try:
                res = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.content, "html.parser")

                name = soup.select_one("div.details-book-main-info__header h1").get_text(strip=True) if soup.select_one("div.details-book-main-info__header h1") else "N/A"
                author = soup.select_one("p.details-book-info__content-author a").get_text(strip=True) if soup.select_one("p.details-book-info__content-author a") else "N/A"
                
                # Price Logic
                orig_price_tag = soup.select_one("strike.original-price")
                if orig_price_tag:
                    price = orig_price_tag.get_text(strip=True)
                else:
                    sell_price_tag = soup.select_one("span.sell-price")
                    price = sell_price_tag.get_text(strip=True) if sell_price_tag else "N/A"

                publisher = "N/A"
                for row in soup.find_all("tr"):
                    if "Publisher" in row.get_text():
                        publisher = row.find_all("td")[-1].get_text(strip=True)
                        break

                results.append({"Book Name": name, "Writer": author, "Original Price": price, "Publisher": publisher, "URL": url})
            except:
                continue
            
            progress_bar.progress((i + 1) / len(urls))
            time.sleep(0.5) # Politeness delay

        # Final Processing
        df = pd.DataFrame(results)
        st.success(f"Finished! Scraped {len(results)} books.")
        st.dataframe(df)

        # Download Button
        csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="📥 Download CSV for Excel",
            data=csv,
            file_name="rokomari_books.csv",
            mime="text/csv",
        )
