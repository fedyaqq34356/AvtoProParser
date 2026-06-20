import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime

class GoogleSheetsManager:
    def __init__(self, credentials_file, config_file='config.json'):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        self.client = gspread.authorize(creds)
        self.spreadsheet = None
        
        with open(config_file, 'r') as f:
            config = json.load(f)
            spreadsheet_id = config['spreadsheet_id']
        
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        
    def get_numbers_to_parse(self):
        try:
            worksheet = self.spreadsheet.worksheet('Номери для парсингу')
            values = worksheet.col_values(1)
            numbers = [v.strip() for v in values if v.strip()]
            return numbers
        except:
            return []
    
    def save_results(self, results, all_numbers):
        try:
            worksheet = self.spreadsheet.worksheet('Готова таблиця')
        except:
            worksheet = self.spreadsheet.add_worksheet(title='Готова таблиця', rows=1000, cols=10)
        
        worksheet.clear()
        
        headers = ['номер', 'виробник', 'код', 'опис', 'доставка', 'місто', 'ціна', 'наявність', 'дата парсингу']
        data = [headers]
        
        numbers_with_results = set()
        for result in results:
            numbers_with_results.add(result.get('number'))
            row = [
                result.get('number', ''),
                result.get('maker', ''),
                result.get('code', ''),
                result.get('description', ''),
                result.get('delivery', ''),
                result.get('city', ''),
                result.get('price', ''),
                result.get('availability', ''),
                result.get('parse_date', '')
            ]
            data.append(row)
        
        for number in all_numbers:
            if number not in numbers_with_results:
                parse_date = datetime.now().strftime('%d-%m-%Y')
                row = [number, '-', '-', '-', '-', '-', '-', '-', parse_date]
                data.append(row)
        
        worksheet.update('A1', data)
        
        self.save_to_history(results, all_numbers)
    
    def save_to_history(self, results, all_numbers):
        try:
            history_worksheet = self.spreadsheet.worksheet('Історія')
        except:
            history_worksheet = self.spreadsheet.add_worksheet(title='Історія', rows=5000, cols=10)
            headers = ['номер', 'виробник', 'код', 'опис', 'доставка', 'місто', 'ціна', 'наявність', 'дата парсингу']
            history_worksheet.update('A1', [headers])
        
        existing_data = history_worksheet.get_all_values()
        next_row = len(existing_data) + 1
        
        new_data = []
        numbers_with_results = set()
        
        for result in results:
            numbers_with_results.add(result.get('number'))
            row = [
                result.get('number', ''),
                result.get('maker', ''),
                result.get('code', ''),
                result.get('description', ''),
                result.get('delivery', ''),
                result.get('city', ''),
                result.get('price', ''),
                result.get('availability', ''),
                result.get('parse_date', '')
            ]
            new_data.append(row)
        
        for number in all_numbers:
            if number not in numbers_with_results:
                parse_date = datetime.now().strftime('%d-%m-%Y')
                row = [number, '-', '-', '-', '-', '-', '-', '-', parse_date]
                new_data.append(row)
        
        if new_data:
            history_worksheet.append_rows(new_data)