"""
TxRanker: Ранжирование входящих транзакций по "весу" отправителей.
"""

import requests
import argparse

def get_transactions(address):
    url = f"https://api.blockchair.com/bitcoin/dashboards/address/{address}"
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception("Ошибка получения транзакций")
    return r.json()["data"][address]["transactions"]

def get_transaction_inputs(txid):
    url = f"https://api.blockchair.com/bitcoin/raw/transaction/{txid}"
    r = requests.get(url)
    if r.status_code != 200:
        return []
    try:
        vin = r.json()["data"][txid]["decoded_raw_transaction"]["vin"]
        input_addresses = []
        for i in vin:
            prevout = i.get("prev_out", {})
            input_addresses.extend(prevout.get("addresses", []))
        return input_addresses
    except:
        return []

def get_address_value(address):
    url = f"https://api.blockchair.com/bitcoin/dashboards/address/{address}"
    r = requests.get(url)
    if r.status_code != 200:
        return 0
    try:
        data = r.json()["data"][address]["address"]
        total_sent = data.get("sent", 0)
        total_received = data.get("received", 0)
        return (total_sent + total_received) / 1e8
    except:
        return 0

def rank_transactions(address):
    print(f"🏷️ Ранжирование входящих транзакций для: {address}")
    txs = get_transactions(address)
    results = []

    for txid in txs[:20]:  # анализируем последние 20 транзакций
        senders = get_transaction_inputs(txid)
        sender_weights = [get_address_value(sender) for sender in senders if sender != address]

        if sender_weights:
            total_sender_value = sum(sender_weights)
            results.append((txid, round(total_sender_value, 5)))

    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

    for txid, weight in sorted_results:
        print(f"🔹 TXID: {txid} | вес отправителя: {weight:.5f} BTC")

    if not sorted_results:
        print("Нет транзакций с доступными данными для анализа.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TxRanker — Ранжирует входящие транзакции по активности отправителей.")
    parser.add_argument("address", help="Bitcoin-адрес")
    args = parser.parse_args()
    rank_transactions(args.address)
