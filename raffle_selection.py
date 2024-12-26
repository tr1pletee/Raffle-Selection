import random
import csv
import argparse
from collections import defaultdict
import requests

SQL_QUERY = """
SELECT
    evt_tx_from,
    evt_tx_to,
    value / pow(10, 18) as value,
    evt_block_number,
    CASE
        WHEN contract_address = '0x3e43cB385A6925986e7ea0f0dcdAEc06673d4e10' THEN 'AR'
        WHEN contract_address = '0x20ef84969f6d81Ff74AE4591c331858b20AD82CD' THEN 'AiSTR'
        WHEN contract_address = '0x2b0772BEa2757624287ffc7feB92D03aeAE6F12D' THEN 'ALCH'
        ELSE 'Unknown'
    END as token
FROM erc20_base.evt_transfer
WHERE contract_address IN (
    '0x3e43cB385A6925986e7ea0f0dcdAEc06673d4e10',
    '0x20ef84969f6d81Ff74AE4591c331858b20AD82CD',
    '0x2b0772BEa2757624287ffc7feB92D03aeAE6F12D'
)
AND evt_tx_to NOT IN (
    '0x197ecb5c176aD4f6e77894913a94c5145416f148',
    '0xF5677B22454dEe978b2Eb908d6a17923F5658a79',
    '0x3fdD9A4b3CA4a99e3dfE931e3973C2aC37B45BE9'
)
AND evt_block_number <= 24223297;
"""

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

def fetch_holders_from_dune(api_key):
    """Fetch real token holders using the updated Dune query."""
    response = query_dune(SQL_QUERY, api_key)

    balances = defaultdict(lambda: {'AR': 0, 'AiSTR': 0, 'ALCH': 0})
    for row in response['data']['rows']:
        address = row['evt_tx_to']
        token = row['token']
        value = float(row['value'])
        if token in balances[address]:
            balances[address][token] += value
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

def main(api_key=None, num_winners=100):
    if api_key:
        # Step 1: Fetch balances from Dune Analytics
        balances = fetch_holders_from_dune(api_key)
    else:
        raise ValueError("API key must be provided to fetch real token holders.")

    # Step 2: Calculate weights
    weights = calculate_weights(balances)

    # Step 3: Perform weighted random selection
    winners = weighted_random_selection(weights, num_winners)

    # Step 4: Display results
    results = [(winner, balances[winner]) for winner in winners]
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run token holder raffle selection using Dune Analytics.")
    parser.add_argument("--api_key", type=str, required=True, help="Dune API key for querying blockchain data.")
    parser.add_argument("--num_winners", type=int, default=100, help="Number of winners to select.")

    args = parser.parse_args()

    try:
        results = main(api_key=args.api_key, num_winners=args.num_winners)
        print("Selected Winners:")
        for winner, holdings in results:
            print(f"Address: {winner}, Holdings: {holdings}")
    except ValueError as e:
        print(e)
    except Exception as ex:
        print(f"Error: {ex}")
