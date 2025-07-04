import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from web3 import AsyncWeb3, AsyncHTTPProvider
from kuru_sdk.margin import MarginAccount
import os

from dotenv import load_dotenv

load_dotenv()

# Network and contract configuration
NETWORK_RPC = os.getenv("RPC_URL")
ADDRESSES = {
    'margin_account': '0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef',
    'chog': '0x7E9953A11E606187be268C3A6Ba5f36635149C81',
    'mon': '0x0000000000000000000000000000000000000000'
}
WS_URL = "https://ws.testnet.kuru.io"

async def main():
    if not NETWORK_RPC or not os.getenv('PK'):
        raise EnvironmentError("RPC_URL and PK must be set in your .env file")

    web3 = AsyncWeb3(AsyncHTTPProvider(NETWORK_RPC))

    margin_account = MarginAccount(
        web3=web3,
        contract_address=ADDRESSES['margin_account'],
        private_key=os.getenv('PK')
    )

    wallet_address = web3.eth.account.from_key(os.getenv('PK')).address

    try:
        print("Submitting deposit transaction...")
        tx_hash = await margin_account.deposit(
            token=ADDRESSES['chog'],
            amount=100000000000000000000000  # 100k CHOG as raw units
        )
        print(f"Deposit tx_hash: {tx_hash}")

        balance = await margin_account.get_balance(
            user_address=wallet_address,
            token=ADDRESSES['mon']
        )
        print(f"Margin account MON balance: {balance}")
    except Exception as exc:
        print(f"Deposit failed: {exc}")

if __name__ == "__main__":
    asyncio.run(main())
