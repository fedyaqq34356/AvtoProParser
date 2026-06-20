# Avto.pro Auto Parts Parser

A Telegram bot system for automated parsing of auto parts from Avto.pro website with Google Sheets integration. The bot searches for parts by number, extracts offers with pricing and delivery information, and saves results to Google Sheets.

## Features

### Core Functionality
- **Automated Parsing**: Search and parse auto parts by part numbers
- **Multi-threaded Processing**: Concurrent parsing with 3 workers for faster results
- **Google Sheets Integration**: Automatic data storage and retrieval
- **Telegram Bot Interface**: User-friendly control via Telegram
- **Cookie-based Authentication**: Persistent session management
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

### Data Extraction
- Part maker/brand
- Part code/number
- Description (max 120 characters)
- Delivery time
- City/location
- Price (UAH only)
- Parse date

### Smart Filtering
- Auto-skip negotiable prices
- Filter non-UAH currencies
- Ignore invalid or zero prices
- Skip parts with missing critical data

## Requirements

- Python 3.8+
- Google Chrome browser (for Selenium)
- ChromeDriver (compatible with your Chrome version)
- Telegram Bot Token
- Google Service Account credentials
- Active Avto.pro cookies

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/avtopro-parser.git
cd avtopro-parser
```

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**

Windows:
```bash
venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Install ChromeDriver:**
   - Download from [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads)
   - Ensure version matches your Chrome browser
   - Add to system PATH or place in project directory

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_telegram_bot_token_here
```

### 2. Google Sheets Setup

Create `config.json`:
```json
{
    "spreadsheet_id": "your_google_spreadsheet_id"
}
```

**Getting Spreadsheet ID:**
From your Google Sheets URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`

### 3. Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API
4. Create Service Account credentials
5. Download JSON key file as `credentials.json`
6. Share your Google Spreadsheet with the service account email

### 4. Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create new bot with `/newbot` command
3. Copy the bot token to `.env` file

### 5. Avto.pro Cookies

Create `cookie.json` with your authenticated session:
```json
[
    {
        "name": "cookie_name",
        "value": "cookie_value",
        "domain": ".avto.pro",
        "path": "/",
        "secure": true,
        "httpOnly": true,
        "expirationDate": 1234567890
    }
]
```

**Getting cookies:**
- Use browser extension like "EditThisCookie" or "Cookie-Editor"
- Login to Avto.pro
- Export all cookies in JSON format
- Save as `cookie.json`

## Google Sheets Structure

### Sheet 1: "Номери для парсингу" (Numbers to Parse)

| Column A |
|----------|
| 12345678 |
| 87654321 |
| 11223344 |

- Contains part numbers to parse (one per row)
- No headers required
- Empty rows are ignored

### Sheet 2: "Готова таблиця" (Results Table)

Auto-generated with headers:

| number | maker | code | description | delivery | city | price | parse_date |
|--------|-------|------|-------------|----------|------|-------|------------|

- Created automatically if doesn't exist
- Overwrites existing data on each parse
- Numbers without results show "-" in all fields

## Usage

### Starting the Bot

Run the main script:
```bash
python main.py
```

Console output:
```
Bot started...
```

### Bot Commands

1. **Start the bot**: Send `/start` to your bot
2. **Begin parsing**: Click the "Старт" button
3. **Monitor progress**: Bot sends status updates
4. **View results**: Check Google Sheets after completion

### Parsing Flow

1. Bot reads numbers from "Номери для парсингу" sheet
2. Launches 3 concurrent workers
3. Each worker:
   - Opens Avto.pro with cookies
   - Searches for the part number
   - Clicks first result
   - Loads all offers (clicking "Show more")
   - Extracts data from each offer
4. Results saved to "Готова таблиця" sheet
5. Bot reports success/failure statistics

### Example Bot Interaction

```
You: /start
Bot: Вітаю! Це бот для запуску парсингу.
     Натисніть кнопку для запуску парсингу:
     [Старт]

You: [Старт]
Bot: Парсинг почався...

Bot: Парсинг закінчився

     Спарсено:
     Успішно: 45
     Не успішно: 5

     Для наступного запуску натисніть кнопку Старт
     [Старт]
```

## Project Structure

```
avtopro-parser/
├── main.py                    # Entry point
├── bot.py                     # Telegram bot logic
├── parser.py                  # Avto.pro parser class
├── worker.py                  # Worker process function
├── google_sheets.py           # Google Sheets manager
├── logger.py                  # Logging configuration
├── utils.py                   # Cookie loader utility
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
├── .gitignore                # Git ignore rules
├── config.json               # Google Sheets config (create this)
├── credentials.json          # Google service account (create this)
├── cookie.json               # Avto.pro cookies (create this)
├── logs/                     # Auto-generated log files
│   └── parser_*.log
└── README.md                 # This file
```

## How It Works

