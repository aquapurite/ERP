"""
Clean up legacy GST accounts at 2310, 2320.
These accounts shouldn't have GST names - they should be deleted or renamed.
"""

import requests

BASE_URL = "https://aquapurite-erp-api.onrender.com"
EMAIL = "themanagingdirector@aquapurite.com"
PASSWORD = "Admin@123"


def main():
    print("=" * 60)
    print("LEGACY GST ACCOUNTS CLEANUP")
    print("=" * 60)

    # Login
    print("\nLogging in...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code}")
        return

    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful!")

    # Fetch accounts
    print("\n--- Fetching accounts at 2310-2330 ---")
    resp = requests.get(f"{BASE_URL}/api/v1/accounting/accounts", headers=headers)
    accounts = resp.json() if isinstance(resp.json(), list) else resp.json().get('items', [])

    legacy_codes = ['2310', '2320', '2330']
    legacy_accounts = []

    for acc in accounts:
        if acc.get('account_code') in legacy_codes:
            legacy_accounts.append(acc)
            print(f"  Found: {acc['account_code']} - {acc['account_name']}")
            print(f"         Balance: {acc.get('current_balance', 0)}")

    if not legacy_accounts:
        print("  No legacy accounts found at 2310-2330")
        return

    # Check for transactions
    print("\n--- Checking for transactions ---")
    for acc in legacy_accounts:
        # Try to get ledger for this account
        resp = requests.get(f"{BASE_URL}/api/v1/accounting/ledger/{acc['id']}", headers=headers)
        if resp.status_code == 200:
            ledger = resp.json()
            entries = ledger.get('entries', [])
            print(f"  {acc['account_code']}: {len(entries)} transactions")
            if entries:
                print(f"    WARNING: Cannot delete - has transactions!")
        else:
            print(f"  {acc['account_code']}: Could not fetch ledger (may be empty)")

    # Delete or rename accounts
    print("\n--- Cleaning up legacy accounts ---")
    for acc in legacy_accounts:
        balance = float(acc.get('current_balance', 0) or 0)

        if balance == 0:
            print(f"\n  Attempting to delete {acc['account_code']}: {acc['account_name']}")
            resp = requests.delete(f"{BASE_URL}/api/v1/accounting/accounts/{acc['id']}", headers=headers)
            if resp.status_code in [200, 204]:
                print(f"    ✅ Deleted successfully")
            else:
                print(f"    ❌ Delete failed: {resp.status_code} - {resp.text[:200]}")
                # Try renaming instead
                print(f"    Trying to rename instead...")
                resp = requests.put(
                    f"{BASE_URL}/api/v1/accounting/accounts/{acc['id']}",
                    json={"account_name": f"LEGACY - {acc['account_name']} (DO NOT USE)"},
                    headers=headers
                )
                if resp.status_code in [200, 201]:
                    print(f"    ✅ Renamed to indicate legacy status")
                else:
                    print(f"    ❌ Rename failed: {resp.status_code}")
        else:
            print(f"\n  {acc['account_code']} has balance {balance} - cannot delete")
            print(f"    Renaming to indicate legacy status...")
            resp = requests.put(
                f"{BASE_URL}/api/v1/accounting/accounts/{acc['id']}",
                json={"account_name": f"LEGACY - {acc['account_name']} (DO NOT USE)"},
                headers=headers
            )
            if resp.status_code in [200, 201]:
                print(f"    ✅ Renamed")
            else:
                print(f"    ❌ Rename failed: {resp.status_code}")

    print("\n✅ Legacy cleanup completed!")


if __name__ == "__main__":
    main()
