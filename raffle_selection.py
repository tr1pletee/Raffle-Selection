import random
import csv
import argparse
from collections import defaultdict
import unittest
import requests

def load_token_balances(file_path):
    """Load token balances from a file, automatically detecting the format."""
    if file_path.endswith(".csv"):
        return load_token_balances_csv(file_path)
    elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
        return load_token_balances_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please provide a .csv or .xlsx file.")

def load_token_balances_csv(file_path):
    """Load balances from a CSV file."""
    balances = defaultdict(lambda: {'AR': 0, 'AISTR': 0, 'ALCH': 0})
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            address = row['address']
            token = row['token']
            balance = float(row['balance'])
            if token in balances[address]:
                balances[address][token] += balance
    return balances

def load_token_balances_excel(file_path):
    """Load balances from an Excel file."""
    import pandas as pd
    balances = defaultdict(lambda: {'AR': 0, 'AISTR': 0, 'ALCH': 0})
    data = pd.read_excel(file_path)
    for _, row in data.iterrows():
        address = row['address']
        token = row['token']
        balance = float(row['balance'])
        if token in balances[address]:
            balances[address][token] += balance
    return balances

def calculate_weights(balances):
    """Calculate weights based on total holdings of AR, AISTR, and ALCH."""
    weights = {}
    for address, holdings in balances.items():
        total_balance = sum(holdings.values())
        if total_balance > 0:
            weights[address] = total_balance
    return weights

def weighted_random_selection(weights, num_winners):
    """Select winners based on weighted random sampling."""
    total_weight = sum(weights.values())
    weighted_addresses = list(weights.keys())
    probabilities = [weights[addr] / total_weight for addr in weighted_addresses]

    # Use random.choices for weighted sampling
    winners = random.choices(weighted_addresses, weights=probabilities, k=num_winners)
    return winners

def query_dune(sql_query, api_key):
    """Query Dune Analytics using the API."""
    url = "https://api.dune.com/api/v1/query"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"sql": sql_query}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Dune API query failed with status {response.status_code}: {response.text}")

def get_snapshot_balances_from_dune(block_number, api_key):
    """Fetch token balances from Dune Analytics specifically for Base Ethereum."""
    sql_query = f"""
    SELECT address, token, SUM(balance) as balance
    FROM base_eth_token_balances
    WHERE block_number = {block_number}
    GROUP BY address, token;
    """
    result = query_dune(sql_query, api_key)

    balances = defaultdict(lambda: {'AR': 0, 'AISTR': 0, 'ALCH': 0})
    for row in result['data']['rows']:
        address = row['address']
        token = row['token']
        balance = float(row['balance'])
        if token in balances[address]:
            balances[address][token] += balance

    return balances

def main(file_path=None, num_winners=100, block_number=None, api_key=None):
    if api_key and block_number:
        # Step 1: Fetch balances using Dune API
        balances = get_snapshot_balances_from_dune(block_number, api_key)
    elif file_path:
        # Step 1: Load balances from the file (this is pre-snapshot data)
        balances = load_token_balances(file_path)
    else:
        raise ValueError("Either a file path or Dune API key with block number must be provided.")

    # Step 2: Calculate weights
    weights = calculate_weights(balances)

    # Step 3: Perform weighted random selection
    winners = weighted_random_selection(weights, num_winners)

    # Step 4: Display results
    results = [(winner, balances[winner]) for winner in winners]
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run token holder raffle selection.")
    parser.add_argument("--file_path", type=str, help="Path to CSV or Excel file containing token balances.")
    parser.add_argument("--num_winners", type=int, default=100, help="Number of winners to select.")
    parser.add_argument("--block_number", type=int, help="Block number for Dune query snapshot.")
    parser.add_argument("--api_key", type=str, help="Dune API key for querying blockchain data.")

    args = parser.parse_args()

    try:
        results = main(file_path=args.file_path, num_winners=args.num_winners, block_number=args.block_number, api_key=args.api_key)
        print("Selected Winners:")
        for winner, holdings in results:
            print(f"Address: {winner}, Holdings: {holdings}")
    except ValueError as e:
        print(e)
    except Exception as ex:
        print(f"Error: {ex}")

class TestRaffleSelection(unittest.TestCase):

    def test_load_token_balances_csv(self):
        """Test loading of token balances from a CSV file."""
        test_csv = "test_balances.csv"
        with open(test_csv, 'w') as f:
            f.write("address,token,balance\n")
            f.write("0x1,AR,100\n")
            f.write("0x1,AISTR,200\n")
            f.write("0x2,ALCH,50\n")
        
        balances = load_token_balances_csv(test_csv)
        self.assertEqual(balances['0x1']['AR'], 100)
        self.assertEqual(balances['0x1']['AISTR'], 200)
        self.assertEqual(balances['0x2']['ALCH'], 50)

    def test_calculate_weights(self):
        """Test calculation of weights."""
        balances = {
            '0x1': {'AR': 100, 'AISTR': 200, 'ALCH': 0},
            '0x2': {'AR': 0, 'AISTR': 0, 'ALCH': 50},
        }
        weights = calculate_weights(balances)
        self.assertEqual(weights['0x1'], 300)
        self.assertEqual(weights['0x2'], 50)

    def test_weighted_random_selection(self):
        """Test weighted random selection."""
        weights = {'0x1': 300, '0x2': 50}
        winners = weighted_random_selection(weights, 1)
        self.assertIn(winners[0], weights.keys())

    def test_query_dune(self):
        """Test Dune query functionality."""
        sql_query = "SELECT 1 as dummy_column;"
        api_key = "your_dune_api_key"
        try:
            result = query_dune(sql_query, api_key)
            self.assertIn('data', result)
        except Exception as e:
            self.fail(f"Dune query test failed with error: {e}")

    def test_main_with_dune(self):
        """Test the main function with Dune API integration."""
        api_key = "your_dune_api_key"
        block_number = 12345678
        try:
            results = main(None, 1, block_number, api_key)
            self.assertEqual(len(results), 1)
        except Exception as e:
            self.fail(f"Main function with Dune API failed: {e}")

if __name__ == "__main__":
    unittest.main()
