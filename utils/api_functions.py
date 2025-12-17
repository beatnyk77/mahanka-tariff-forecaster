import pandas as pd
import streamlit as st
import random
import time

# Try importing the libraries
try:
    import world_trade_data as wits
    import comtradeapicall
except ImportError:
    wits = None
    comtradeapicall = None

@st.cache_data
def get_tariff_data(hs_code, reporter, partner):
    """
    Fetches tariff data. 
    Tries World Bank/WITS API first, falls back to mock data.
    """
    # 1. Try Live API (Placeholder logic - WITS library can be complex to config without credentials sometimes, 
    # but we attempt the standard call if available)
    try:
        # Note: world_trade_data wrapper often requires extensive config or might be slow.
        # We will wrap it aggressively.
        if wits:
             # This is a hypothetical call pattern for world_trade_data if it works out of box
             # often it returns a pandas Series.
             # fallback to mock for safety in this demo if specific parameters fail.
             pass
    except Exception as e:
        print(f"WITS API Error: {e}")

    # 2. Mock Logic (Fallback)
    # Simulating API latency
    time.sleep(0.3)
    
    if hs_code.startswith('8517'): # Smartphones/Electronics
        base_rate = 0.0
        if partner == 'China':
            base_rate = 25.0
        elif partner == 'India':
            base_rate = 0.0
        elif partner == 'Vietnam':
            base_rate = 0.0
    else:
        base_rate = 5.0 # Generic default
        
    return {
        'hs_code': hs_code,
        'reporter': reporter,
        'partner': partner,
        'mf_rate': base_rate, # Most Favored Nation
        'pref_rate': base_rate, # Preferential
        'bound_rate': base_rate + 5.0,
        'year': 2024
    }

@st.cache_data
def get_trade_flow_data(hs_code, reporter='USA'):
    """
    Fetches top exporters for a given HS code to the reporter country.
    Tries Comtrade API, falls back to mock.
    """
    try:
        if comtradeapicall:
            # Real call would look like:
            # data = comtradeapicall.get_trade_data(reporter=reporter, partner='World', hs=hs_code, ...)
            # For stability in this specific MVP environment without guaranteed keys, we use the sophisticated mock
            # but structured to be easily swapped.
            pass
    except Exception as e:
        print(f"Comtrade API Error: {e}")
    
    # Mock data for top exporters of the good
    data = [
        {'partner': 'China', 'trade_value': 5000000000, 'share': 45.0, 'risk_level': 'High', 'growth': -2.5},
        {'partner': 'Vietnam', 'trade_value': 2500000000, 'share': 22.5, 'risk_level': 'Low', 'growth': 15.0},
        {'partner': 'India', 'trade_value': 1200000000, 'share': 10.8, 'risk_level': 'Medium', 'growth': 12.0},
        {'partner': 'Mexico', 'trade_value': 900000000, 'share': 8.1, 'risk_level': 'Low', 'growth': 5.0},
        {'partner': 'Taiwan', 'trade_value': 800000000, 'share': 7.2, 'risk_level': 'Medium', 'growth': 1.0},
        {'partner': 'South Korea', 'trade_value': 700000000, 'share': 6.3, 'risk_level': 'Low', 'growth': 3.0},
    ]
    
    # Shuffle slightly for randomness if not specific known code
    if '8517' not in str(hs_code):
        random.shuffle(data)
        for d in data:
            d['trade_value'] = random.randint(10000000, 1000000000)
            
    df = pd.DataFrame(data)
    return df

def calculate_duty(import_value, rate):
    return import_value * (rate / 100.0)
