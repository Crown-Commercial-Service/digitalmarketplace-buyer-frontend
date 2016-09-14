import os

config = {
    'DM_FRONTEND_URL': os.getenv('DM_FRONTEND_URL', 'http://localhost:5002/marketplace'),
    'DM_BUYER_EMAIL': os.getenv('DM_BUYER_EMAIL', ''),
    'DM_BUYER_PASSWORD': os.getenv('DM_BUYER_PASSWORD', ''),
    'DM_SUPPLIER_EMAIL': os.getenv('DM_SUPPLIER_EMAIL', ''),
    'DM_SUPPLIER_PASSWORD': os.getenv('DM_SUPPLIER_PASSWORD', ''),
    'DM_DATA_API_URL': os.getenv('DM_DATA_API_URL', ''),
    'DM_DATA_API_AUTH_TOKEN': os.getenv('DM_DATA_API_AUTH_TOKEN', '')
}
