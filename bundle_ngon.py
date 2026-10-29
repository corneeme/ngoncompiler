import urllib.request
import zipfile
import io
import os
import re
from bs4 import BeautifulSoup

REPO_ZIP_URL = "https://github.com/landgreen/n-gon/archive/refs/heads/master.zip"
OUTPUT_FILE = "ngon_standalone.html"

def download_and_extract_repo(url):
    print(f"Downloading repository from {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        zip_data = response.read()
    
    print("Extracting archive in memory...")
    z = zipfile.ZipFile(io.BytesIO(zip_data))
    
    files = {}
    for name in z.namelist():
        # Remove root folder prefix (e.g., n-gon-master/)
        parts = name.split('/', 1)
        if len(parts) > 1 and parts[1]:
            rel_path = parts[1]
            if not name.endswith('/'):
                try:
                    files[rel_path] = z.read(name).decode('utf-8')
                except UnicodeDecodeError:
                    files[rel_path] = z.read(name)  # Binary files
    return files

def bundle_ngon(files, output_filename=OUTPUT_FILE):
    print("Bundling repository into a standalone HTML file...")
    
    index_html = files.get('index.html')
    if not index_html:
        raise FileNotFoundError("index.html not found in repository!")
    
    soup = BeautifulSoup(index_html, 'html.parser')

    # 1. Inline CSS stylesheets
    for link in soup.find_all('link', rel=re.compile(r'stylesheet', re.I)):
        href = link.get('href')
        if href and href in files:
            css_content = files[href]
            if isinstance(css_content, bytes):
                css_content = css_content.decode('utf-8')
            style_tag = soup.new_tag('style')
            style_tag.string = css_content
            link.replace_with(style_tag)
            print(f"  Inlined stylesheet: {href}")

    # 2. Inline JavaScript scripts
    for script in soup.find_all('script'):
        src = script.get('src')
        if src and src in files:
            js_content = files[src]
            if isinstance(js_content, bytes):
                js_content = js_content.decode('utf-8')
            
            # Prevent premature closing script tag issues
            js_content = js_content.replace('</script>', '<\\/script>')
            
            new_script = soup.new_tag('script')
            new_script.string = js_content
            script.replace_with(new_script)
            print(f"  Inlined script: {src}")

    # Write output
    bundled_html = str(soup)
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(bundled_html)
        
    print(f"\nSuccessfully generated standalone file: {output_filename}")
    print(f"File size: {os.path.getsize(output_filename) / (1024 * 1024):.2f} MB")

if __name__ == "__main__":
    try:
        files = download_and_extract_repo(REPO_ZIP_URL)
        bundle_ngon(files)
    except Exception as e:
        print(f"Error during bundling: {e}")
