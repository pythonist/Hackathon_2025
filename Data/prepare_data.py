# =============================================================
# Banking–Telecom Fraud Detection Dataset Generator
# Synthetic Dataset for Hackathon (10K Records)
# =============================================================

import pandas as pd
import numpy as np
import random

# -----------------------------------------
# Configuration
# -----------------------------------------
N_SAMPLES = 10000
FRAUD_RATE = 0.09  # 9% fraud cases
np.random.seed(42)
random.seed(42)

# -----------------------------------------
# Helper Functions
# -----------------------------------------
def generate_customer_id(n):
    """Generate unique customer IDs"""
    return [f"CUST{str(i).zfill(8)}" for i in range(1, n + 1)]

def generate_local_number_for_country(country, existing_locals):
    """
    Generate a plausible local phone number (string of digits) for a given country.
    existing_locals is a set to enforce uniqueness per country code+local combination.
    This is synthetic and not guaranteed to match exact national numbering plans, but realistic enough.
    """
    # lengths chosen for plausibility
    lengths = {
        "India": 10,
        "UAE": 9,
        "USA": 10,
        "Singapore": 8,
        "Pakistan": 10,
        "Iran": 10,
        "Myanmar": 9,
        "UK": 10,
        "Germany": 11
    }
    length = lengths.get(country, 9)
    # try until unique local number for this country
    while True:
        if country == "India":
            # start with 6-9 for Indian mobiles
            first = str(np.random.randint(6, 10))
            rest = ''.join(str(np.random.randint(0, 10)) for _ in range(length - 1))
            local = first + rest
        else:
            # other countries: random digits, avoid leading zero
            first = str(np.random.randint(2, 10))
            rest = ''.join(str(np.random.randint(0, 10)) for _ in range(length - 1))
            local = first + rest

        if local not in existing_locals:
            existing_locals.add(local)
            return local

