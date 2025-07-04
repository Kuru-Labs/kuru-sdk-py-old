import sys
from pathlib import Path
import random
import uuid

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from kuru_sdk.websocket_handler import WebSocketHandler
from kuru_sdk.types import OrderCancelledPayload, OrderCreatedPayload, OrderRequest, TradePayload
from kuru_sdk.client_order_executor import ClientOrderExecutor

from web3 import AsyncWeb3, AsyncHTTPProvider
import os
import asyncio
from dotenv import load_dotenv
import signal

load_dotenv()

# Network and contract configuration
NETWORK_RPC = os.getenv("RPC_URL")
PK = os.getenv("PK")

if not NETWORK_RPC or not PK:
    print("Error: RPC_URL and PK must be set in the .env file.")
    sys.exit(1)

print(f"NETWORK_RPC: {NETWORK_RPC}")

ADDRESSES = {
    'margin_account': '0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef', 
    'orderbook': '0x05e6f736b5dedd60693fa806ce353156a1b73cf3', 
}

# Market Making Configuration
MEAN_PRICE = 0.00015
STD_DEV = 0.00002
ORDER_SIZE = 10000
NUM_ORDERS_PER_SIDE = 3 # Number of buy/sell orders to place

def get_random_price(mean, std_dev):
    """Generates a random price based on a normal distribution."""
    price = random.normalvariate(mean, std_dev)
    # Ensure price is positive and round to a reasonable number of decimals
    return max(0.00000001, round(price, 8)) 

