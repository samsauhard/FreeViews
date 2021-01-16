from multiprocessing import Pool, cpu_count, freeze_support
from selenium import webdriver
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from time import sleep
import random
import os
def get_proxies(ua):
    proxies = []
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

  # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
                        'ip':   row.find_all('td')[0].string,
                        'port': row.find_all('td')[1].string})
        #proxies.append({'ip':  '216.47.42.18',
                        #'port': '56202'})
    return proxies

def random_proxy(proxies):
  return random.choice(proxies)

# def search_string_to_query(search_string):
#     search = search_string.split(' ')
#     query = '+'.join(search)
#     return query

def search_and_click(ua,sleep_time,top5,proxy,proxies,sleep_after):


    options1 = webdriver.ChromeOptions()
    options1.add_argument("--headless") 
    options1.add_argument('--no-sandbox')
    options1.add_argument("--disable-gpu")
    options1.add_argument('--proxy-server=%s'%(proxy['ip'] + ':' + proxy['port']))
    options1.binary_location = os.environ.get('GOOGLE_CHROME_PATH')
    #options1.add_argument('user-agent=%s'%ua.random)

    driver = webdriver.Chrome(os.environ.get('CHROMEDRIVER_PATH'),options=options1)
    #options.add_experimental_option( "prefs",{'profile.managed_default_content_settings.javascript': 2})

    
        #driver = webdriver.Chrome(chrome_options=options)
    #query = search_string_to_query(search_string)
    
        #driver.get('https://www.dailymotion.com/video/x7yfnh3')
    try:  
        driver.get('https://dai.ly/x7ymznr')
        #time.sleep(3)
        #mm = driver.find_element_by_class_name('top-matter')
        #mm = driver.find_element_by_class_name('md')
        #w=driver.find_element_by_tag_name('p')
        #j = w.find_element_by_tag_name('a')
        #time.sleep(5)
        #j.click()
        sleep(105)

        print('Watched Video')
        #driver.get("https://helpx.adobe.com/flash-player.html")
        #driver.get('https://www.youtube.com/watch?v=UUwJbWtijNY')
        ## Step 2  Once your page is loaded in chrome, go to the URL where lock sign is there visit the 
        ##setting page where you will see that the flash is disabled.

## step 3 copy that link and paste below
        #driver.get("chrome://settings/content/siteDetails?site=https%3A%2F%2Fhelpx.adobe.com")

## below code is for you to reach to flash dialog box and change it to allow from block.
#       actions = ActionChains(driver)
#       actions = actions.send_keys(Keys.TAB * 12)
#       actions = actions.send_keys(Keys.SPACE)
#       actions = actions.send_keys("a")
#       actions = actions.send_keys(Keys.ENTER)    
#       actions.perform()

# ## This Step will bring you back to your original page where you want to load the flash
#       driver.back()
        
        # time.sleep(20)

        #mm.('p')
    except Exception as e:
        print(e)
    try:
        #section_list = driver.find_element_by_class_name('section-list')

        link = section_list.find_element_by_class_name('yt-uix-tile-link')

        #link.click()
    
        #sleep(sleep_time)
    
        #driver.quit()
        
        if sleep_after is not None:
            sleep(sleep_after)
    
    except:
        driver.quit()
        proxy = random.choice(proxies)
        search_string = 'ds'
        

        #search_and_click(ua,sleep_time,search_string,proxy,proxies,sleep_after)
        
def parse_line(line):
    delim_loc = line.find('=')
    return line[delim_loc+1:].strip()

def read_config(config_string):
    try:
        search_string = parse_line(config_string[0])
        min_watch = int(parse_line(config_string[1]))
        max_watch = int(parse_line(config_string[2]))
        sleep_after = int(parse_line(config_string[3]))
        views = int(parse_line(config_string[4]))
        multicore = parse_line(config_string[5])
        if multicore != 'True':
            multicore = False
        if sleep_after == 'None':
            sleep_after = None
        return search_string,sleep_after, min_watch, max_watch, views, multicore
    except:
        write_defaults()
        return 'Bad File', 'RIP', 'Bad File', 'RIP', 'Bad File', 'RIP'
    
def write_defaults():
    with open('config.txt', 'w') as config:
        config.write('search_string = Your Search Here\n')
        config.write('min_watch = 50\n')
        config.write('max_watch = 115\n')
        config.write('wait_after = 15\n')
        config.write('views = 1000\n')
        config.write('multicore = False')

write_defaults()

if __name__ == "__main__":
    freeze_support()
    with open('config.txt', 'r') as config:
        config_values = config.readlines()
    
    search_string, sleep_after, min_watch ,max_watch, views, multicore = read_config(config_values)
    if min_watch == 'Bad File':
        i = 'rip'
    elif multicore:
        threads = int(cpu_count()*0.75)
        pool = Pool(threads)
        ua = UserAgent()
        proxies = get_proxies(ua)
        for i in range(1000):
            sleep_time = random.randint(min_watch,max_watch)
            proxy = random_proxy(proxies)
            pool.apply_async(search_and_click, args=[ua,sleep_time,search_string,proxy,proxies,sleep_after])
        pool.close()
        pool.join()
    else:
        ua = UserAgent()
        proxies = get_proxies(ua)
        for i in range(1000):
            sleep_time = random.randint(min_watch,max_watch)
            proxy = random_proxy(proxies)
            search_and_click(ua,sleep_time,search_string,proxy,proxies,sleep_after)
