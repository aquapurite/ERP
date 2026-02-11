"""
Execute Chart of Accounts Cleanup.

This script fixes the GST account codes in the production database:
1. Renames accounts at 1510-1530 from GST to Fixed Assets
2. Creates correct GST Input accounts at 1400-1430
3. Creates correct GST Output accounts at 2210-2230
4. Fixes account 1200 to be Inventory (not GST)
"""

import requests
from datetime import datetime
import json

BASE_URL = "https://aquapurite-erp-api.onrender.com"
EMAIL = "themanagingdirector@aquapurite.com"
PASSWORD = "Admin@123"


def login():
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.status_code}")
    return resp.json().get("access_token")


def get_accounts(headers):
    """Fetch all chart of accounts."""
    resp = requests.get(f"{BASE_URL}/api/v1/accounting/accounts", headers=headers)
    if resp.status_code != 200:
        return []
    data = resp.json()
    if isinstance(data, dict) and 'items' in data:
        return data['items']
    return data if isinstance(data, list) else []


def get_account_by_code(accounts, code):
    """Find account by code."""
    for acc in accounts:
        if acc.get('account_code') == code:
            return acc
    return None


def create_account(headers, data):
    """Create a new chart of account entry."""
    resp = requests.post(f"{BASE_URL}/api/v1/accounting/accounts", json=data, headers=headers)
    return resp


def update_account(headers, account_id, data):
    """Update an existing chart of account entry."""
    resp = requests.put(f"{BASE_URL}/api/v1/accounting/accounts/{account_id}", json=data, headers=headers)
    return resp


