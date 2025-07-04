import requests
from bs4 import BeautifulSoup

def check_security_headers(domain: str) -> str:
    url = f"https://{domain}"
    try:
        response = requests.get(url, timeout=5)
        headers = response.headers

        results = []
        required = ['Content-Security-Policy', 'X-Frame-Options', 'Strict-Transport-Security']
        for h in required:
            if h in headers:
                results.append(f"✅ {h} found")
            else:
                results.append(f"❌ {h} missing")

        return "\n".join(results)
    except Exception as e:
        return f"Header check failed: {e}"

def check_common_directories(domain: str) -> str:
    url_base = f"https://{domain}"
    wordlist = ["/admin", "/login", "/config", "/.git", "/backup"]
    found = []

    for path in wordlist:
        try:
            full_url = url_base + path
            r = requests.get(full_url, timeout=3)
            if r.status_code in [200, 401, 403]:
                found.append(f"🔍 Found: {full_url} [{r.status_code}]")
        except:
            continue

    return "\n".join(found) if found else "No common directories found."

def find_js_urls(domain: str) -> str:
    url = f"https://{domain}"
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        js_urls = []

        for script in soup.find_all("script", src=True):
            src = script["src"]
            if src.startswith("http"):
                js_urls.append(src)
            else:
                js_urls.append(f"{url.rstrip('/')}/{src.lstrip('/')}")

        return "\n".join(js_urls) if js_urls else "No JS files found."
    except Exception as e:
        return f"JS scan failed: {e}"

def check_robots_txt(domain: str) -> str:
    url = f"https://{domain}/robots.txt"
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return f"📄 robots.txt found:\n{r.text[:500]}"
        else:
            return f"❌ robots.txt not found (status {r.status_code})"
    except Exception as e:
        return f"robots.txt check failed: {e}"

def check_sitemap(domain: str) -> str:
    url = f"https://{domain}/sitemap.xml"
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return f"🗺️ sitemap.xml found:\n{r.text[:500]}"
        else:
            return f"❌ sitemap.xml not found (status {r.status_code})"
    except Exception as e:
        return f"sitemap check failed: {e}"

def check_env_exposure(domain: str) -> str:
    url = f"https://{domain}/.env"
    try:
        r = requests.get(url, timeout=3)
        if "APP_KEY" in r.text or "DB_PASSWORD" in r.text:
            return f"⚠️ Exposed .env file found:\n{r.text[:300]}"
        elif r.status_code == 200:
            return "⚠️ .env file exists but no sensitive data detected."
        else:
            return "✅ .env file not accessible."
    except Exception as e:
        return f".env check failed: {e}"

def check_server_header(domain: str) -> str:
    url = f"https://{domain}"
    try:
        r = requests.get(url, timeout=5)
        server = r.headers.get("Server", "Not found")
        return f"🖥️ Server header: {server}"
    except Exception as e:
        return f"Server header check failed: {e}"

def check_http_redirect(domain: str) -> str:
    http_url = f"http://{domain}"
    try:
        r = requests.get(http_url, timeout=5, allow_redirects=True)
        if r.url.startswith("https://"):
            return "✅ HTTP redirects to HTTPS."
        else:
            return f"❌ HTTP does not redirect securely. Final URL: {r.url}"
    except Exception as e:
        return f"Redirect check failed: {e}"

def check_github_mentions(domain: str) -> str:
    try:
        query = f'"{domain}" site:github.com'
        return f"🔎 Search manually for GitHub mentions:\nhttps://www.google.com/search?q={query.replace(' ', '+')}"
    except Exception as e:
        return f"GitHub mention check failed: {e}"
