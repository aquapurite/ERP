"""
Fix GST Chart of Accounts - Audit and verify account mappings.

Issues that were fixed in auto_journal_service.py:
1. INVENTORY: Changed from "1400" to "1200"
2. GST_OUTPUT: Changed from "2300" to "2200"
3. CGST_PAYABLE: Changed from "2310" to "2210"
4. SGST_PAYABLE: Changed from "2320" to "2220"
5. IGST_PAYABLE: Changed from "2330" to "2230"
6. CGST_RECEIVABLE: Changed from "1510" to "1410" (1510 was Land & Building!)
7. SGST_RECEIVABLE: Changed from "1520" to "1420" (1520 was Plant & Machinery!)
8. IGST_RECEIVABLE: Changed from "1530" to "1430" (1530 was Furniture & Fixtures!)

This script verifies the COA via API.
"""

import requests

BASE_URL = "https://aquapurite-erp-api.onrender.com"
EMAIL = "themanagingdirector@aquapurite.com"
PASSWORD = "Admin@123"


def main():
    print("=" * 60)
    print("GST CHART OF ACCOUNTS - VERIFICATION")
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

    # Fetch chart of accounts
    print("\n--- Fetching Chart of Accounts ---")
    resp = requests.get(f"{BASE_URL}/api/v1/accounting/accounts", headers=headers)

    if resp.status_code != 200:
        print(f"Failed to fetch COA: {resp.status_code} - {resp.text}")
        return

    accounts = resp.json()
    if isinstance(accounts, dict) and 'items' in accounts:
        accounts = accounts['items']

    # Create lookup by code
    account_by_code = {acc['account_code']: acc for acc in accounts}

    # Expected mappings after fix
    expected_mappings = {
        # GST Input (should be under Current Assets)
        "1400": {"name": "GST Input Credit", "type": "ASSET"},
        "1410": {"name": "CGST Input", "type": "ASSET"},
        "1420": {"name": "SGST Input", "type": "ASSET"},
        "1430": {"name": "IGST Input", "type": "ASSET"},
        # GST Output (should be under Liabilities)
        "2200": {"name": "GST Output", "type": "LIABILITY"},
        "2210": {"name": "CGST Output", "type": "LIABILITY"},
        "2220": {"name": "SGST Output", "type": "LIABILITY"},
        "2230": {"name": "IGST Output", "type": "LIABILITY"},
        # Fixed Assets (should NOT have GST entries)
        "1510": {"name": "Land & Building", "type": "ASSET"},
        "1520": {"name": "Plant & Machinery", "type": "ASSET"},
        "1530": {"name": "Furniture & Fixtures", "type": "ASSET"},
        # Inventory
        "1200": {"name": "Inventory", "type": "ASSET"},
    }

    print("\n--- Verifying Account Mappings ---")
    all_ok = True

    for code, expected in expected_mappings.items():
        if code in account_by_code:
            acc = account_by_code[code]
            name_match = any(word.lower() in acc['account_name'].lower()
                          for word in expected['name'].split())
            type_match = acc['account_type'] == expected['type']

            if name_match and type_match:
                print(f"  ✅ {code}: {acc['account_name']} ({acc['account_type']})")
            else:
                print(f"  ⚠️ {code}: {acc['account_name']} ({acc['account_type']})")
                print(f"      Expected: {expected['name']} ({expected['type']})")
                all_ok = False
        else:
            print(f"  ❌ {code}: NOT FOUND - Expected: {expected['name']}")
            all_ok = False

    # Check for duplicates/wrong entries
    print("\n--- Checking for GST Accounts at Wrong Codes ---")
    problematic_codes = ['1510', '1520', '1530', '2310', '2320', '2330']

    for code in problematic_codes:
        if code in account_by_code:
            acc = account_by_code[code]
            if 'GST' in acc['account_name'].upper() or 'CGST' in acc['account_name'].upper():
                print(f"  ⚠️ WARNING: {code} has GST in name: {acc['account_name']}")
                print(f"      This code should be for Fixed Assets, not GST!")
                all_ok = False

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if all_ok:
        print("""
✅ All account mappings are correct!

The auto_journal_service.py has been updated with correct codes:
- GST Input:  1410, 1420, 1430 (CGST, SGST, IGST under Current Assets)
- GST Output: 2210, 2220, 2230 (CGST, SGST, IGST under Liabilities)
- Inventory:  1200 (under Current Assets)

Fixed Asset codes (1510-1530) are correctly mapped to:
- 1510: Land & Building
- 1520: Plant & Machinery
- 1530: Furniture & Fixtures
""")
    else:
        print("""
⚠️ Some issues were found. Please review the warnings above.

If there are GST entries at wrong account codes, they may need
manual cleanup in the database.
""")


if __name__ == "__main__":
    main()
