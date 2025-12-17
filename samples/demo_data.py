import pandas as pd

def get_demo_scenario():
    """
    Returns a demo setup for Smartphones (HS 851713)
    Importing from China to USA.
    """
    return {
        'product_name': 'Smartphones',
        'hs_code': '851713',
        'current_supplier': 'China',
        'market': 'USA',
        'annual_value': 10000000, # $10M
        'base_margin': 20.0, # 20% margin
    }
