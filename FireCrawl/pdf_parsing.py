from firecrawl import FirecrawlApp

firecrawl = FirecrawlApp(api_key="fc-7cb47598f5144f49816a55e8ab1b819f")

response = firecrawl.crawl_url(
    url="https://www.pwc.com/gx/en/issues/analytics/assets/pwc-ai-analysis-sizing-the-prize-report.pdf"
)

print(response)