from decimal import Decimal
import requests
import psycopg2
import pandas as pd
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.book import OrderBook
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import OrderSide, TimeInForce, TriggerType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.trading.strategy import Strategy
import datetime
from datetime import timezone

class CopyTradingConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    vid: int
    ml_model_url: str

class CopyTradingStrategy(Strategy):
    def __init__(self, config: CopyTradingConfig) -> None:
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.trade_size = Decimal("1.0") 
        self.ml_model_url = config.ml_model_url
        self.db_connection = None
        self.counter = config.vid

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(f"Could not find instrument for {self.instrument_id}")
            self.stop()
            return

        # Establish DB connection
        self.db_connection = psycopg2.connect(
            dbname="alfredfeatures",
            port=5433,
            user="viewer",
            password="viewer",
            host="localhost"
        )

        self.subscribe_trade_ticks(self.instrument_id)

    def on_trade_tick(self, tick: TradeTick) -> None:
        self.log.info(str(tick))
        self.counter += 1
        trade_data = self.fetch_trade_data(self.counter)
        if trade_data:
            trade_data_df = pd.Series(trade_data)
            self._log.info(f"vid : {trade_data_df[0]} trade_data : {trade_data}")
            trade_side = trade_data_df[1]
            if trade_side == 'LONG' and trade_data_df[2] == 'OPEN':

                prediction = self.get_ml_prediction(trade_data)
                self._log.warning(f"Ml prediction is {prediction['result']}")
                if prediction["result"] == 1:
                    self.log.info(f"vid : {trade_data_df[0]} prediction is 1, taking open trade.")
                    #self.take_trade(OrderSide.BUY, self.trade_size)
                else:
                    self._log.info(f"vid : {trade_data_df[0]} prediction is not 1, skipping trade.")
            if trade_side == 'LONG' and trade_data_df[2] == 'LONG':
                self._log.info(f"vid : {trade_data_df[0]} prediction is 1, taking sell trade.")
                #self.take_trade(OrderSide.SELL, self.trade_size)
        else:
            self._log.warning(f"No trade data found for vid: {self.counter}")

    def fetch_trade_data(self, trade_id: int):
        cursor = self.db_connection.cursor()
        query = """
        SELECT vid,position_side,status
        FROM gmx_v2_trades WHERE vid = %s
        """
        cursor.execute(query, (trade_id,))
        trade_data = cursor.fetchone()
        cursor.close()
        return trade_data

    def get_ml_prediction(self, trade_data):
        response = requests.post(self.ml_model_url, json={"features": trade_data})
        if response.status_code == 200:
            return response.json()
        else:
            self._log.error(f"Failed to get prediction from ML model: {response.text}")
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

    def get_trade_inference(self, vid, account, id, link, unix_block_timestamp):
        """
        Get trade inference.

        Parameters:
            id (str): Inference ID.

        Returns:
            dict: Trade inference details.
        """
        MODEL_SERVER_URL = "http://localhost:5000/predict"
        block_timestamp = datetime.fromtimestamp(
            unix_block_timestamp, tz=timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        resp = requests.post(
            MODEL_SERVER_URL,
            json={
                "vid": vid,
                "platform": "V2",
                "account": account,
                "id": id,
                "link": link,
                "event_timestamp": block_timestamp,
            },
        )
        if resp.status_code == requests.codes.ok:
            return resp.json()
        else:
            self._log.error(f"Failed to get inference for vid: {vid}")
            raise Exception(f"Failed to get inference for vid: {vid}")

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
