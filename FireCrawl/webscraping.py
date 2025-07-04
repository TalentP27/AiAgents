import os
import json
import time
import requests
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp


AIRTABLE_API_KEY = 'patKVtVdOrVnWTJEV.a0cc49e69bbaf220dace89ac784db7491f7616456e5c7d86ca24914cc71f7d46'
AIRTABLE_BASE_ID = 'appdy8gyjm6dcXfvp'
AIRTABLE_TABLE_ID = 'tblyU5DpVM8lxTaEY'

firecrawl = FirecrawlApp(api_key="fc-280f4641c9c64d93b69338877636f2bc")

url = "https://www.century21.fr/annonces/f/achat/v-paris/"

def simple_parse(text):
    listings = text.split("Ref :")
    records = []

    for listing in listings[1:]:  # skip first empty part
        lines = listing.strip().split('\n')
        record = {}

        # Ref is first line after split
        record['ref'] = lines[0].strip()

        # Try to find price line (has €)
        price_line = next((l for l in lines if '€' in l), '')
        record['price'] = price_line.strip() if price_line else ''

        # Try to find location line (line with "PARIS")
        location_line = next((l for l in lines if 'PARIS' in l.upper()), '')
        record['location'] = location_line.strip() if location_line else ''

        # Description: all lines between price and "Voir le détail du bien"
        try:
            price_index = lines.index(price_line)
            detail_index = lines.index(next(l for l in lines if 'Voir le détail du bien' in l))
            description = ' '.join(line.strip() for line in lines[price_index+1:detail_index])
            record['description'] = description
        except StopIteration:
            record['description'] = ''

        records.append(record)

    return records

def clean_text_block(text_block):
    # Remove leading/trailing spaces, then remove blank lines inside the block
    lines = [line.strip() for line in text_block.splitlines()]
    lines = [line for line in lines if line]  # remove empty lines
    return "\n".join(lines)

def split_listings(text):
    parts = text.split("Ref :")
    listings = []
    for part in parts[1:]:  # skip first empty before first "Ref :"
        cleaned_part = clean_text_block(part)
        listings.append("Ref : " + cleaned_part)
    return listings

    

scrape_result = firecrawl.scrape_url(url, formats=["html"])

soup = BeautifulSoup(scrape_result.html, "html.parser")
plain_text = soup.get_text()

listings = split_listings(plain_text)

records = simple_parse(plain_text)
for i, record in enumerate(records, 1):
    print(f"Record {i}:\n{record}\n{'-'*20}")

    # Create a new record in Airtable
    response = requests.post(
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}",
        headers={
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        },
        json={"fields": record}
    )
