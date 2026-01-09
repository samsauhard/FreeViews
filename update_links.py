import json
import xml.etree.ElementTree as ET
import os

def update_config_from_sitemap():
    if not os.path.exists('sitemap.xml'):
        print("sitemap.xml not found")
        return

    try:
        tree = ET.parse('sitemap.xml')
        root = tree.getroot()
        
        # Namespace for sitemap
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        blog_urls = []
        for url in root.findall('ns:url', ns):
            loc = url.find('ns:loc', ns)
            if loc is not None and '/blog/' in loc.text:
                blog_urls.append(loc.text)
        
        print(f"Found {len(blog_urls)} blog URLs.")
        
        # Update config
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            config['urls'] = blog_urls
            # Ensure proper threading/timing settings for blogs if needed
            # (Keeping existing settings for now)
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            print("Successfully updated config.json with blog URLs.")
            
    except Exception as e:
        print(f"Error parsing sitemap: {e}")

if __name__ == "__main__":
    update_config_from_sitemap()
