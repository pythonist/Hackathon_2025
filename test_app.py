#!/usr/bin/env python3
"""
Test Transaction Generator for FraudGuard AI
Generates realistic mixed transactions (legitimate + FATF risk countries)
and distributes timestamps across 1–24 hours.
"""

import requests
import random
import time
from datetime import datetime, timedelta
import json

# ======================================
# CONFIGURATION
# ======================================
BASE_URL = "http://localhost:5000"
PREDICT_ENDPOINT = f"{BASE_URL}/predict"
TOTAL_TRANSACTIONS = 1000
DELAY_BETWEEN_REQUESTS = 0.5  # seconds

# ======================================
# COUNTRY & CUSTOMER CONFIG
# ======================================
LEGITIMATE_COUNTRIES = ["India", "UK", "USA", "Singapore", "UAE"]
FATF_HIGH_RISK_COUNTRIES = [
    "Iran", "North Korea", "Myanmar", "Pakistan", "Syria",
    "Yemen", "Iraq", "Sudan", "Cuba", "Ethiopia"
]

PHONE_PREFIXES = {
    "India": "+91-98",
    "UK": "+44-20",
    "USA": "+1-555",
    "Singapore": "+65-91",
    "UAE": "+971-50",
    "Iran": "+98-21",
    "Pakistan": "+92-300",
    "Myanmar": "+95-9",
    "Syria": "+963-9",
    "Sudan": "+249-91",
}

# ======================================
# SCENARIOS
# ======================================
TRANSACTION_SCENARIOS = {
    "normal_low": {
        "description": "Normal low-value transaction",
        "amount_range": (10, 200),
        "probability": 0.35,
        "fraud_likelihood": "low"
    },
    "normal_medium": {
        "description": "Normal medium-value transaction",
        "amount_range": (200, 1000),
        "probability": 0.25,
        "fraud_likelihood": "low"
    },
    "normal_high": {
        "description": "Normal high-value transaction",
        "amount_range": (1000, 5000),
        "probability": 0.10,
        "fraud_likelihood": "medium"
    },
    "suspicious_round": {
        "description": "Suspicious round-amount transaction",
        "amount_range": (500, 3000),
        "probability": 0.10,
        "fraud_likelihood": "medium",
        "round_amount": True
    },
    "fraud_high_velocity": {
        "description": "Fraud - High velocity pattern",
        "amount_range": (2000, 8000),
        "probability": 0.07,
        "fraud_likelihood": "high",
        "rapid_fire": True
    },
    "fraud_large_amount": {
        "description": "Fraud - Large high-risk transfer",
        "amount_range": (10000, 50000),
        "probability": 0.05,
        "fraud_likelihood": "high"
    },
    "fraud_fatf_country": {
        "description": "Fraud - FATF high-risk origin country",
        "amount_range": (1000, 15000),
        "probability": 0.08,
        "fraud_likelihood": "high",
        "fatf_origin": True
    }
}

# ======================================
# FUNCTIONS
# ======================================

def select_country(is_fatf=False):
    """Randomly select a customer country"""
    if is_fatf:
        return random.choice(FATF_HIGH_RISK_COUNTRIES)
    return random.choice(LEGITIMATE_COUNTRIES)


def generate_phone_number(country):
    """Generate a realistic phone number using prefix by country"""
    prefix = PHONE_PREFIXES.get(country, "+1-555")
    suffix = f"{random.randint(1000,9999):04d}-{random.randint(1000,9999):04d}"
    return f"{prefix}-{suffix}"


def generate_amount(scenario):
    """Generate transaction amount"""
    min_amt, max_amt = scenario["amount_range"]
    if scenario.get("round_amount"):
        base_amounts = [500, 1000, 1500, 2000, 2500, 3000]
        return float(random.choice(base_amounts))
    return round(random.uniform(min_amt, max_amt), 2)


def generate_timestamp():
    """Generate timestamps spread across the last 24 hours"""
    now = datetime.now()
    random_hour = random.randint(0, 23)
    random_minute = random.randint(0, 59)
    ts = now.replace(hour=random_hour, minute=random_minute, second=random.randint(0,59))
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def select_scenario():
    """Weighted random scenario"""
    rand = random.random()
    cumulative = 0
    for name, scenario in TRANSACTION_SCENARIOS.items():
        cumulative += scenario["probability"]
        if rand <= cumulative:
            return name, scenario
    return "normal_low", TRANSACTION_SCENARIOS["normal_low"]


def send_transaction(data):
    """Send transaction to Flask API"""
    try:
        response = requests.post(PREDICT_ENDPOINT, data=data, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def main():
    print("=" * 70)
    print(f"FraudGuard AI - Test Transaction Generator")
    print(f"Generating {TOTAL_TRANSACTIONS} transactions across 1–24 hours")
    print("=" * 70, "\n")

    stats = {"total": 0, "success": 0, "failed": 0, "fatf": 0, "legit": 0}

    for i in range(TOTAL_TRANSACTIONS):
        scenario_name, scenario = select_scenario()
        is_fatf = scenario.get("fatf_origin", False) or random.random() < 0.15  # 15% random FATF origin

        country = select_country(is_fatf)
        phone = generate_phone_number(country)
        amount = generate_amount(scenario)
        timestamp = generate_timestamp()

        payload = {
            "phone_number": phone,
            "transaction_amount": amount,
            "timestamp": timestamp,
            "country": country
        }

        success = send_transaction(payload)
        stats["total"] += 1
        stats["success" if success else "failed"] += 1
        stats["fatf" if is_fatf else "legit"] += 1

        print(f"[{i+1:03}] {timestamp} | {country:12} | ${amount:8.2f} | {scenario_name:20} | {'OK' if success else 'FAILED'}")

        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Summary
    print("\n" + "=" * 70)
    print("Generation Complete")
    print(f"Total Transactions: {stats['total']}")
    print(f"Successful:         {stats['success']}")
    print(f"Failed:             {stats['failed']}")
    print(f"Legitimate Country: {stats['legit']}")
    print(f"FATF Country:       {stats['fatf']}")
    print("=" * 70)

    # Save log
    filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Results saved to: {filename}")


if __name__ == "__main__":
    main()
