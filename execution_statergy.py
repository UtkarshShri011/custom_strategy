# pylint: skip-file
from __future__ import annotations

import time

from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
from nautilus_trader.adapters.binance.config import BinanceDataClientConfig
from nautilus_trader.adapters.binance.config import BinanceExecClientConfig
from nautilus_trader.adapters.binance.factories import BinanceLiveDataClientFactory
from nautilus_trader.adapters.binance.factories import BinanceLiveExecClientFactory
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveExecEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.identifiers import Venue

from copy_trading_statergy import CopyTradingConfig
from copy_trading_statergy import CopyTradingStrategy
from utils.fetch_trade_data import fetch_vid_cursor

# import threading

# *** THIS IS A TEST STRATEGY WITH NO ALPHA ADVANTAGE WHATSOEVER. ***
# *** IT IS NOT INTENDED TO BE USED TO TRADE LIVE WITH REAL MONEY. ***


# Configure the trading node
config_node = TradingNodeConfig(
    trader_id=TraderId('TESTER-001'),
    logging=LoggingConfig(log_level='INFO'),
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_lookback_mins=1440,
    ),
    # cache=CacheConfig(
    #     database=DatabaseConfig(),
    #     buffer_interval_ms=100,
    # ),
    # message_bus=MessageBusConfig(
    #     database=DatabaseConfig(),
    #     encoding="json",
    #     streams_prefix="quoters",
    #     use_instance_id=False,
    #     timestamps_as_iso8601=True,
    #     # types_filter=[QuoteTick],
    #     autotrim_mins=1,
    # ),
    heartbeat_interval=1.0,
    snapshot_orders=True,
    snapshot_positions=True,
    snapshot_positions_interval=5.0,
    data_clients={
        'BINANCE': BinanceDataClientConfig(
            account_type=BinanceAccountType.USDT_FUTURE,
            # 'BINANCE_API_KEY' env var
            api_key='f6120805ad848210623d784e22b412e9e6bd8cc89ffea7194d5cce69e81525a7',
            # 'BINANCE_API_SECRET' env var
            api_secret='5a708ef8b6fd809022e76f73dbf0306ea3be461603a36cdca7ba950eb338564b',
            testnet=True,
            base_url_http='https://testnet.binancefuture.com',
            base_url_ws='wss://fstream.binancefuture.com',
            us=False,  # If client is for Binance US
            instrument_provider=InstrumentProviderConfig(load_all=True),
        ),
    },
    exec_clients={
        'BINANCE': BinanceExecClientConfig(
            account_type=BinanceAccountType.USDT_FUTURE,
            # 'BINANCE_API_KEY' env var
            api_key='f6120805ad848210623d784e22b412e9e6bd8cc89ffea7194d5cce69e81525a7',
            # 'BINANCE_API_SECRET' env var
            api_secret='5a708ef8b6fd809022e76f73dbf0306ea3be461603a36cdca7ba950eb338564b',
            testnet=True,
            base_url_http='https://testnet.binancefuture.com',
            base_url_ws='wss://fstream.binancefuture.com',
            us=False,  # If client is for Binance US
            instrument_provider=InstrumentProviderConfig(load_all=True),
        ),
    },
    timeout_connection=30.0,
    timeout_reconciliation=10.0,
    timeout_portfolio=10.0,
    timeout_disconnection=10.0,
    timeout_post_stop=5.0,
)

# Instantiate the node with a configuration
node = TradingNode(config=config_node)
BINANCE = Venue('BINANCE')
# Configure your strategy
# strat_config = EMACrossConfig(
#     instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
#     external_order_claims=[InstrumentId.from_str("BTCUSDT-PERP.BINANCE")],
#     bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
#     fast_ema_period=10,
#     slow_ema_period=20,
#     trade_size=Decimal("0.010"),
#     order_id_tag="001",
# )
# # Instantiate your strategy
# strategy = EMACross(config=strat_config)

strat_config = CopyTradingConfig(
    instrument_id=InstrumentId.from_str('ETHUSDT-PERP.BINANCE'),
    vid=fetch_vid_cursor(),
)

strategy = CopyTradingStrategy(config=strat_config)

# Add your strategies and modules
node.trader.add_strategy(strategy)

# Register your client factories with the node (can take user-defined factories)
node.add_data_client_factory('BINANCE', BinanceLiveDataClientFactory)
node.add_exec_client_factory('BINANCE', BinanceLiveExecClientFactory)
node.build()


def statistics(node: TradingNode):
    account_report = node.trader.generate_positions_report()
    order_fill_report = node.trader.generate_order_fills_report()
    open_orders = node.trader.check_residuals()
    account_details = node.trader.generate_account_report(BINANCE)
    print(account_report)
    print(order_fill_report)
    print(open_orders)
    print(account_details)
    return


def run_statistics_periodically(node: TradingNode):
    i = 0
    while True:
        i = i + 1
        statistics(node)
        time.sleep(30)
        if i == 1:
            break


# Stop and dispose of the node with SIGINT/CTRL+C
if __name__ == '__main__':
    try:
        # thread_1 = threading.Thread(target=node.run)
        # thread_2 = threading.Thread(target=run_statistics_periodically, args=(node,))
        # thread_1.start()
        # thread_2.start()
        # thread_1.join()
        # thread_2.join()
        node.run()
        statistics(node)
    finally:
        node.dispose()
