# Daily Playbook Stock Analysis - Scheduling Setup

## 📅 Automated Schedule

The daily playbook analysis is now scheduled to run **automatically every weekday (Monday-Friday) at 8:00 PM**.

## How It Works

1. **Day-Aware**: The script automatically detects the current day of the week
2. **Reads Correct Column**: Fetches tickers from the corresponding day column in `Playbook.xlsx`
   - Monday → `Mon` column
   - Tuesday → `Tue` column
   - Wednesday → `Weds` column
   - Thursday → `Thur` column
   - Friday → `Fri` column
3. **Analyzes Stocks**: For each ticker:
   - Fetches 13 months of historical data
   - Calculates YTD and 1-year returns
   - Finds last 4 earnings dates (since July 2024)
   - Calculates post-earnings performance
4. **Generates Reports**: Creates dated CSV files with results

## Files Created

### Script Files
- `daily_playbook_analysis.py` - Main analysis script
- `com.playbook.dailyanalysis.plist` - macOS launchd configuration
- `test_daily_analysis.sh` - Manual test script

### Output Files (generated daily)
- `daily_analysis_[day]_[YYYYMMDD]_summary.csv` - Performance summary
- `daily_analysis_[day]_[YYYYMMDD]_earnings.csv` - Detailed earnings data
- `logs/daily_analysis.log` - Execution log
- `logs/daily_analysis_error.log` - Error log

## Manual Testing

To test the analysis without waiting for 8pm:

```bash
# Option 1: Run the test script
./test_daily_analysis.sh

# Option 2: Run directly with Python
python3 daily_playbook_analysis.py
```

## Managing the Scheduled Task

### Check if the task is running:
```bash
launchctl list | grep playbook
```

### View upcoming schedule:
The task will run at 8:00 PM every Monday-Friday automatically.

### Stop the scheduled task:
```bash
launchctl unload ~/Library/LaunchAgents/com.playbook.dailyanalysis.plist
```

### Start the scheduled task:
```bash
launchctl load ~/Library/LaunchAgents/com.playbook.dailyanalysis.plist
```

### Force run immediately (for testing):
```bash
launchctl start com.playbook.dailyanalysis
```

### View logs:
```bash
# View output log
tail -f logs/daily_analysis.log

# View error log
tail -f logs/daily_analysis_error.log
```

## Schedule Details

- **Frequency**: Every weekday (Monday-Friday)
- **Time**: 8:00 PM (20:00)
- **Timezone**: System local time
- **Weekend Behavior**: Script exits gracefully on weekends

## What Gets Analyzed

For each ticker in the day's column:

### A) Performance Metrics
- **YTD Return**: Year-to-date performance (%)
- **1-Year Return**: Performance over the last 12 months (%)
- **Current Price**: Latest closing price

### B) Post-Earnings Performance
- Last 4 earnings dates (since July 2024)
- Price movement after earnings:
  - **Before Market Open**: Compare same day to previous day
  - **After Market Close**: Compare next day to earnings day
- Average post-earnings return
- Win/loss ratio

## Troubleshooting

### Task Not Running?
1. Check if it's loaded: `launchctl list | grep playbook`
2. Check error logs: `cat logs/daily_analysis_error.log`
3. Verify Python path: `which python3`
4. Test manually: `./test_daily_analysis.sh`

### Missing Output Files?
- Check logs directory exists: `ls -la logs/`
- Verify script has write permissions
- Run manually to see errors: `python3 daily_playbook_analysis.py`

### Updating the Schedule
1. Edit `com.playbook.dailyanalysis.plist`
2. Reload the configuration:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.playbook.dailyanalysis.plist
   cp com.playbook.dailyanalysis.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.playbook.dailyanalysis.plist
   ```

## Dependencies

Required Python packages (install via pip):
```bash
pip3 install pandas yfinance openpyxl
```

All dependencies are listed in `requirements.txt`.

## Notes

- The script will skip execution on weekends automatically
- All paths are absolute to ensure reliability when run by launchd
- Logs are appended, not overwritten, so you can track execution history
- CSV files are timestamped to prevent overwriting previous analyses

