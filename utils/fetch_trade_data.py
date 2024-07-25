from enum import Enum
from common.common import get_timestamp_ago
from utils.constants import (MAX_PARALLEL_POSITIONS,
                            POSITION_SIDE, TOKEN_SUPPORTED,
                            TRADE_INTERVAL, VID_CURSOR)

from utils.db_utils import (check_gmx_position,
                            check_inference_logs,
                            get_open_positions_count,
                            get_vid_cursor,
                            insert_trade_inference_logs,
                            update_vid_cursor)

from utils.feature_extractor_utils import (
    extract_feature_values, 
    get_online_trade_features, 
    get_trade_inference,
    is_supported_asset)



class Status(Enum):
    TRIGGERED = "Triggered"
    SKIPPED = "Skipped"


class SkipReason(Enum):
    TOKEN_NOT_SUPPORTED = "Token not supported"
    POSITION_SIDE_NOT_SUPPORTED = "Position side not supported"
    NOT_RECENT_TRADE = "Not recent trade"
    INFERENCE_ALREADY_PROCESSED = "Inference already processed"
    NO_CORRESPONDING_OPEN_TRADE = "No corresponding  open position for this trade"
    NEGATIVE_INFERENCE = "Negative Inference"
    MAX_PARALLEL_POSITIONS = (
        "No of parallel positions exceeds the max open positions limit"
    )

async def fetch_vid_cursor():
    last_vid_cursor = await get_vid_cursor()
    if last_vid_cursor is None:
        vid_cursor = VID_CURSOR
    else:
        vid_cursor = int(last_vid_cursor.vid)

    return vid_cursor


async def fetch_trade_details(vid_cursor: int):
    """
    Fetches the latest trades from the feature store.

    Returns:
        List[dict]: A list of dictionaries containing details of the latest trades.
                    Each dictionary represents a trade.
    """
    trades = []

    trade_features = get_online_trade_features(vid_cursor + 1, vid_cursor + 15)
    trades = extract_feature_values(trade_features)

    return trades


async def check_inference_output(self,trades):
    """
    Check inference output for a list of trades and trigger trade orders based on conditions.

    Parameters:
    - trades (list): List of trade dictionaries containing trade information.

    Returns:
    - list: List of inference logs for successful trades.
    """
    inference_logs = []

    if trades is None or len(trades) == 0:
        return []
    for trade in trades:
        self._log.info(f"Trade Vid:{trade["vid"]}")
        is_trade_not_recent = int(float(trade["block_timestamp"])) < get_timestamp_ago(
            TRADE_INTERVAL
        )
        if not is_supported_asset(TOKEN_SUPPORTED, trade["token"]):
            await update_vid_cursor(
                str(trade["vid"]),
                str(trade["block_timestamp"]),
                str(trade["token"]),
                str(trade["position_side"]),
                str(trade["link"]),
                Status.SKIPPED.value,
                SkipReason.TOKEN_NOT_SUPPORTED.value,
            )
            continue

        if not is_supported_asset(POSITION_SIDE, trade["position_side"]):
            await update_vid_cursor(
                str(trade["vid"]),
                str(trade["block_timestamp"]),
                str(trade["token"]),
                str(trade["position_side"]),
                str(trade["link"]),
                Status.SKIPPED.value,
                SkipReason.POSITION_SIDE_NOT_SUPPORTED.value,
            )
            continue

        if is_trade_not_recent and trade["status"].capitalize() == "Open":
            
            self._log.info(f'VID {trade["vid"]} timestamp difference is below interval threshold. Timestamp {trade["block_timestamp"]}')
            
            await update_vid_cursor(
                str(trade["vid"]),
                str(trade["block_timestamp"]),
                str(trade["token"]),
                str(trade["position_side"]),
                str(trade["link"]),
                Status.SKIPPED.value,
                SkipReason.NOT_RECENT_TRADE.value,
            )
            continue

        logs = await check_inference_logs(trade["id"])
        if logs is not None:
            await update_vid_cursor(
                str(trade["vid"]),
                str(trade["block_timestamp"]),
                str(trade["token"]),
                str(trade["position_side"]),
                str(trade["link"]),
                Status.SKIPPED.value,
                SkipReason.INFERENCE_ALREADY_PROCESSED.value,
            )
            continue

        gmx_position = await check_gmx_position(trade["link"], True)
        if gmx_position is None and trade["status"].capitalize() != "Open":
            await update_vid_cursor(
                str(trade["vid"]),
                str(trade["block_timestamp"]),
                str(trade["token"]),
                str(trade["position_side"]),
                str(trade["link"]),
                Status.SKIPPED.value,
                SkipReason.NO_CORRESPONDING_OPEN_TRADE.value,
            )
            continue

        open_position_count = int(await get_open_positions_count())
        if open_position_count >= MAX_PARALLEL_POSITIONS and trade["status"].capitalize() == "Open":
            inference_logs.append(0)
            await update_vid_cursor(
                str(trade["vid"]),
                str(trade["block_timestamp"]),
                str(trade["token"]),
                str(trade["position_side"]),
                str(trade["link"]),
                Status.SKIPPED.value,
                SkipReason.MAX_PARALLEL_POSITIONS.value,
            )
            continue
        if trade["status"].capitalize() == "Open":
            inference = get_trade_inference(
                trade["vid"],
                trade["account"],
                trade["id"],
                trade["link"],
                trade["block_timestamp"],
            )

            if inference[0] == 0:
                await update_vid_cursor(
                    str(trade["vid"]),
                    str(trade["block_timestamp"]),
                    str(trade["token"]),
                    str(trade["position_side"]),
                    str(trade["link"]),
                    Status.SKIPPED.value,
                    SkipReason.NEGATIVE_INFERENCE.value,
                )
                inference_logs.append(inference)
                continue

            await update_vid_cursor(
                str(trade["vid"]),
                str(trade["block_timestamp"]),
                str(trade["token"]),
                str(trade["position_side"]),
                str(trade["link"]),
                Status.TRIGGERED.value,
                None,
            )
            await insert_trade_inference_logs(
                str(inference), trade["id"], str(trade["vid"])
            )
        await update_vid_cursor(
            str(trade["vid"]),
            str(trade["block_timestamp"]),
            str(trade["token"]),
            str(trade["position_side"]),
            str(trade["link"]),
            Status.TRIGGERED.value,
            None,
        )
        if trade["status"].capitalize() in ("Open", "Close", "Liquidated"):
            trade["gmx_position"] = gmx_position

    return inference_logs
