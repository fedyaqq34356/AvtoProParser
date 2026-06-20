from parser import AvtoProParser
import time
import random

def process_number(number, worker_id, logger, cookie_file):
    parser = None
    try:
        delay = random.uniform(1, 3)
        logger.info(f'[Worker-{worker_id}] Delay {delay:.2f}s before START')
        time.sleep(delay)
        
        logger.info(f'[Worker-{worker_id}] START: {number}')
        
        parser = AvtoProParser(logger=logger, worker_id=worker_id)
        
        delay = random.uniform(1, 3)
        logger.info(f'[Worker-{worker_id}] Random delay {delay:.2f}s')
        time.sleep(delay)
        
        parser.load_cookies(cookie_file)
        parser.set_number(number)
        
        parser.open_main_page()
        
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
        parser.search_number()
        
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
        if not parser.click_first_result():
            logger.warning(f'[Worker-{worker_id}] No offers for {number}')
            return []
        
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
        results = parser.parse_all_offers()
        
        if results:
            logger.info(f'[Worker-{worker_id}] DONE: {number} - {len(results)} offers')
            return results
        else:
            logger.warning(f'[Worker-{worker_id}] No offers for {number}')
            return []
            
    except Exception as e:
        logger.exception(f'[Worker-{worker_id}] ERROR: {number} - {e}')
        return []
    finally:
        if parser:
            parser.close()