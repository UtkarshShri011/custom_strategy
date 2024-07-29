# pylint: skip-file
"""Module for handling HTTP requests in the copy trading strategy."""
from __future__ import annotations

from decimal import Decimal

import requests
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.enums import TriggerType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy

from utils.fetch_trade_data import check_inference_output
from utils.fetch_trade_data import fetch_trade_details

# import psycopg2


class CopyTradingConfig(StrategyConfig):
    instrument_id: InstrumentId
    vid: int


class CopyTradingStrategy(Strategy):
    def __init__(self, config: CopyTradingConfig) -> None:
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.trade_size = Decimal('1.0')
        # self.db_connection = None
        self.counter = config.vid
        self.model_url = 'http://localhost:5000/predict'

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(
                f'Could not find instrument for {self.instrument_id}',
            )
            self.stop()
            return

        # Establish DB connection
        # self.db_connection = psycopg2.connect(
        #     dbname="alfredfeatures",
        #     port=5433,
        #     user="viewer",
        #     password="viewer",
        #     host="localhost",
        # )
        self.subscribe_trade_ticks(self.instrument_id)

    def on_trade_tick(self, tick: TradeTick) -> None:
        self.log.info(str(tick))
        self.counter += 2
        self.log.info(f'vid : {self.counter}')
        trade_data = fetch_trade_details(self.counter)
        if trade_data:
            for trades in trade_data:
                inference = check_inference_output(self, trades)
                # inference = self.get_ml_prediction(trades)
                if inference == 1:
                    self.log.warning(
                        f"""vid : {trades['vid']} prediction is 1,
                         taking open trade.""",
                    )
                    # self.take_trade(OrderSide.BUY, self.trade_size)
                else:
                    self._log.warning(
                        f"""vid : {trades['vid']} prediction is not 1,
                        skipping trade.""",
                    )

    # def fetch_trade_data(self, trade_id: int):
    #     cursor = self.db_connection.cursor()
    #     query = """
    #     SELECT vid,position_side,status
    #     FROM gmx_v2_trades WHERE vid = %s
    #     """
    #     cursor.execute(query, (trade_id,))
    #     trade_data = cursor.fetchone()
    #     cursor.close()
    #     return trade_data

    def get_ml_prediction(self, trade_data):
        response = requests.post(self.model_url, json=trade_data)
        if response.status_code == 200:
            return response.json()
        else:
            self._log.error(
                f'Failed to get prediction from ML model: {response.text}',
            )
            return 0

    def take_trade(self, side: OrderSide, size: Decimal):
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=side,
            quantity=self.instrument.make_qty(size),
            time_in_force=TimeInForce.GTC,
            emulation_trigger=TriggerType.NO_TRIGGER,
        )
        self.submit_order(order)

    def on_stop(self) -> None:
        if self.db_connection:
            self.db_connection.close()

        # Cleanup orders and positions
        self.cancel_all_orders(self.instrument_id)
        self.close_all_positions(self.instrument_id)

    def on_reset(self) -> None:
        self.counter = 0

    def on_dispose(self) -> None:
        if self.db_connection:
            self.db_connection.close()