### Architecture

1. **Telegram Bot Layer** (`bot.py`)
   - Handles user interaction
   - Manages parsing state
   - Coordinates workers

2. **Worker Pool** (`worker.py`)
   - ThreadPoolExecutor with 3 workers
   - Processes numbers concurrently
   - Random delays to avoid detection

3. **Parser Engine** (`parser.py`)
   - Selenium WebDriver automation
   - Headless Chrome browser
   - Dynamic content loading
   - Smart data extraction

4. **Data Management** (`google_sheets.py`)
   - Reads input numbers
   - Writes parsed results
   - Handles missing data

### Parsing Algorithm

```
For each part number:
  1. Load Avto.pro with cookies
  2. Search for part number
  3. Click first result
  4. While "Show more" button exists:
     a. Parse visible offers
     b. Click "Show more"
     c. Wait for new content
     d. Continue parsing
  5. Return all offers
```

### Data Validation

The parser applies these filters:
- ✓ Only UAH currency
- ✓ Only numeric prices > 0
- ✗ Skip "договірна" (negotiable)
- ✗ Skip empty prices
- ✗ Skip invalid currencies

## Logging

Logs are saved in `logs/` directory with timestamps:
```
logs/parser_20240128_143052.log
```

Log levels:
- **DEBUG**: Detailed parsing steps
- **INFO**: General progress updates
- **WARNING**: Missing data or issues
- **ERROR**: Exceptions and failures

Example log output:
```
2024-01-28 14:30:52 - AvtoProParser - INFO - [Worker-0] START: 12345678
2024-01-28 14:30:55 - AvtoProParser - INFO - [Worker-0] Loaded 15 cookies
2024-01-28 14:30:58 - AvtoProParser - INFO - [Worker-0] Entered number: 12345678
2024-01-28 14:31:01 - AvtoProParser - INFO - [Worker-0] Iteration 1: +10 offers, Total: 10
2024-01-28 14:31:05 - AvtoProParser - INFO - [Worker-0] DONE: 12345678 - 25 offers
```

## Troubleshooting

### Common Issues

**Issue**: "Bot parsing error: No such file or directory: 'credentials.json'"
```
Solution: Create Google Service Account and download credentials.json
```

**Issue**: "ChromeDriver version mismatch"
```
Solution: Update ChromeDriver to match your Chrome browser version
```

**Issue**: "Worksheet 'Номери для парсингу' not found"
```
Solution: Create a sheet with exactly this name in your Google Spreadsheet
```

**Issue**: "No offers found" for all numbers
```
Solution: 
1. Check if cookies are valid and not expired
2. Login to Avto.pro manually and export fresh cookies
3. Verify part numbers exist on the website
```

**Issue**: "Parsing already in progress"
```
Solution: Wait for current parsing to finish or restart the bot
```

**Issue**: Selenium crashes or timeouts
```
Solution:
1. Increase wait times in parser.py
2. Check internet connection
3. Verify website is accessible
4. Try running with visible browser (remove --headless)
```

### Debug Mode

To see browser actions, remove headless mode in `parser.py`:
```python
# Comment out this line:
# options.add_argument('--headless')
```

### Testing Single Number

Modify `worker.py` to test individual numbers:
```python
# Test single number
results = process_number('12345678', 0, logger, 'cookie.json')
print(results)
```

## Performance

### Specifications
- **Workers**: 3 concurrent threads
- **Average speed**: ~10-15 numbers per minute
- **Timeout**: 10 seconds per element wait
- **Random delays**: 1-3 seconds between actions

### Optimization Tips
- Increase workers for faster parsing (max 5 recommended)
- Reduce random delays if Avto.pro allows
- Use faster internet connection
- Run on VPS for 24/7 availability

## Security Considerations

- **Cookie Security**: Never commit `cookie.json` to version control
- **Credentials**: Keep `credentials.json` and `.env` private
- **API Keys**: Rotate Telegram bot token regularly
- **Rate Limiting**: Respect Avto.pro's terms of service
- **Data Privacy**: Handle parsed data according to regulations

## Dependencies

```
selenium - Web browser automation
gspread - Google Sheets API client
oauth2client - Google OAuth authentication
aiogram - Telegram Bot API framework
python-dotenv - Environment variable management
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/improvement`)
5. Create Pull Request

## License

This project is licensed under the GNU General Public License v3.0 - see LICENSE file for details.

## Acknowledgments

- [Aiogram](https://aiogram.dev/) for Telegram Bot framework
- [Selenium](https://www.selenium.dev/) for web automation
- [gspread](https://gspread.readthedocs.io/) for Google Sheets integration
- [Avto.pro](https://avto.pro/) for auto parts data

## Support

For issues, questions, or suggestions:
- Open an [Issue](https://github.com/fedyaqq34356/AvtoProParser/issues)

---

**Made with ❤️ and Python**