# -----------------------------------------
# Core Dataset Generation
# -----------------------------------------
def generate_dataset():
    n = N_SAMPLES
    data = pd.DataFrame()

    # === Identifiers ===
    data['customer_id'] = generate_customer_id(n)
    # Note: phone fields will be generated after KYC country is known

    # === Fraud Label ===
    n_fraud = int(n * FRAUD_RATE)
    labels = np.array([1] * n_fraud + [0] * (n - n_fraud))
    np.random.shuffle(labels)
    data['Fraud_Label'] = labels

    # === Customer Vintage Bucket ===
    data['Customer_Vintage_Bucket'] = [
        np.random.choice(['New', 'Mid', 'Mature'],
                         p=[0.35, 0.40, 0.25] if f == 1 else [0.18, 0.28, 0.54])
        for f in labels
    ]

    # === Customer Risk Rating ===
    data['customer_risk_rating'] = np.random.choice([1, 2, 3], size=n, p=[0.60, 0.30, 0.10])

    # === Avg Monthly Transaction Value ===
    avg_txn_values = []
    for f in labels:
        if f == 1:
            if np.random.rand() < 0.4:
                value = np.random.uniform(5e6, 1e7)
            else:
                value = np.random.lognormal(13, 1.5)
        else:
            value = np.random.lognormal(12.2, 0.8)
        avg_txn_values.append(min(value, 1e7))
    data['Avg_Monthly_Txn_Value'] = avg_txn_values

    # === KYC Update Frequency ===
    kyc_freq = []
    for f in labels:
        if f == 1:
            freq = np.random.choice([0,1,2,3,4,5,6,7,8,9,10,15,20,25],
                                    p=[0.15,0.10,0.10,0.12,0.10,0.08,0.07,0.06,0.05,0.04,0.04,0.04,0.03,0.02])
        else:
            p = np.array([0.88,0.05,0.03,0.015,0.01,0.005,0.003,0.002,0.001,0.001,0.002])
            p /= p.sum()
            freq = np.random.choice([0,1,2,3,4,5,6,7,8,9,10], p=p)
        kyc_freq.append(freq)
    data['KYC_Update_Freq'] = kyc_freq

    # === PEP / High-Risk Flag ===
    data['PEP_HighRisk_Flag'] = [
        np.random.choice([0, 1], p=[0.70, 0.30]) if f == 1 else np.random.choice([0, 1], p=[0.97, 0.03])
        for f in labels
    ]

    # === Customer Segment ===
    data['Customer_Segment'] = np.random.choice(['Retail', 'Corporate'], size=n, p=[0.90, 0.10])

    # === Occupation Type ===
    data['Occupation_Type'] = np.random.choice(
        ['Salaried', 'Self-Employed', 'Student', 'Retired', 'Unemployed'],
        size=n, p=[0.50, 0.30, 0.10, 0.07, 0.03]
    )

    # === Txn Count (1 Hour Window) ===
    txn_counts = []
    for f in labels:
        if f == 1:
            probs = np.array([0.10] + [0.015]*10 + [0.025]*10 + [0.035]*20 + [0.020]*9)
            probs /= probs.sum()
            txn_counts.append(np.random.choice(range(0,50), p=probs))
        else:
            probs = np.array([0.50,0.20,0.12,0.08,0.05] + [0.01]*10 + [0.002]*15)
            probs /= probs.sum()
            txn_counts.append(np.random.choice(range(0,30), p=probs))
    data['Txn_Count_1H'] = txn_counts

    # === Txn Frequency vs Mean ===
    data['Txn_Frequency_Day_vs_Mean'] = [
        min(np.random.gamma(2,1.5),10) if f == 1 else min(np.random.gamma(1.2,0.5),10)
        for f in labels
    ]

    # === Round Amount Repetitiveness ===
    data['RoundAmt_Repetitiveness_Percent'] = [
        np.random.beta(3,2)*100 if f == 1 else np.random.beta(1.5,4)*100
        for f in labels
    ]

    # === Same Day Credit Reversal (7D) ===
    data['SameDay_CreditReversal_Count_7D'] = [
        np.random.choice(range(0,8),
                         p=[0.30,0.20,0.15,0.12,0.10,0.08,0.03,0.02]) if f == 1
        else np.random.choice(range(0,8),
                              p=[0.92,0.04,0.02,0.01,0.005,0.003,0.001,0.001])
        for f in labels
    ]

    # === Geography / FATF-based Risk ===
    countries = ['India','UAE','USA','Singapore','Pakistan','Iran','Myanmar','UK','Germany']
    cities = {
        'India':['Mumbai','Delhi','Bangalore','Chennai','Kolkata','Hyderabad'],
        'UAE':['Dubai','Abu Dhabi','Sharjah'],
        'USA':['New York','San Francisco','Chicago','Los Angeles'],
        'Singapore':['Singapore'],
        'Pakistan':['Karachi','Lahore','Islamabad'],
        'Iran':['Tehran','Mashhad','Isfahan'],
        'Myanmar':['Yangon','Mandalay','Naypyidaw'],
        'UK':['London','Manchester','Birmingham'],
        'Germany':['Berlin','Munich','Frankfurt']
    }
    fatf_high_risk = ['Iran','North Korea','Myanmar']
    fatf_watchlist = ['Pakistan','Syria','Yemen','Turkey']

    kyc_country, kyc_city, geo_level, restricted_flag = [], [], [], []
    for f in labels:
        if f == 1:
            country = np.random.choice(['India','Pakistan','Iran','Myanmar','UAE'],
                                       p=[0.45,0.20,0.15,0.10,0.10])
        else:
            country = np.random.choice(['India','UAE','USA','UK','Germany','Singapore'],
                                       p=[0.55,0.15,0.10,0.10,0.05,0.05])
        city = np.random.choice(cities[country])
        if country in fatf_high_risk:
            level = 'High-Risk'
        elif country in fatf_watchlist:
            level = 'Watchlist'
        else:
            # small random noise
            level = 'Watchlist' if np.random.rand() < 0.01 else 'Normal'
        restricted = 1 if level != 'Normal' else 0

        kyc_country.append(country)
        kyc_city.append(city)
        geo_level.append(level)
        restricted_flag.append(restricted)

    data['KYC_Country'] = kyc_country
    data['KYC_City'] = kyc_city
    data['Geo_Restriction_Level'] = geo_level
    data['Restricted_Geo_Location'] = restricted_flag

    # === Country Code and Local Phone Number (consistent with KYC_Country) ===
    country_phone_codes = {
        "India": "+91",
        "UAE": "+971",
        "USA": "+1",
        "Singapore": "+65",
        "Pakistan": "+92",
        "Iran": "+98",
        "Myanmar": "+95",
        "UK": "+44",
        "Germany": "+49"
    }

    # to ensure uniqueness of local numbers per country code
    existing_local_per_country = {c: set() for c in country_phone_codes.keys()}

    country_codes = []
    phone_local_numbers = []
    full_phone_numbers = []

    for c in data['KYC_Country']:
        cc = country_phone_codes.get(c, "+91")
        local = generate_local_number_for_country(c, existing_local_per_country.setdefault(c, set()))
        full = f"{cc}{local}"
        country_codes.append(cc)
        phone_local_numbers.append(local)
        full_phone_numbers.append(full)

    data['Country_Code'] = country_codes
    data['Phone_Number'] = phone_local_numbers  # local part (digits only)
    data['Full_Phone'] = full_phone_numbers     # concatenation of code + local

    # === Rounding Numeric Features ===
    data['Avg_Monthly_Txn_Value'] = [round(v, 2) for v in data['Avg_Monthly_Txn_Value']]
    data['Txn_Frequency_Day_vs_Mean'] = [round(v, 2) for v in data['Txn_Frequency_Day_vs_Mean']]
    data['RoundAmt_Repetitiveness_Percent'] = [round(v, 1) for v in data['RoundAmt_Repetitiveness_Percent']]
    data['Txn_Count_1H'] = [int(v) for v in data['Txn_Count_1H']]
    data['SameDay_CreditReversal_Count_7D'] = [int(v) for v in data['SameDay_CreditReversal_Count_7D']]
    data['KYC_Update_Freq'] = [int(v) for v in data['KYC_Update_Freq']]

    # === Final Column Order ===
    column_order = [
        'customer_id', 'Country_Code', 'Phone_Number', 'Full_Phone', 'Fraud_Label',
        'Customer_Vintage_Bucket', 'customer_risk_rating', 'Customer_Segment', 'Occupation_Type',
        'Avg_Monthly_Txn_Value', 'KYC_Update_Freq', 'PEP_HighRisk_Flag',
        'Txn_Count_1H', 'Txn_Frequency_Day_vs_Mean', 'RoundAmt_Repetitiveness_Percent',
        'SameDay_CreditReversal_Count_7D',
        'KYC_Country', 'KYC_City', 'Geo_Restriction_Level', 'Restricted_Geo_Location'
    ]

    return data[column_order]

# -----------------------------------------
# Generate Dataset
# -----------------------------------------
print("Generating synthetic banking-telecom fraud dataset...")
df = generate_dataset()
print("✓ Dataset generated successfully!")
df.to_csv(r"E:\VS code stuff\Dataset Generation\banking_cust_dataset.csv",index=False)
# Quick checks
# print("\nTotal Records:", len(df))
# print("Fraud Cases:", df['Fraud_Label'].sum(), f"({df['Fraud_Label'].mean()*100:.2f}%)")
# print("\nSample rows:")
# print(df.head().to_string(index=False))
