"""
Check the expense_vouchers table structure via API.
"""
import requests

BASE_URL = "https://aquapurite-erp-api.onrender.com"
EMAIL = "themanagingdirector@aquapurite.com"
PASSWORD = "Admin@123"


def main():
    # Login
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Try fetching expense vouchers list (this might work even if create fails)
    print("\n--- Fetching expense vouchers list ---")
    resp = requests.get(f"{BASE_URL}/api/v1/expenses", headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total vouchers: {data.get('total', 0)}")
    else:
        print(f"Response: {resp.text[:500]}")

    # Try fetching expense categories
    print("\n--- Fetching expense categories ---")
    resp = requests.get(f"{BASE_URL}/api/v1/expenses/categories", headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Categories: {data}")
    else:
        print(f"Response: {resp.text[:500]}")

    # Test with more verbose error from create
    print("\n--- Testing voucher create (verbose) ---")
    from datetime import date

    voucher_data = {
        "voucher_date": str(date.today()),
        "amount": 1000,
        "payment_mode": "CASH"
    }

    resp = requests.post(f"{BASE_URL}/api/v1/expenses", json=voucher_data, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Headers: {dict(resp.headers)}")
    print(f"Response: {resp.text}")


if __name__ == "__main__":
    main()
