import json

def load_cookies_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        cookies_data = json.load(f)
    
    cookies = []
    for cookie in cookies_data:
        cookie_dict = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie['domain'],
            'path': cookie['path'],
            'secure': cookie['secure'],
            'httpOnly': cookie['httpOnly']
        }
        
        if 'expirationDate' in cookie:
            cookie_dict['expiry'] = int(cookie['expirationDate'])
            
        cookies.append(cookie_dict)
    
    return cookies