import asyncio
import sys
from pathlib import Path


# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from kuru_sdk.client_order_executor import ClientOrderExecutor


from web3 import Web3
from kuru_sdk.margin import MarginAccount
import os

from dotenv import load_dotenv

load_dotenv()

# Network and contract configuration
NETWORK_RPC = os.getenv("RPC_URL")
ADDRESSES = {
    "margin_account": "0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef",
    "orderbook": "0xd3af145f1aa1a471b5f0f62c52cf8fcdc9ab55d3",
    "chog": "0x7E9953A11E606187be268C3A6Ba5f36635149C81",
    "mon": "0x0000000000000000000000000000000000000000",
}
WS_URL = "https://ws.testnet.kuru.io"


async def main():
    web3 = Web3(Web3.HTTPProvider(NETWORK_RPC))

    client = ClientOrderExecutor(
        web3=web3, contract_address=ADDRESSES["orderbook"], private_key=os.getenv("PK")
    )

    orderbook = await client.get_l2_book()
    print(orderbook)


if __name__ == "__main__":
    asyncio.run(main())
