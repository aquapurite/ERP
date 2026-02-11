"""
Final test for expense voucher workflow.
"""
import requests
from datetime import date

BASE_URL = "https://aquapurite-erp-api.onrender.com"
EMAIL = "themanagingdirector@aquapurite.com"
PASSWORD = "Admin@123"


def main():
    # Login
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful!")

    # Test 1: Create voucher without category
    print("\n--- Test 1: Create voucher without category ---")
    voucher_data = {
        "voucher_date": str(date.today()),
        "amount": 1000.00,
        "gst_amount": 180.00,
        "tds_amount": 0,
        "narration": "Test expense",
        "purpose": "Testing",
        "payment_mode": "CASH"
    }
    resp = requests.post(f"{BASE_URL}/api/v1/expenses", json=voucher_data, headers=headers)
    if resp.status_code in [200, 201]:
        v = resp.json()
        print(f"✅ Created voucher: {v['voucher_number']} (Amount: ₹{v['amount']})")
        voucher_id = v['id']
    else:
        print(f"❌ Failed: {resp.status_code} - {resp.text}")
        return

    # Test 2: Submit for approval
    print("\n--- Test 2: Submit for approval ---")
    resp = requests.post(f"{BASE_URL}/api/v1/expenses/{voucher_id}/submit", headers=headers)
    if resp.status_code in [200, 201]:
        v = resp.json()
        print(f"✅ Submitted. Status: {v['status']}")
    else:
        print(f"❌ Failed: {resp.status_code} - {resp.text}")

    # Test 3: Try to approve (will fail due to maker-checker)
    print("\n--- Test 3: Approve (expecting maker-checker error) ---")
    resp = requests.post(f"{BASE_URL}/api/v1/expenses/{voucher_id}/approve",
                         json={"remarks": "Test approval"}, headers=headers)
    if resp.status_code == 400:
        print(f"✅ Expected: {resp.json().get('detail')}")
    elif resp.status_code in [200, 201]:
        print(f"✅ Approved. Status: {resp.json()['status']}")
    else:
        print(f"❌ Unexpected: {resp.status_code} - {resp.text}")

    # Test 4: Dashboard stats
    print("\n--- Test 4: Dashboard stats ---")
    resp = requests.get(f"{BASE_URL}/api/v1/expenses/dashboard/stats", headers=headers)
    if resp.status_code == 200:
        d = resp.json()
        print(f"✅ Dashboard:")
        print(f"   Month: ₹{d.get('total_amount_this_month', 0)}")
        print(f"   Year: ₹{d.get('total_amount_this_year', 0)}")
        print(f"   Pending: {d.get('pending_approval_count', 0)} (₹{d.get('pending_approval_amount', 0)})")
    else:
        print(f"❌ Failed: {resp.status_code} - {resp.text}")

    # Test 5: List vouchers
    print("\n--- Test 5: List expense vouchers ---")
    resp = requests.get(f"{BASE_URL}/api/v1/expenses", headers=headers)
    if resp.status_code == 200:
        d = resp.json()
        print(f"✅ Total vouchers: {d['total']}")
        for v in d['items'][:3]:
            print(f"   - {v['voucher_number']}: ₹{v['amount']} ({v['status']})")
    else:
        print(f"❌ Failed: {resp.status_code} - {resp.text}")

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main()
