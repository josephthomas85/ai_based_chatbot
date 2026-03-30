import json
import os
from datetime import datetime
import random

def fix_transaction_ids():
    print("Migrating transaction IDs...")
    path = 'database/transactions.json'
    if not os.path.exists(path):
        print("No transactions to migrate.")
        return

    with open(path, 'r') as f:
        data = json.load(f)
    
    id_map = {} # old_id -> new_id
    new_transactions = []
    
    for i, tx in enumerate(data['transactions']):
        # Generate a truly unique ID
        # Format: TXN_YYYYMMDD_HHMMSS_RAND
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        rand = random.randint(1000, 9999)
        new_id = f"T{now}_{i:03d}_{rand}" 
        
        # We can also keep it simple: T10001, T10002...
        new_id = f"T{10000 + i}"
        
        tx['transactionid'] = new_id
        new_transactions.append(tx)
        
    data['transactions'] = new_transactions
    
    # Backup
    os.rename(path, path + '.bak')
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Successfully migrated {len(new_transactions)} transactions.")

if __name__ == "__main__":
    fix_transaction_ids()
