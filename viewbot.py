import json
import logging
import random
import time
import os
import requests
import string
import zipfile
import threading
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("viewbot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CONFIG_FILE = 'config.json'
USAGE_FILE = 'proxy_usage.json'

REFERRERS = [
    "https://www.google.com/",
    "https://www.youtube.com/",
    "https://www.facebook.com/",
    "https://twitter.com/",
    "https://www.reddit.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://www.instagram.com/",
    "https://www.tiktok.com/",
    "https://www.pinterest.com/",
    "https://www.linkedin.com/",
    "https://www.twitch.tv/",
    "https://discord.com/"
]

# Concurrency Control
concurrency_manager = None
driver_install_lock = threading.Lock()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"{CONFIG_FILE} not found!")
        return None
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        if 'url' in config and 'urls' not in config:
            config['urls'] = [config['url']]
        return config

def load_proxy_usage():
    if not os.path.exists(USAGE_FILE):
        return {}
    try:
        with open(USAGE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_proxy_usage(usage_data):
    try:
        with open(USAGE_FILE, 'w') as f:
            json.dump(usage_data, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save usage data: {e}")

def get_proxies():
    proxies = []
    if os.path.exists('proxies.txt'):
        with open('proxies.txt', 'r') as f:
            lines = f.readlines()
            proxies = [line.strip() for line in lines if line.strip()]
            if proxies:
                return proxies
    
    logger.info("Scraping proxies from sslproxies.org...")
    try:
        ua = UserAgent()
        req_url = 'https://www.sslproxies.org/'
        headers = {'User-Agent': ua.random}
        response = requests.get(req_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        if table:
            for row in table.find_all('tr')[1:]:
                 cols = row.find_all('td')
                 if len(cols) >= 2:
                     ip = cols[0].text.strip()
                     port = cols[1].text.strip()
                     proxies.append(f"{ip}:{port}")
    except Exception as e:
        logger.error(f"Error fetching proxies: {e}")

    return proxies

def check_proxy_usage(proxy, urls):
    usage = load_proxy_usage()
    allowed_urls = []
    for url in urls:
        key = f"{proxy}|{url}"
        count = usage.get(key, 0)
        if count < 10:
            allowed_urls.append(url)
    return allowed_urls

def increment_proxy_usage(proxy, url):
    usage = load_proxy_usage()
    key = f"{proxy}|{url}"
    usage[key] = usage.get(key, 0) + 1
    save_proxy_usage(usage)

def create_proxy_auth_extension(proxy_string):
    try:
        parts = proxy_string.split(':')
        if len(parts) < 4:
            return None
        ip, port, user, password = parts[0], parts[1], parts[2], parts[3]
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": ["proxy", "tabs", "unlimitedStorage", "storage", "<all_urls>", "webRequest", "webRequestBlocking"],
            "background": {"scripts": ["background.js"]},
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (ip, port, user, password)

        import uuid
        safe_ip = ip.replace('.', '_')
        plugin_file = f"proxy_auth_plugin_{safe_ip}_{port}_{uuid.uuid4()}.zip"
        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        return plugin_file
    except Exception as e:
        logger.error(f"Failed to create proxy extension: {e}")
        return None

def get_driver(headless=False, proxy=None):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    width = random.randint(1024, 1920)
    height = random.randint(768, 1080)
    options.add_argument(f"--window-size={width},{height}")

    extension_path = None
    if proxy:
        if len(proxy.split(':')) == 4:
             extension_path = create_proxy_auth_extension(proxy)
             if extension_path:
                 options.add_extension(extension_path)
             else:
                 logger.error("Failed to create auth extension")
        else:
            options.add_argument(f'--proxy-server={proxy}')
    
    ua = UserAgent()
    options.add_argument(f'user-agent={ua.random}')

    try:
        global driver_install_lock
        with driver_install_lock:
             manager = ChromeDriverManager()
             driver_path = manager.install()
        if "THIRD_PARTY_NOTICES" in driver_path:
            driver_path = os.path.join(os.path.dirname(driver_path), "chromedriver.exe")
        
        service = ChromeService(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"""
        })
        return driver, extension_path
    except Exception as e:
        logger.error(f"Failed to initialize driver: {e}")
        return None, None

def check_and_skip_ad(driver):
    skipped = False
    try:
        for _ in range(2):
            skip_btns = driver.find_elements(By.CSS_SELECTOR, 'div[aria-label="Skip Ad"]')
            for btn in skip_btns:
                try:
                    logger.info("Skip Ad detect! Clicking...")
                    driver.execute_script("arguments[0].click();", btn)
                    skipped = True
                    time.sleep(1)
                except:
                    pass
            if not skip_btns:
                break
            time.sleep(0.5)
    except Exception:
        pass
    return skipped

def simulate_human_behavior(driver):
    """
    Simulates natural human reading behavior:
    - Mostly scrolls down (reading).
    - Occasionally scrolls up (re-reading).
    - Varies scroll speed and pauses.
    """
    try:
        action = ActionChains(driver)
        
        # Determine direction: 70% chance down, 30% chance up
        direction = 1 if random.random() < 0.7 else -1
        
        # Scroll Amount
        scroll_amount = random.randint(150, 600) * direction
        
        # Execute Scroll
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        
        # Random Reading Pause
        time.sleep(random.uniform(1.5, 8.0))
        
        # Occasional Interaction (Hover)
        if random.random() < 0.3:
            elements = driver.find_elements(By.TAG_NAME, 'a')
            if elements:
                try:
                    # Pick visible element near viewport center ideally, but random is okay
                    el = random.choice(elements[:20]) 
                    action.move_to_element(el).perform()
                    time.sleep(random.uniform(0.5, 1.5))
                except:
                    pass
                    
    except Exception as e:
        pass

def inject_fake_cookies(driver):
    try:
        ga_id = f"GA1.2.{random.randint(100000000, 999999999)}.{random.randint(1600000000, 1700000000)}"
        script = f"""
            document.cookie = "_ga={ga_id}; path=/; domain=.{driver.execute_script("return document.domain")}";
        """
        driver.execute_script(script)
    except Exception:
        pass

def watch_session(config, proxy=None, max_duration_override=None):
    driver = None
    extension_file = None
    
    # URL Selection Logic
    primary_urls = config.get('primary_urls', [])
    if not primary_urls:
        # Fallback to 'urls' if primary not set, for backward compatibility
        primary_urls = config.get('urls', [])
        
    blog_urls = config.get('blog_urls', [])
    
    # Check proxy usage only against PRIMARY urls (the target)
    allowed_primary = check_proxy_usage(proxy, primary_urls) if proxy else primary_urls
    
    if not allowed_primary:
        return

    try:
        driver, extension_file = get_driver(headless=config.get('headless', False), proxy=proxy)
        if not driver:
            return

        # Setup Tabs
        # Tab 0: Primary (Target)
        # Tab 1: Secondary (Blog/Random) - Interactive browsing
        
        # Pick ONE primary URL to focus on for this session (simulating a user watching one stream)
        target_url = random.choice(allowed_primary)
        
        try:
            # Open Primary in Tab 0
            logger.info(f"Navigating to Target: {target_url}")
            driver.get(target_url)
            inject_fake_cookies(driver)
            
            if proxy:
                increment_proxy_usage(proxy, target_url)
            
            # Open Secondary in Tab 1 (if blog urls exist)
            if blog_urls:
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                
                blog_url = random.choice(blog_urls)
                logger.info(f"Navigating to Blog: {blog_url}")
                driver.get(blog_url)
                inject_fake_cookies(driver)
                
                # Switch back to primary initially
                driver.switch_to.window(driver.window_handles[0])
                
        except Exception as e:
            logger.error(f"Navigation Error: {e}")

        # Watch Duration Setup
        min_watch = config.get('min_watch_duration', 30)
        config_max = config.get('max_watch_duration', 1800)
        actual_max = max_duration_override if max_duration_override else config_max
        if actual_max > 1800: actual_max = 1800
        
        if min_watch > actual_max:
            min_watch = max(30, actual_max - 60)
            
        watch_time = random.randint(min_watch, actual_max)
        logger.info(f"Session started. Target Duration: {watch_time}s")
        
        start_time = time.time()
        while time.time() - start_time < watch_time:
            # Active Tab Rotation
            # 80% chance to be on Primary (Tab 0), 20% on Blog (Tab 1)
            handles = driver.window_handles
            if len(handles) > 1:
                if random.random() < 0.8:
                    driver.switch_to.window(handles[0]) # Primary
                else:
                    driver.switch_to.window(handles[1]) # Blog
            elif handles:
                driver.switch_to.window(handles[0])

            try:
                current_url = driver.current_url
                
                # Ad Skipping (Only relevant on Primary usually, but check anyway)
                if check_and_skip_ad(driver):
                    logger.info("Ad skipped! Extending watch.")
                    elapsed = time.time() - start_time
                    if (watch_time - elapsed) < 60:
                        new_watch = watch_time + 60
                        if new_watch <= actual_max + 120:
                            watch_time = new_watch
                            
                simulate_human_behavior(driver)
                time.sleep(random.uniform(5, 15)) # Longer intervals between actions
                
            except Exception:
                pass
                
    except Exception as e:
        logger.error(f"Session Error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        if extension_file and os.path.exists(extension_file):
            try:
                os.remove(extension_file)
            except:
                pass

def worker(config, worker_id):
    time.sleep(worker_id * 2) # Stagger start
    logger.info(f"Worker {worker_id} started loop")
    
    while True:
        try:
            # Dynamic Concurrency Check
            # Pause if we are above the target thread count unless we are a "reserved" short session worker
            # We treat workers 0-4 as "reserved" for short sessions typically, so maybe exempt them or just let them run
            target = concurrency_manager.target_threads
            active = concurrency_manager.active_threads
            
            # Simple check, if we are just "extra" threads, we might pause
            # For simplicity, if random chance says pause, or strict limit:
            if active > target:
                 # If we are a higher ID thread, sleep
                 if worker_id >= target:
                     time.sleep(30)
                     continue

            proxy = get_proxies() # Get list of proxies, then pick ONE that is available
            # Note: get_proxy() was not defined in previous context, using local logic or get_proxies()
            proxies = get_proxies()
            if not proxies:
                logger.error(f"Worker {worker_id}: No proxies found")
                time.sleep(60)
                continue

            # Select a valid proxy
            proxy = None
            random.shuffle(proxies)
            for p in proxies:
                 # Check usage against primary urls (backward compat with logic inside watch_session but we do it here to pick)
                 pri_urls = config.get('primary_urls', config.get('urls', []))
                 if check_proxy_usage(p, pri_urls):
                     proxy = {'ip': p.split(':')[0], 'port': p.split(':')[1]}
                     if len(p.split(':')) >= 4:
                         proxy['user'] = p.split(':')[2]
                         proxy['pass'] = p.split(':')[3]
                     break
            
            if not proxy:
                 logger.warning(f"Worker {worker_id}: No available proxy (limit reached)")
                 time.sleep(30)
                 continue
                
            selected_proxy = f"{proxy['ip']}:{proxy['port']}"
            if proxy.get('user'):
                 selected_proxy += f":{proxy['user']}:{proxy['pass']}"
            
            logger.info(f"Worker {worker_id} selected proxy: {selected_proxy}. Attempting session...")
            
            with concurrency_manager.track_active():
                 watch_session(config, selected_proxy)
                 
            logger.info(f"Worker {worker_id} session finished.")

        except Exception as e:
            logger.error(f"Worker {worker_id} Error: {e}")
            time.sleep(30)
            
            sleep_after = config.get('sleep_after', 15)
            time.sleep(sleep_after)
            
        except Exception as e:
            logger.error(f"Worker {worker_id} Error: {e}")
            time.sleep(5)

class ConcurrencyManager:
    def __init__(self, max_threads, min_threads=3):
        self.max_threads = max_threads
        self.min_threads = min_threads
        self.target_threads = random.randint(min_threads, max_threads)
        self.active_threads = 0
        self.lock = threading.Lock()
        self.running = True
        
    def start(self):
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
        logger.info(f"Dynamic Concurrency Manager started. Range: {self.min_threads}-{self.max_threads}")

    def _loop(self):
        while self.running:
            new_target = random.randint(self.min_threads, self.max_threads)
            self.target_threads = new_target
            logger.info(f"Updated Dynamic Target Threads: {new_target} (Current Active: {self.active_threads})")
            time.sleep(random.randint(120, 300))

    def track_active(self):
        return self.ActiveContext(self)

    class ActiveContext:
        def __init__(self, manager):
            self.manager = manager
        
        def __enter__(self):
            with self.manager.lock:
                self.manager.active_threads += 1
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            with self.manager.lock:
                self.manager.active_threads -= 1

def main():
    config = load_config()
    if not config:
        return

    max_threads = config.get('threads', 1)
    
    if max_threads > 1:
        min_limit = 3 if max_threads >= 3 else 1
        global concurrency_manager
        concurrency_manager = ConcurrencyManager(max_threads, min_limit)
        concurrency_manager.start()
    else:
        # Fallback for single thread or no concurrency dynamics
        concurrency_manager = ConcurrencyManager(1, 1) # passive
        concurrency_manager.target_threads = 1
    
    logger.info(f"Starting {max_threads} worker threads...")
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for i in range(max_threads):
            executor.submit(worker, config, i) # Pass worker_id
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping...")

if __name__ == "__main__":
    main()
