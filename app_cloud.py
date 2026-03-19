import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import time
import re

st.set_page_config(page_title="Rokomari Scraper Pro", page_icon="📚")
st.title("📚 Rokomari Book Scraper")

raw_links = st.text_area("Paste links here (one per line):", height=200)

if st.button("Start Scraping"):
    urls = list(dict.fromkeys(re.findall(r'(https?://www.rokomari.com/book/\d+/\S+)', raw_links)))
    
    if not urls:
        st.error("No valid links found!")
    else:
        results = []
        progress_bar = st.progress(0)
        
        # Create a scraper object that mimics a real Chrome browser
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        for i, url in enumerate(urls):
            try:
                # Scraper.get bypasses the 403 block
                res = scraper.get(url, timeout=20)
                
                if res.status_code == 200:
                    soup = BeautifulSoup(res.content, "html.parser")

                    # 1. Name
                    name = soup.select_one("div.details-book-main-info__header h1")
                    name = name.get_text(strip=True) if name else "N/A"

                    # 2. Author
                    author = soup.select_one("p.details-book-info__content-author a")
                    author = author.get_text(strip=True) if author else "N/A"

                    # 3. Price (Original/Non-Striked)
                    orig_price_tag = soup.select_one("strike.original-price")
                    if orig_price_tag:
                        price = orig_price_tag.get_text(strip=True)
                    else:
                        sell_price_tag = soup.select_one("span.sell-price")
                        price = sell_price_tag.get_text(strip=True) if sell_price_tag else "N/A"

                    # 4. Publisher
                    publisher = "N/A"
                    for row in soup.find_all("tr"):
                        if "Publisher" in row.get_text():
                            publisher = row.find_all("td")[-1].get_text(strip=True)
                            break

                    results.append({"Book Name": name, "Writer": author, "Original Price": price, "Publisher": publisher, "URL": url})
                else:
                    results.append({"Book Name": f"Error {res.status_code}", "Writer": "Blocked", "URL": url})

            except Exception as e:
                results.append({"Book Name": "Error", "Writer": str(e), "URL": url})
            
            progress_bar.progress((i + 1) / len(urls))
            time.sleep(2) # Cloudflare hates speed; keep it slow

        df = pd.DataFrame(results)
        st.dataframe(df)
        csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("📥 Download CSV", data=csv, file_name="books.csv", mime="text/csv")
