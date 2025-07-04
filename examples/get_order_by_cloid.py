import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from kuru_sdk.client_order_executor import ClientOrderExecutor
from web3 import AsyncWeb3, AsyncHTTPProvider
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Network and contract configuration
NETWORK_RPC = os.getenv("RPC_URL")
ORDERBOOK_ADDRESS = '0xd3af145f1aa1a471b5f0f62c52cf8fcdc9ab55d3'

async def main():
    # Initialize the client
    client = ClientOrderExecutor(
        web3=AsyncWeb3(AsyncHTTPProvider(NETWORK_RPC)),
        contract_address=ORDERBOOK_ADDRESS,
        private_key=os.getenv("PK"),
        kuru_api_url=os.getenv("KURU_API_URL"),
    )

    # Example list of CLOIDs you want to query
    cloids_to_query = [
        "8bea322482b20a0d43a623376047bb8b6eb3381ee3e183c49702f6783bc12251_sell_8000000",
        "6756d9eafbd8f673490c0f5fa178c82ff75955886ad34541f493a2bb91f10ce4_sell_8000000"
    ]

    try:
        # Fetch orders by SDK CLOIDs
        orders = await client.get_user_orders_by_sdk_cloids(cloids_to_query)
        print("Orders retrieved:")
        print(orders)

    except Exception as e:
        print(f"Error fetching orders: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 