# Token Holder Raffle Selection

This Python script selects winners for a raffle based on token holdings from multiple sources, including local files and Dune Analytics for Base Ethereum. The selection is weighted by the total holdings of three tokens: AR, AISTR, and ALCH.

## Features
- Supports token balance input from CSV and Excel files.
- Integrates with Dune Analytics API to fetch token balances at specific block numbers.
- Performs weighted random selection to ensure fairness.
- Includes unit tests for core functionality.

## Requirements
- Python 3.7 or higher
- Required Python libraries:
  - `requests`
  - `pandas`
  - `openpyxl` (for Excel file handling)

## Usage
### Command Line Arguments
- `--file_path`: Path to the input file (CSV or Excel) containing token balances.
- `--num_winners`: Number of winners to select (default: 100).
- `--block_number`: Block number for fetching balances via Dune Analytics.
- `--api_key`: API key for Dune Analytics.

### Examples
#### Using a CSV File
```bash
python raffle_selection.py --file_path balances.csv --num_winners 10
```

#### Using Dune Analytics
```bash
python raffle_selection.py --block_number 12345678 --api_key YOUR_DUNE_API_KEY --num_winners 10
```

## Input File Formats
### CSV File
The CSV file should have the following columns:
```
address,token,balance
0x1,AR,100
0x1,AISTR,200
0x2,ALCH,50
```

### Excel File
The Excel file should have the same structure as the CSV file.

## Output
The script outputs the selected winners along with their token holdings:
```
Selected Winners:
Address: 0x1, Holdings: {'AR': 100, 'AISTR': 200, 'ALCH': 0}
Address: 0x2, Holdings: {'AR': 0, 'AISTR': 0, 'ALCH': 50}
```

## Testing
To run the unit tests, execute:
```bash
python -m unittest raffle_selection.py
```