def main():
    print("=" * 60)
    print("CHART OF ACCOUNTS CLEANUP EXECUTION")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Login
    print("\nLogging in...")
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful!")

    # Fetch current accounts
    print("\n--- Fetching current Chart of Accounts ---")
    accounts = get_accounts(headers)
    print(f"Found {len(accounts)} accounts")

    # Create lookup
    acc_by_code = {acc['account_code']: acc for acc in accounts}

    changes_made = []
    errors = []

    # ========================================
    # STEP 1: Fix account 1200 (should be Inventory)
    # ========================================
    print("\n--- Step 1: Fix account 1200 ---")
    acc_1200 = acc_by_code.get('1200')
    if acc_1200:
        if 'GST' in acc_1200['account_name'].upper():
            print(f"  Updating 1200 from '{acc_1200['account_name']}' to 'Inventory'")
            resp = update_account(headers, acc_1200['id'], {
                "account_name": "Inventory",
                "account_sub_type": "INVENTORY"
            })
            if resp.status_code in [200, 201]:
                changes_made.append("1200: Renamed to 'Inventory'")
                print("  ✅ Updated successfully")
            else:
                errors.append(f"1200: Failed to update - {resp.text}")
                print(f"  ❌ Failed: {resp.text}")
        else:
            print(f"  ✅ Already correct: {acc_1200['account_name']}")

    # ========================================
    # STEP 2: Fix accounts 1510-1530 (should be Fixed Assets)
    # ========================================
    print("\n--- Step 2: Fix accounts 1510-1530 ---")
    fixed_asset_mapping = {
        '1510': 'Land & Building',
        '1520': 'Plant & Machinery',
        '1530': 'Furniture & Fixtures',
    }

    for code, expected_name in fixed_asset_mapping.items():
        acc = acc_by_code.get(code)
        if acc:
            if 'GST' in acc['account_name'].upper() or 'CGST' in acc['account_name'].upper():
                print(f"  Updating {code} from '{acc['account_name']}' to '{expected_name}'")
                resp = update_account(headers, acc['id'], {
                    "account_name": expected_name,
                    "account_sub_type": "FIXED_ASSET"
                })
                if resp.status_code in [200, 201]:
                    changes_made.append(f"{code}: Renamed to '{expected_name}'")
                    print("  ✅ Updated successfully")
                else:
                    errors.append(f"{code}: Failed to update - {resp.text}")
                    print(f"  ❌ Failed: {resp.text}")
            else:
                print(f"  ✅ Already correct: {acc['account_name']}")

    # ========================================
    # STEP 3: Create GST Input Credit accounts (1400-1430)
    # ========================================
    print("\n--- Step 3: Create GST Input Credit accounts ---")

    # Get Assets parent (1000)
    assets_parent = acc_by_code.get('1000')
    assets_parent_id = assets_parent['id'] if assets_parent else None

    gst_input_accounts = [
        {'code': '1400', 'name': 'GST Input Credit', 'is_group': True, 'parent_code': '1000'},
        {'code': '1410', 'name': 'CGST Input Credit', 'is_group': False, 'parent_code': '1400'},
        {'code': '1420', 'name': 'SGST Input Credit', 'is_group': False, 'parent_code': '1400'},
        {'code': '1430', 'name': 'IGST Input Credit', 'is_group': False, 'parent_code': '1400'},
    ]

    for acc_def in gst_input_accounts:
        existing = acc_by_code.get(acc_def['code'])
        if existing:
            print(f"  ✅ {acc_def['code']}: Already exists - {existing['account_name']}")
            continue

        # Get parent ID
        parent_id = None
        if acc_def['parent_code']:
            parent = acc_by_code.get(acc_def['parent_code'])
            if parent:
                parent_id = parent['id']

        print(f"  Creating {acc_def['code']}: {acc_def['name']}")
        resp = create_account(headers, {
            "account_code": acc_def['code'],
            "account_name": acc_def['name'],
            "account_type": "ASSET",
            "account_sub_type": "CURRENT_ASSET",
            "parent_id": parent_id,
            "is_active": True,
            "is_group": acc_def['is_group'],
            "allow_direct_posting": not acc_def['is_group']
        })

        if resp.status_code in [200, 201]:
            changes_made.append(f"{acc_def['code']}: Created '{acc_def['name']}'")
            print("  ✅ Created successfully")
            # Update lookup for next iterations
            new_acc = resp.json()
            acc_by_code[acc_def['code']] = new_acc
        else:
            errors.append(f"{acc_def['code']}: Failed to create - {resp.text}")
            print(f"  ❌ Failed: {resp.text}")

    # ========================================
    # STEP 4: Create GST Output Liability accounts (2210-2230)
    # ========================================
    print("\n--- Step 4: Create GST Output Liability accounts ---")

    # Get GST Liabilities parent (2200)
    gst_liab_parent = acc_by_code.get('2200')

    gst_output_accounts = [
        {'code': '2210', 'name': 'CGST Output Liability', 'parent_code': '2200'},
        {'code': '2220', 'name': 'SGST Output Liability', 'parent_code': '2200'},
        {'code': '2230', 'name': 'IGST Output Liability', 'parent_code': '2200'},
    ]

    for acc_def in gst_output_accounts:
        existing = acc_by_code.get(acc_def['code'])
        if existing:
            print(f"  ✅ {acc_def['code']}: Already exists - {existing['account_name']}")
            continue

        # Get parent ID
        parent_id = None
        if acc_def['parent_code']:
            parent = acc_by_code.get(acc_def['parent_code'])
            if parent:
                parent_id = parent['id']

        print(f"  Creating {acc_def['code']}: {acc_def['name']}")
        resp = create_account(headers, {
            "account_code": acc_def['code'],
            "account_name": acc_def['name'],
            "account_type": "LIABILITY",
            "account_sub_type": "TAX_PAYABLE",
            "parent_id": parent_id,
            "is_active": True,
            "is_group": False,
            "allow_direct_posting": True
        })

        if resp.status_code in [200, 201]:
            changes_made.append(f"{acc_def['code']}: Created '{acc_def['name']}'")
            print("  ✅ Created successfully")
        else:
            errors.append(f"{acc_def['code']}: Failed to create - {resp.text}")
            print(f"  ❌ Failed: {resp.text}")

    # ========================================
    # Summary
    # ========================================
    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)

    print(f"\n✅ Changes made: {len(changes_made)}")
    for change in changes_made:
        print(f"   - {change}")

    if errors:
        print(f"\n❌ Errors: {len(errors)}")
        for error in errors:
            print(f"   - {error}")
    else:
        print("\n✅ No errors!")

    print("\n" + "-" * 60)
    print("NOTE: If accounts at 2310, 2320 still have GST names,")
    print("they may need manual review/deletion in Supabase.")
    print("-" * 60)


if __name__ == "__main__":
    main()
