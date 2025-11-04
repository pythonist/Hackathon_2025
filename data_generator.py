# data_generator.py
import pandas as pd
import numpy as np

def generate_customer_id(n):
    """Generate unique customer IDs"""
    return [f"CUST{str(i).zfill(8)}" for i in range(1, n + 1)]


def generate_local_number_for_country(country, existing_locals):
    """
    Generate a plausible local phone number (string of digits) for a given country.
    existing_locals is a set to enforce uniqueness per country code+local combination.
    This is synthetic and not guaranteed to match exact national numbering plans, but realistic enough.
    """
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
    while True:
        if country == "India":
            first = str(np.random.randint(6, 10))
            rest = ''.join(str(np.random.randint(0, 10)) for _ in range(length - 1))
            local = first + rest
        else:
            first = str(np.random.randint(2, 10))
            rest = ''.join(str(np.random.randint(0, 10)) for _ in range(length - 1))
            local = first + rest

        if local not in existing_locals:
            existing_locals.add(local)
            return local


def generate_unlabeled_dataset():
    n = 1
    data = pd.DataFrame()
    data["customer_id"] = generate_customer_id(n)

    data["Customer_Vintage_Bucket"] = np.random.choice(["New", "Mid", "Mature"], size=n, p=[0.2, 0.4, 0.4])
    data["customer_risk_rating"] = np.random.choice([1, 2, 3], size=n, p=[0.6, 0.3, 0.1])
    data["Avg_Monthly_Txn_Value"] = np.random.lognormal(12.3, 0.9, size=n)
    data["KYC_Update_Freq"] = np.random.choice(range(0, 10), size=n, p=[0.4,0.2,0.1,0.1,0.05,0.05,0.03,0.03,0.02,0.02])
    data["PEP_HighRisk_Flag"] = np.random.choice([0, 1], size=n, p=[0.95, 0.05])
    data["Customer_Segment"] = np.random.choice(["Retail", "Corporate"], size=n, p=[0.9, 0.1])
    data["Occupation_Type"] = np.random.choice(["Salaried", "Self-Employed", "Student", "Retired", "Unemployed"], size=n, p=[0.5,0.3,0.1,0.07,0.03])
    data["Txn_Count_1H"] = np.random.poisson(2, size=n)
    data["Txn_Frequency_Day_vs_Mean"] = np.random.gamma(1.5, 1.0, size=n)
    data["RoundAmt_Repetitiveness_Percent"] = np.random.beta(2,3,size=n)*100
    data["SameDay_CreditReversal_Count_7D"] = np.random.poisson(0.5, size=n)

    countries = ["India","UAE","USA","Singapore","Pakistan","Iran","Myanmar","UK","Germany"]
    cities = {
        "India":["Mumbai","Delhi","Bangalore"], "UAE":["Dubai","Abu Dhabi"], "USA":["New York","San Francisco"],
        "Singapore":["Singapore"], "Pakistan":["Karachi","Lahore"], "Iran":["Tehran","Isfahan"],
        "Myanmar":["Yangon","Mandalay"], "UK":["London","Manchester"], "Germany":["Berlin","Munich"]
    }
    fatf_high_risk = ["Iran","Myanmar"]
    fatf_watchlist = ["Pakistan"]

    kyc_country, kyc_city, geo_level, restricted_flag = [], [], [], []
    for _ in range(n):
        country = np.random.choice(countries)
        city = np.random.choice(cities[country])
        if country in fatf_high_risk:
            level = "High-Risk"
        elif country in fatf_watchlist:
            level = "Watchlist"
        else:
            level = "Normal"
        restricted = 1 if level != "Normal" else 0
        kyc_country.append(country)
        kyc_city.append(city)
        geo_level.append(level)
        restricted_flag.append(restricted)

    data["KYC_Country"] = kyc_country
    data["KYC_City"] = kyc_city
    data["Geo_Restriction_Level"] = geo_level
    data["Restricted_Geo_Location"] = restricted_flag

    country_phone_codes = {"India":"+91","UAE":"+971","USA":"+1","Singapore":"+65","Pakistan":"+92","Iran":"+98","Myanmar":"+95","UK":"+44","Germany":"+49"}
    existing_local_per_country = {c:set() for c in country_phone_codes.keys()}
    country_codes, phone_local_numbers, full_phone_numbers = [], [], []

    for c in data["KYC_Country"]:
        cc = country_phone_codes[c]
        local = generate_local_number_for_country(c, existing_local_per_country[c])
        full = f"{cc}{local}"
        country_codes.append(cc)
        phone_local_numbers.append(local)
        full_phone_numbers.append(full)

    data["Country_Code"] = country_codes
    data["Phone_Number"] = phone_local_numbers
    data["Full_Phone"] = full_phone_numbers
    data.columns = data.columns.str.lower()

    return data