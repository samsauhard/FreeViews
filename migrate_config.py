import json

def migrate():
    try:
        with open('config.json', 'r') as f:
            data = json.load(f)

        # Move current urls to blog_urls if not already done
        if 'blog_urls' not in data:
            data['blog_urls'] = data.get('urls', [])
        
        # Set primary urls
        data['primary_urls'] = [
            "https://rumble.com/v734vwa-gold-demand-supply-live-chart-with-strategy-76-accuracy.html"
        ]

        # Clear old urls key to force use of new specific keys
        data['urls'] = [] 
        
        # Ensure other settings are preserved
        
        with open('config.json', 'w') as f:
            json.dump(data, f, indent=4)
            
        print("Config migrated successfully.")
        
    except Exception as e:
        print(f"Error migrating config: {e}")

if __name__ == "__main__":
    migrate()
