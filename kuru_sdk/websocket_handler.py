import socketio
import asyncio
import aiohttp
import logging
from typing import Optional, Callable, Union, Awaitable
from kuru_sdk.types import (
    OrderCreatedPayload,
    TradePayload,
    OrderCancelledPayload,
    MarketParams,
)
from kuru_sdk.client_order_executor import ClientOrderExecutor


class WebSocketHandler:

    def __init__(
        self,
        websocket_url: str,
        market_address: str,
        market_params: MarketParams,
        on_order_created: Optional[
            Callable[[OrderCreatedPayload], Awaitable[None]]
        ] = None,
        on_trade: Optional[Callable[[TradePayload], None]] = None,
        on_order_cancelled: Optional[
            Callable[[OrderCancelledPayload], Awaitable[None]]
        ] = None,
        reconnect_interval: int = 5,
        max_reconnect_attempts: int = 5,
        client_order_executor: Optional[ClientOrderExecutor] = None,
        logger: Union[logging.Logger, bool] = True,
    ):

        self.websocket_url = websocket_url
        self.market_address = market_address
        self._session = None
        self.client_order_executor = client_order_executor
        self.market_params = market_params

        # Set up logger
        if isinstance(logger, logging.Logger):
            self.logger = logger
        elif logger:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = None

        # Store callback functions
        self._on_order_created = on_order_created
        self._on_trade = on_trade
        self._on_order_cancelled = on_order_cancelled

        # Create Socket.IO client with specific configuration
        self.sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=max_reconnect_attempts,
            reconnection_delay=reconnect_interval,
            reconnection_delay_max=reconnect_interval * 2,
        )

        # Register event handlers
        @self.sio.event
        async def connect():
            self._log_info(f"Connected to WebSocket server at {websocket_url}")

        @self.sio.event
        async def disconnect():
            self._log_info("Disconnected from WebSocket server")

        @self.sio.event
        async def OrderCreated(payload):
            formatted_payload = self._format_order_created_payload(payload)
            self._log_info(f"OrderCreated Event Received: {formatted_payload}")
            try:
                if self._on_order_created:
                    await self._on_order_created(formatted_payload)
            except Exception as e:
                self._log_error(f"Error in on_order_created callback: {e}")

        @self.sio.event
        async def Trade(payload):
            formatted_payload = self._format_trade_payload(payload)
            self._log_info(f"Trade Event Received: {formatted_payload}")
            try:
                if self._on_trade:
                    await self._on_trade(formatted_payload)
            except Exception as e:
                self._log_error(f"Error in on_trade callback: {e}")

        @self.sio.event
        async def OrdersCanceled(payload):
            formatted_payload = self._format_order_cancelled_payload(payload)
            self._log_info(f"OrdersCanceled Event Received: {formatted_payload}")
            try:
                if self._on_order_cancelled:
                    await self._on_order_cancelled(formatted_payload)
            except Exception as e:
                self._log_error(f"Error in on_order_cancelled callback: {e}")

    def _log_info(self, message):
        """Log info message if logger is enabled"""
        if self.logger:
            self.logger.info(message)

    def _log_error(self, message):
        """Log error message if logger is enabled"""
        if self.logger:
            self.logger.error(message)

    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()

            self._log_info(self.websocket_url)
            await self.sio.connect(
                f"{self.websocket_url}?marketAddress={self.market_address}",
                transports=["websocket"],
            )
            self._log_info(f"Successfully connected to {self.websocket_url}")

            # Keep the connection alive in the background
            asyncio.create_task(self.sio.wait())
        except Exception as e:
            self._log_error(f"Failed to connect to WebSocket server: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        try:
            await self.sio.disconnect()
            if self._session:
                await self._session.close()
                self._session = None
            self._log_info("Disconnected from WebSocket server")
        except Exception as e:
            self._log_error(f"Error during disconnect: {e}")
            raise

    def is_connected(self) -> bool:
        """Check if the WebSocket is currently connected"""
        return self.sio.connected

    def _format_order_created_payload(self, payload) -> OrderCreatedPayload:
        return OrderCreatedPayload(
            order_id=payload["orderId"],
            cloid=(
                self.client_order_executor.get_cloid_by_order_id(payload["orderId"])
                if self.client_order_executor
                else None
            ),
            market_address=payload["marketAddress"],
            owner=payload["owner"],
            price=float(payload["price"])
            / float(str(self.market_params.price_precision)),
            size=float(payload["size"]) / float(str(self.market_params.size_precision)),
            is_buy=payload["isBuy"],
            block_number=payload["blockNumber"],
            tx_index=payload["txIndex"],
            log_index=payload["logIndex"],
            transaction_hash=payload["transactionHash"],
            trigger_time=payload["triggerTime"],
            remaining_size=float(payload["remainingSize"])
            / float(str(self.market_params.size_precision)),
            is_canceled=payload["isCanceled"],
        )

    def _format_trade_payload(self, payload) -> TradePayload:
        return TradePayload(
            order_id=payload["orderId"],
            cloid=(
                self.client_order_executor.get_cloid_by_order_id(payload["orderId"])
                if self.client_order_executor
                else None
            ),
            market_address=payload["marketAddress"],
            maker_address=payload["makerAddress"],
            is_buy=payload["isBuy"],
            price=float(payload["price"])
            / float(str(self.market_params.price_precision)),
            updated_size=float(payload["updatedSize"])
            / float(str(self.market_params.size_precision)),
            taker_address=payload["takerAddress"],
            filled_size=float(payload["filledSize"])
            / float(str(self.market_params.size_precision)),
            block_number=payload["blockNumber"],
            tx_index=payload["txIndex"],
            log_index=payload["logIndex"],
            transaction_hash=payload["transactionHash"],
            trigger_time=payload["triggerTime"],
        )

    def _format_order_cancelled_payload(self, payload) -> OrderCancelledPayload:
        cloids = None
        if self.client_order_executor:
            cloids = [
                self.client_order_executor.get_cloid_by_order_id(order_id)
                for order_id in payload["orderIds"]
            ]

        return OrderCancelledPayload(
            order_ids=payload["orderIds"],
            cloids=cloids,
            maker_address=payload["makerAddress"],
            canceled_orders_data=[
                self._format_order_created_payload(order)
                for order in payload["canceledOrdersData"]
            ],
        )
