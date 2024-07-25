from  datetime import timedelta, datetime

def get_timestamp_ago(minutes):
    # Calculate the timedelta object for the specified minutes
    delta = timedelta(minutes=minutes)

    # Get the current datetime
    current_time = datetime.now()

    # Subtract the timedelta from the current datetime to get the past time
    past_time = current_time - delta

    # Convert the past_time datetime object to a timestamp (Unix epoch time)
    timestamp_ago = int(past_time.timestamp())

    return timestamp_ago

def get_token_from_index(index_token):
    """
    Get token from index token.

    Parameters:
    - index_token (str): Index token.
    """
    token_map = {
        "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": "ETH",
        "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f": "BTC",
        "0xf97f4df75117a78c1a5a0dbb814af92458539fb4": "LINK",
        "0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0": "UNI",
    }

    # Default token value if index_token is not found in the map
    default_token = "UNKNOWN"

    # Get the corresponding token from the map, or use default_token if not found
    return token_map.get(index_token, default_token)

def calculate_leverage(size, collateral):
    """
    Calculate leverage based on size and collateral values.

    Parameters:
    - size (float): Size value for the trade.
    - collateral (float): Collateral value for the trade.

    Returns:
    - str: Calculated leverage as a text (string) value.
    """
    # Convert collateral and size to numeric (float) values for division
    try:
        collateral_value = float(collateral)
        size_value = float(size)
    except ValueError:
        return "Invalid input"  # Handle invalid input (non-numeric values)

    # Calculate leverage based on collateral and size values
    if collateral_value == 0:
        leverage = "0"
    else:
        leverage = str(size_value / collateral_value)  # Calculate leverage ratio

    return float(leverage)