class MarketMakerBot:
    def __init__(self):
        self.client = None
        self.ws_client = None
        self.shutdown_event = None
        self.cloid_to_order = {} # Stores the original OrderRequest
        self.order_id_to_cloid = {} # Maps Kuru order ID back to client order ID
        self.cloid_status = {} # Tracks 'active', 'filled', 'cancelled', 'partially_filled'
        self.active_cloids = set() # Keep track of cloids we expect to be active

    def on_order_created(self, payload: OrderCreatedPayload):
        print(f"Order created callback: {payload}")
        # Map Kuru order ID to our cloid if we know the cloid
        if payload.cloid in self.cloid_to_order:
            self.order_id_to_cloid[payload.order_id] = payload.cloid
            # Update order details based on creation confirmation
            order = self.cloid_to_order[payload.cloid]
            order.size = payload.remaining_size # Initial size might be confirmed here
            order.is_cancelled = payload.is_canceled

            if payload.is_canceled:
                self.cloid_status[payload.cloid] = "cancelled"
                if payload.cloid in self.active_cloids: self.active_cloids.remove(payload.cloid)
                print(f"Order {payload.cloid} immediately cancelled on creation.")
            elif payload.remaining_size == 0:
                self.cloid_status[payload.cloid] = "filled"
                if payload.cloid in self.active_cloids: self.active_cloids.remove(payload.cloid)
                print(f"Order {payload.cloid} immediately filled on creation.")
            else:
                self.cloid_status[payload.cloid] = "active"
                self.active_cloids.add(payload.cloid)
                print(f"Order {payload.cloid} confirmed active.")
            
            print(f"Updated order details for {payload.cloid}: {order}")
        else:
             print(f"Received creation confirmation for unknown cloid: {payload.cloid}")


    def on_trade(self, payload: TradePayload):
        print(f"Trade callback: {payload}")
        order_id = payload.order_id
        if order_id in self.order_id_to_cloid:
            cloid = self.order_id_to_cloid[order_id]
            if cloid in self.cloid_to_order:
                # Update remaining size
                self.cloid_to_order[cloid].size = payload.updated_size
                if payload.updated_size == 0:
                    self.cloid_status[cloid] = "filled"
                    if cloid in self.active_cloids: self.active_cloids.remove(cloid)
                    print(f"Order {cloid} fully filled.")
                else:
                    self.cloid_status[cloid] = "partially_filled"
                    # Keep it in active_cloids as it's still partially active
                    print(f"Order {cloid} partially filled. Remaining size: {payload.updated_size}")
                
                print(f"Updated order details for {cloid} after trade: {self.cloid_to_order[cloid]}")
            else:
                 print(f"Received trade for cloid {cloid} not in local cache.")
        else:
            print(f"Received trade for unknown order_id: {order_id}")


    def on_order_cancelled(self, payload: OrderCancelledPayload):
        print(f"Order cancelled callback: {payload}")
        for order_id in payload.order_ids:
            if order_id in self.order_id_to_cloid:
                cloid = self.order_id_to_cloid[order_id]
                if cloid in self.cloid_to_order:
                    self.cloid_to_order[cloid].is_cancelled = True
                    self.cloid_status[cloid] = "cancelled"
                    if cloid in self.active_cloids: self.active_cloids.remove(cloid)
                    print(f"Order {cloid} confirmed cancelled.")
                    print(f"Updated order details for {cloid}: {self.cloid_to_order[cloid]}")
                else:
                    print(f"Received cancellation for cloid {cloid} not in local cache.")
            else:
                 print(f"Received cancellation for unknown order_id: {order_id}")

    async def initialize(self):
        self.shutdown_event = asyncio.Future()

        self.client = ClientOrderExecutor(
            web3=AsyncWeb3(AsyncHTTPProvider(NETWORK_RPC)),
            contract_address=ADDRESSES['orderbook'],
            private_key=PK,
        )

        # Ensure market params are fetched before initializing WebSocketHandler
        if not self.client.orderbook.market_params:
             await self.client.orderbook.fetch_market_params()
             if not self.client.orderbook.market_params:
                 print("Error: Failed to fetch market parameters.")
                 sys.exit(1)


        ws_url = f"wss://ws.testnet.kuru.io" 

        self.ws_client = WebSocketHandler(
            websocket_url=ws_url,
            market_address=ADDRESSES['orderbook'],
            market_params=self.client.orderbook.market_params,
            on_order_created=self.on_order_created,
            on_trade=self.on_trade,
            on_order_cancelled=self.on_order_cancelled,
        )

        print("Connecting to WebSocket...")
        await self.ws_client.connect()
        print("WebSocket connected.")

        # Add signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self.shutdown(s)))
        print("Signal handlers set.")

    async def shutdown(self, sig):
        print(f"Received exit signal {sig.name}... Shutting down.")
        
        # Cancel active orders before disconnecting
        await self.cancel_all_active_orders()

        print("Disconnecting WebSocket client...")
        if self.ws_client:
            try:
                await self.ws_client.disconnect()
                print("WebSocket client disconnected.")
            except Exception as e:
                print(f"Error during WebSocket disconnect: {e}")
        
        if not self.shutdown_event.done():
             self.shutdown_event.set_result(True)

        # Optional: Clean up signal handlers
        loop = asyncio.get_running_loop()
        for s in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.remove_signal_handler(s)
            except ValueError:
                pass # Handler might already be removed


    async def place_mm_orders(self):
        """Places a set of buy and sell limit orders around the mean price."""
        orders = []
        print(f"Placing {NUM_ORDERS_PER_SIDE} buy and {NUM_ORDERS_PER_SIDE} sell orders...")

        for i in range(NUM_ORDERS_PER_SIDE):
            # Buy order
            buy_price = get_random_price(MEAN_PRICE, STD_DEV)
            buy_cloid = f"mm_buy_{uuid.uuid4()}"
            buy_order = OrderRequest(
                market_address=ADDRESSES['orderbook'],
                order_type='limit',
                side='buy',
                price=buy_price,
                size=ORDER_SIZE,
                cloid=buy_cloid
            )
            orders.append(buy_order)
            self.cloid_to_order[buy_cloid] = buy_order # Store request before sending
            self.cloid_status[buy_cloid] = "pending_creation" # Initial status

            # Sell order
            sell_price = get_random_price(MEAN_PRICE, STD_DEV)
            # Ensure sell price is reasonably higher than buy or mean
            sell_price = max(sell_price, MEAN_PRICE + STD_DEV * 0.5) 
            sell_price = round(sell_price, 8)

            sell_cloid = f"mm_sell_{uuid.uuid4()}"
            sell_order = OrderRequest(
                market_address=ADDRESSES['orderbook'],
                order_type='limit',
                side='sell',
                price=sell_price,
                size=ORDER_SIZE,
                cloid=sell_cloid
            )
            orders.append(sell_order)
            self.cloid_to_order[sell_cloid] = sell_order # Store request
            self.cloid_status[sell_cloid] = "pending_creation" # Initial status
            
            print(f"Prepared Buy: cloid={buy_cloid}, price={buy_price}, size={ORDER_SIZE}")
            print(f"Prepared Sell: cloid={sell_cloid}, price={sell_price}, size={ORDER_SIZE}")


        if not orders:
            print("No orders generated to place.")
            return

        try:
            print(f"Sending batch of {len(orders)} orders...")
            tx_hash = await self.client.batch_orders(orders)
            print(f"Market making batch order transaction hash: {tx_hash}")
            print("Waiting for order confirmations via WebSocket...")
        except Exception as e:
            print(f"Error placing batch orders: {e}")
            # Mark orders as failed locally if submission fails
            for order in orders:
                 if order.cloid in self.cloid_status and self.cloid_status[order.cloid] == "pending_creation":
                     self.cloid_status[order.cloid] = "failed_submission"


    async def cancel_all_active_orders(self):
        """Cancels all orders currently believed to be active."""
        cloids_to_cancel = list(self.active_cloids) # Create a copy to iterate over
        
        if not cloids_to_cancel:
            print("No active orders to cancel.")
            return

        print(f"Attempting to cancel active orders: {cloids_to_cancel}")
        
        cancel_requests = [
             OrderRequest(
                 market_address=ADDRESSES['orderbook'],
                 order_type='cancel',
                 cancel_cloids=cloids_to_cancel # Send single batch cancel if possible
             )
        ]

        try:
             tx_hash = await self.client.batch_orders(cancel_requests)
             print(f"Cancellation batch order transaction hash: {tx_hash}")
             # Update local status optimistically, WS will confirm
             for cloid in cloids_to_cancel:
                 if cloid in self.cloid_status and self.cloid_status[cloid] != 'filled':
                     self.cloid_status[cloid] = "pending_cancellation"
                 if cloid in self.active_cloids:
                      self.active_cloids.remove(cloid) # Remove from active set

        except Exception as e:
             print(f"Error sending cancellation request: {e}")


    async def run(self):
        try:
            await self.initialize()
            
            
            while not self.shutdown_event.done():
                try:
                    if not self.shutdown_event.done():
                        print("Refreshing market maker orders...")
                        await self.place_mm_orders()
                        await asyncio.sleep(10)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Error during periodic order placement: {e}")

            print("Market Maker Bot started. Initial orders placed.")
            print("Listening for WebSocket events. Press Ctrl+C to exit gracefully.")
            
            # Keep running, listening to WS updates and potentially re-balancing orders periodically
            await self.shutdown_event # Wait until shutdown signal is received

        except asyncio.CancelledError:
            print("Main task cancelled.")
        except Exception as e:
             print(f"An unexpected error occurred in run loop: {e}")
        finally:
            print("Starting final cleanup...")
            # Ensure disconnect is called even if there's an error before shutdown_event is awaited
            if self.ws_client and self.ws_client.is_connected:
                 print("Ensuring WebSocket is disconnected...")
                 await self.ws_client.disconnect()

            if self.shutdown_event and not self.shutdown_event.done():
                 print("Forcing shutdown event completion.")
                 self.shutdown_event.set_result(True) # Ensure main loop exits if stuck

            print("Cleanup finished.")


async def main():
    print("Starting Market Maker Bot...")
    bot = MarketMakerBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # The shutdown logic should handle this via signal handlers
        print("KeyboardInterrupt caught in __main__. Shutdown initiated by signal handler.")
    except Exception as e:
         print(f"Critical error in main: {e}")
