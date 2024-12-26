import random
import csv
import argparse
from collections import defaultdict
import unittest
import requests

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

def fetch_holders_from_dune(block_number, api_key):
    """Fetch real token holders from Dune Analytics for specific tokens."""
    token_addresses = [
        "0x3e43cB385A6925986e7ea0f0dcdAEc06673d4e10",
        "0x20ef84969f6d81Ff74AE4591c331858b20AD82CD",
        "0x2b0772BEa2757624287ffc7feB92D03aeAE6F12D",
    ]

    token_addresses_sql = ", ".join([f"'{token}'" for token in token_addresses])

    sql_query = f"""
    SELECT address, token, SUM(balance) as balance
    FROM ethereum.token_balances
    WHERE block_number = {block_number} AND token IN ({token_addresses_sql})
    GROUP BY address, token;
    """

    response = query_dune(sql_query, api_key)

    balances = defaultdict(lambda: {token: 0 for token in token_addresses})
    for row in response['data']['rows']:
        address = row['address']
        token = row['token']
        balance = float(row['balance'])
        if token in balances[address]:
            balances[address][token] += balance
    return balances

def calculate_weights(balances):
    """Calculate weights based on total holdings of the specified tokens."""
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

    winners = random.choices(weighted_addresses, weights=probabilities, k=num_winners)
    return winners

def main(block_number=None, api_key=None, num_winners=100):
    if block_number and api_key:
        # Step 1: Fetch balances from Dune Analytics
        balances = fetch_holders_from_dune(block_number, api_key)
    else:
        raise ValueError("Block number and API key must be provided to fetch real token holders.")

    # Step 2: Calculate weights
    weights = calculate_weights(balances)

    # Step 3: Perform weighted random selection
    winners = weighted_random_selection(weights, num_winners)

    # Step 4: Display results
    results = [(winner, balances[winner]) for winner in winners]
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run token holder raffle selection using Dune Analytics.")
    parser.add_argument("--block_number", type=int, required=True, help="Block number for Dune query snapshot.")
    parser.add_argument("--api_key", type=str, required=True, help="Dune API key for querying blockchain data.")
    parser.add_argument("--num_winners", type=int, default=100, help="Number of winners to select.")

    args = parser.parse_args()

    try:
        results = main(block_number=args.block_number, api_key=args.api_key, num_winners=args.num_winners)
        print("Selected Winners:")
        for winner, holdings in results:
            print(f"Address: {winner}, Holdings: {holdings}")
    except ValueError as e:
        print(e)
    except Exception as ex:
        print(f"Error: {ex}")

class TestRaffleSelection(unittest.TestCase):

    def test_calculate_weights(self):
        """Test calculation of weights."""
        balances = {
            '0x1': {
                "0x3e43cB385A6925986e7ea0f0dcdAEc06673d4e10": 100,
                "0x20ef84969f6d81Ff74AE4591c331858b20AD82CD": 200,
                "0x2b0772BEa2757624287ffc7feB92D03aeAE6F12D": 0,
            },
            '0x2': {
                "0x3e43cB385A6925986e7ea0f0dcdAEc06673d4e10": 0,
                "0x20ef84969f6d81Ff74AE4591c331858b20AD82CD": 0,
                "0x2b0772BEa2757624287ffc7feB92D03aeAE6F12D": 50,
            },
        }
        weights = calculate_weights(balances)
        self.assertEqual(weights['0x1'], 300)
        self.assertEqual(weights['0x2'], 50)

    def test_weighted_random_selection(self):
        """Test weighted random selection."""
        weights = {'0x1': 300, '0x2': 50}
        winners = weighted_random_selection(weights, 1)
        self.assertIn(winners[0], weights.keys())

if __name__ == "__main__":
    unittest.main()
