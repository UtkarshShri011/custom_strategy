"""
Constants
"""
from __future__ import annotations

MAX_PARALLEL_POSITIONS = 10
POSITION_SIDE = 'LONG'
TOKEN_SUPPORTED = 'ETH'
TRADE_INTERVAL = 3600
VID_CURSOR = 1072110

TRADE_FEATURES_URL = (
    'https://feast-historical-server.chainlake.dev/get-offline-features'
)
MODEL_SERVER_URL = 'http://localhost:5000/predict'
# RAY_MODEL_SERVE_URL=http://192.168.29.132:3000/predict
FIX_LEVERAGE = 20
