from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime
from utils import load_cookies_from_file
import re

class AvtoProParser:
    def __init__(self, logger=None, worker_id=0):
        self.logger = logger
        self.worker_id = worker_id
        
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.number = None
        self.parsed_tbody_count = 0
        
        if self.logger:
            self.logger.info(f'[Worker-{worker_id}] WebDriver initialized')
        
    def load_cookies(self, cookie_file):
        self.driver.get('https://avto.pro')
        time.sleep(1)
        
        cookies = load_cookies_from_file(cookie_file)
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        
        if self.logger:
            self.logger.info(f'[Worker-{self.worker_id}] Loaded {len(cookies)} cookies')
    
    def set_number(self, number):
        self.number = number
        self.parsed_tbody_count = 0
        
        if self.logger:
            self.logger.info(f'[Worker-{self.worker_id}] Set number: {number}')
    
    def open_main_page(self):
        self.driver.get('https://avto.pro')
        if self.logger:
            self.logger.info(f'[Worker-{self.worker_id}] Opened main page')
        
    def close_cookie_popup(self):
        try:
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, '.cookie-block__notice__button, .cookie-block button, button[class*="cookie"]')
            if cookie_button.is_displayed():
                cookie_button.click()
                time.sleep(0.5)
                if self.logger:
                    self.logger.info(f'[Worker-{self.worker_id}] Closed cookie popup')
                return True
        except:
            pass
        return False
    
    def search_number(self):
        self.close_cookie_popup()
        
        search_input = self.wait.until(
            EC.presence_of_element_located((By.ID, 'ap-search-query'))
        )
        search_input.clear()
        search_input.send_keys(self.number)
        time.sleep(1)
        
        if self.logger:
            self.logger.info(f'[Worker-{self.worker_id}] Entered number: {self.number}')
        
    def click_first_result(self):
        try:
            time.sleep(1)
            
            not_found_alert = self.driver.find_elements(By.CSS_SELECTOR, '.ap-search__alert, .ap-search__alert--blue')
            for alert in not_found_alert:
                if 'ничего не найдено' in alert.text.lower() or 'nothing found' in alert.text.lower():
                    if self.logger:
                        self.logger.warning(f'[Worker-{self.worker_id}] Nothing found alert detected')
                    return False
            
            first_result = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.ap-search__results-list a'))
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_result)
            time.sleep(0.5)
            
            try:
                first_result.click()
            except:
                self.driver.execute_script("arguments[0].click();", first_result)
            
            if self.logger:
                self.logger.info(f'[Worker-{self.worker_id}] Clicked first result')
            
            return True
        except TimeoutException:
            if self.logger:
                self.logger.warning(f'[Worker-{self.worker_id}] No results found')
            return False
    
    def check_page_type(self):
        time.sleep(2)
        
        feed_cards = self.driver.find_elements(By.CSS_SELECTOR, '.feed-card')
        if feed_cards and len(feed_cards) > 0:
            if self.logger:
                self.logger.info(f'[Worker-{self.worker_id}] Found single feed card')
            return 'card'
        
        tbodies = self.driver.find_elements(By.CSS_SELECTOR, '#js-partslist-primary tbody')
        if tbodies and len(tbodies) > 0:
            if self.logger:
                self.logger.info(f'[Worker-{self.worker_id}] Found table list with {len(tbodies)} tbody')
            return 'list'
        
        feed_page_card = self.driver.find_elements(By.CSS_SELECTOR, '.feed-pages-card')
        if feed_page_card and len(feed_page_card) > 0:
            if self.logger:
                self.logger.info(f'[Worker-{self.worker_id}] Found product info page')
            return 'info_page'
        
        if self.logger:
            self.logger.warning(f'[Worker-{self.worker_id}] No offers found on page')
        return None
    
    def check_availability_status(self):
        try:
            not_available = self.driver.find_elements(By.CSS_SELECTOR, '.feed-pages-card__info--head__not-found')
            if not_available:
                if self.logger:
                    self.logger.info(f'[Worker-{self.worker_id}] Product found but not available')
                return 'not_available'
            
            return 'available'
        except:
            return 'available'
    
    def parse_info_page(self, availability_status):
        try:
            availability = 'В наявності' if availability_status == 'available' else 'Немає в наявності'
            
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, '.ap-feed__header h1, h1.h2')
                title = title_elem.text.strip()
                parts = title.split()
                code = parts[0] if parts else self.number
                maker = ' '.join(parts[1:]) if len(parts) > 1 else ''
            except:
                code = self.number
                maker = ''
            
            description = ''
            
            try:
                params = self.driver.find_elements(By.CSS_SELECTOR, '.pro-dl__auto-grid-row')
                desc_parts = []
                for param in params:
                    try:
                        dt = param.find_element(By.TAG_NAME, 'dt').text.strip()
                        dd = param.find_element(By.TAG_NAME, 'dd').text.strip()
                        desc_parts.append(f'{dt}: {dd}')
                    except:
                        continue
                
                description = ', '.join(desc_parts)
                if len(description) > 120:
                    description = description[:120]
            except:
                description = ''
            
            parse_date = datetime.now().strftime('%d-%m-%Y')
            
            offer = {
                'number': self.number,
                'maker': maker,
                'code': code,
                'description': description,
                'delivery': '-',
                'city': '-',
                'price': '-',
                'availability': availability,
                'parse_date': parse_date
            }
            
            if self.logger:
                self.logger.info(f'[Worker-{self.worker_id}] Parsed info page: {maker} | {availability}')
            
            return [offer]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f'[Worker-{self.worker_id}] Error parsing info page: {e}')
            return []
    
    def parse_single_card(self):
        try:
            card = self.driver.find_element(By.CSS_SELECTOR, '.feed-card')
            
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, '.feed-card__title-main')
                title = title_elem.text.strip()
                parts = title.split()
                code = parts[0] if parts else self.number
                maker = ' '.join(parts[1:]) if len(parts) > 1 else ''
            except:
                code = self.number
                maker = ''
            
            try:
                description_elem = card.find_element(By.CSS_SELECTOR, '.feed-card__specs-description span')
                description = description_elem.text.strip()
                if len(description) > 120:
                    description = description[:120]
            except:
                description = ''
            
            try:
                delivery_elem = card.find_element(By.CSS_SELECTOR, '.delivery-text')
                delivery_text = delivery_elem.text.strip()
            except:
                delivery_text = ''
            
            try:
                city_elem = card.find_element(By.CSS_SELECTOR, '.font-weight-medium')
                city = city_elem.text.strip().replace(',', '').strip()
            except:
                city = ''
            
            try:
                price_elem = card.find_element(By.CSS_SELECTOR, '.pro-card__price__value strong')
                price_full_text = price_elem.text.strip().lower()
                
                if 'договір' in price_full_text or 'договор' in price_full_text or 'договірна' in price_full_text or 'договорная' in price_full_text:
                    return []
                
                price_match = re.search(r'([\d\s,.]+)', price_full_text)
                if not price_match:
                    return []
                
                price = price_match.group(1).replace(' ', '').replace(',', '.')
                
                if not price or price == '0':
                    return []
                
                if 'грн' not in price_full_text and 'uah' not in price_full_text:
                    return []
                
            except Exception as e:
                if self.logger:
                    self.logger.warning(f'[Worker-{self.worker_id}] Failed to parse price: {e}')
                return []
            
            parse_date = datetime.now().strftime('%d-%m-%Y')
            
            offer = {
                'number': self.number,
                'maker': maker,
                'code': code,
                'description': description,
                'delivery': delivery_text,
                'city': city,
                'price': price,
                'availability': 'В наявності',
                'parse_date': parse_date
            }
            
            if self.logger:
                self.logger.info(f'[Worker-{self.worker_id}] Parsed single card: {maker} | {price} UAH')
            
            return [offer]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f'[Worker-{self.worker_id}] Error parsing single card: {e}')
            return []
        
    def click_show_more_button(self):
        try:
            time.sleep(1)
            
            show_more_button = self.driver.find_element(By.CSS_SELECTOR, '.ap-feed__show-more button')
            
            if show_more_button.is_displayed() and show_more_button.is_enabled():
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more_button)
                time.sleep(1)
                
                tbodies_before = len(self.driver.find_elements(By.CSS_SELECTOR, '#js-partslist-primary tbody'))
                
                if self.logger:
                    self.logger.info(f'[Worker-{self.worker_id}] Clicking show more. Current tbody: {tbodies_before}')
                
                show_more_button.click()
                
                max_wait = 5
                start_time = time.time()
                while time.time() - start_time < max_wait:
                    time.sleep(0.5)
                    tbodies_after = len(self.driver.find_elements(By.CSS_SELECTOR, '#js-partslist-primary tbody'))
                    if tbodies_after > tbodies_before:
                        if self.logger:
                            self.logger.info(f'[Worker-{self.worker_id}] New tbody loaded: {tbodies_after}')
                        return True
                
                return True
            else:
                return False
                
        except NoSuchElementException:
            if self.logger:
                self.logger.info(f'[Worker-{self.worker_id}] Show more not found - end of list')
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f'[Worker-{self.worker_id}] Error: {e}')
            return False
        
    def parse_all_offers(self):
        page_type = self.check_page_type()
        
        if page_type == 'card':
            return self.parse_single_card()
        
        if page_type == 'list':
            results = []
            iteration = 1
            
            if self.logger:
                self.logger.info(f'[Worker-{self.worker_id}] Starting parse list')
            
            while True:
                if self.logger:
                    self.logger.info(f'[Worker-{self.worker_id}] Iteration {iteration}')
                
                tbodies = self.driver.find_elements(By.CSS_SELECTOR, '#js-partslist-primary tbody')
                total_tbodies = len(tbodies)
                
                if self.parsed_tbody_count >= total_tbodies:
                    if self.logger:
                        self.logger.info(f'[Worker-{self.worker_id}] No new tbody')
                else:
                    new_offers_count = 0
                    
                    for tbody_index in range(self.parsed_tbody_count, total_tbodies):
                        tbody = tbodies[tbody_index]
                        rows = tbody.find_elements(By.TAG_NAME, 'tr')
                        
                        if self.logger:
                            self.logger.debug(f'[Worker-{self.worker_id}] tbody[{tbody_index}]: {len(rows)} rows')
                        
                        for row_index, row in enumerate(rows):
                            try:
                                offer = self.parse_offer(row)
                                if offer:
                                    results.append(offer)
                                    new_offers_count += 1
                                    
                                    if self.logger:
                                        self.logger.debug(f'[Worker-{self.worker_id}] Parsed: {offer["maker"]} | {offer["price"]} UAH')
                                else:
                                    if self.logger:
                                        self.logger.warning(f'[Worker-{self.worker_id}] Failed row {row_index + 1}')
                                    
                            except Exception as e:
                                if self.logger:
                                    self.logger.error(f'[Worker-{self.worker_id}] Row error: {e}')
                                continue
                        
                        if self.logger:
                            self.logger.debug(f'[Worker-{self.worker_id}] tbody[{tbody_index}] done')
                    
                    self.parsed_tbody_count = total_tbodies
                    
                    if self.logger:
                        self.logger.info(f'[Worker-{self.worker_id}] Iteration {iteration}: +{new_offers_count} offers, Total: {len(results)}')
                
                if not self.click_show_more_button():
                    if self.logger:
                        self.logger.info(f'[Worker-{self.worker_id}] Parse completed')
                    break
                
                iteration += 1
                time.sleep(2)
                
            return results
        
        if page_type == 'info_page':
            availability_status = self.check_availability_status()
            return self.parse_info_page(availability_status)
        
        if self.logger:
            self.logger.warning(f'[Worker-{self.worker_id}] No content to parse - returning empty')
        return []
    
    def parse_offer(self, row):
        try:
            code_elem = row.find_element(By.CSS_SELECTOR, 'td[data-type="code"]')
            code = code_elem.text.strip()
        except:
            code = self.number
        
        try:
            maker_elem = row.find_element(By.CSS_SELECTOR, 'td[data-type="maker"] span')
            maker = maker_elem.text.strip()
        except:
            maker = ''
        
        try:
            description_elem = row.find_element(By.CSS_SELECTOR, 'td[title]')
            description = description_elem.get_attribute('title').strip()
            if len(description) > 120:
                description = description[:120]
        except:
            description = ''
        
        try:
            delivery_elem = row.find_element(By.CSS_SELECTOR, 'td[data-type="delivery"]')
            city = delivery_elem.get_attribute('data-city').strip()
            delivery_text = delivery_elem.text.strip().split('\n')[0].strip()
        except:
            city = ''
            delivery_text = ''
        
        try:
            price_elem = row.find_element(By.CSS_SELECTOR, 'td[data-type="price"]')
            price = price_elem.get_attribute('data-value').strip()
            price_text = price_elem.text.strip().lower()
            
            if not price or price == '0' or not price_text:
                return None
            
            if 'договір' in price_text or 'договор' in price_text or 'договірна' in price_text or 'договорная' in price_text:
                return None
            
            currency = price_elem.get_attribute('data-currency')
            if currency:
                currency = currency.lower()
                if 'uah' not in currency and 'грн' not in currency:
                    return None
                
        except:
            return None
        
        parse_date = datetime.now().strftime('%d-%m-%Y')
        
        return {
            'number': self.number,
            'maker': maker,
            'code': code,
            'description': description,
            'delivery': delivery_text,
            'city': city,
            'price': price,
            'availability': 'В наявності',
            'parse_date': parse_date
        }
    
    def close(self):
        if self.logger:
            self.logger.info(f'[Worker-{self.worker_id}] Closing browser')
        self.driver.quit()