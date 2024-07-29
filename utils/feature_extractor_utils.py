# pylint: disable=too-many-arguments
# pylint: disable = line-too-long
# pylint: skip-file
""" Extract the Features with the Help of VID"""
from __future__ import annotations

from datetime import datetime
from datetime import timezone

import requests

from common.common import calculate_leverage
from common.common import get_token_from_index
from utils.constants import FIX_LEVERAGE
from utils.constants import MODEL_SERVER_URL
from utils.constants import TRADE_FEATURES_URL


def extract_feature_values(data):
    """
    Extract feature values from JSON data and organize them into a dictionary.

    Parameters:
    - data (dict): JSON data containing feature names and values.

    Returns:
    - dict: A dictionary where feature names are keys and corresponding values are values.
    """
    feature_names = data['metadata']['feature_names']
    results = data['results']
    feature_values_arr = []
    for result_arr in results:
        feature_values = {}
        for result in result_arr:
            values = result['value']
            feature_names = result['name']
            if len(values) > 0:
                feature_name = feature_names[0]
                feature_value = values[0]
                feature_values[feature_name] = feature_value

        # emit_vid_timestamp_metrics(feature_values["block_timestamp"])
        feature_values['token'] = get_token_from_index(
            feature_values['index_token'],
        )
        feature_values['leverage'] = (
            FIX_LEVERAGE
            if FIX_LEVERAGE > 0
            else calculate_leverage(
                feature_values['size'],
                feature_values['collateral'],
            )
        )
        # print(f"feature_values: {feature_values}")
        feature_values_arr.append(feature_values)

    return feature_values_arr


def get_online_trade_features(start_id, end_id):
    """
    Retrieve online trade features for a given VID asynchronously.

    Parameters:
    - vid (int): VID (Trade ID) for which to retrieve features.

    Returns:
    - dict or None: Dictionary containing trade features, or None if trade is not found.
    """
    url = TRADE_FEATURES_URL
    payload = {
        'featureService': 'v2_trades_feature_service',
        'entities': {'start_vid': [start_id], 'end_vid': [end_id]},
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()  # Return the JSON response as a Python dictionary
    except Exception as e:
        reason = f'Failed to get offline trade features. reason: {e} from vid: {start_id} to vid: {end_id}'
        if str(e).startswith('Expecting value: line 1 column 1 (char 0)'):
            reason = (
                f'404 Data not found for the range from {start_id} to vid: {end_id}'
            )
        # self._log.error(reason)
        raise Exception(reason)


def get_trade_inference(self, vid, account, id, link, unix_block_timestamp):
    """
    Get trade inference.

    Parameters:
        id (str): Inference ID.

    Returns:
        dict: Trade inference details.
    """
    block_timestamp = datetime.fromtimestamp(
        unix_block_timestamp,
        tz=timezone.utc,
    ).strftime('%Y-%m-%dT%H:%M:%SZ')
    resp = requests.post(
        MODEL_SERVER_URL,
        json={
            'vid': vid,
            'platform': 'V2',
            'account': account,
            'id': id,
            'link': link,
            'event_timestamp': block_timestamp,
        },
    )
    if resp.status_code == requests.codes.ok:
        return resp.json()
    else:
        self._log.error(f'Failed to get inference for vid: {vid}')
        raise Exception(f'Failed to get inference for vid: {vid}')


def is_supported_asset(supported_assets, asset):
    """
    Check if a specific token or position side is supported.

    Parameters:
    - supported_assets (str): Comma-separated string of supported
    tokens and position sides.
    - asset (str): Token or position side to check for support.

    Returns:
    - bool: True if the asset is supported, False otherwise.
    """
    # Split the supported_assets string using comma as delimiter
    supported_list = supported_assets.split(',')

    # Check if the asset is in the list of supported assets
    return asset in supported_list
