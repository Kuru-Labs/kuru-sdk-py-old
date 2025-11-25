from dataclasses import dataclass
from typing import Optional, Dict, Any

from web3 import Web3

from .client_order_executor import ClientOrderExecutor
from .margin import MarginAccount


@dataclass
class NetworkConfig:
    """Simple network configuration for Kuru SDK clients."""

    rpc_url: str
    websocket_url: Optional[str] = None
    chain_id: Optional[int] = None
    margin_contract_address: Optional[str] = None
    common_tokens: Optional[Dict[str, Dict[str, Any]]] = None


# Monad mainnet defaults
MONAD_MAINNET_CHAIN_ID = 143

MONAD_MAINNET = NetworkConfig(
    rpc_url="https://rpc.monad.xyz",
    websocket_url="wss://rpc.monad.xyz",
    chain_id=MONAD_MAINNET_CHAIN_ID,
    margin_contract_address="0x2A68ba1833cDf93fa9Da1EEbd7F46242aD8E90c5",
    common_tokens={
        "MON": {
            "address": "0x0000000000000000000000000000000000000000",
            "decimals": 18,
            "symbol": "MON"
        },
        "USDC": {
            "address": "0x754704Bc059F8C67012fEd69BC8A327a5aafb603",
            "decimals": 6,
            "symbol": "USDC"
        },
        "WBTC": {
            "address": "0x0555E30da8f98308EdB960aa94C0Db47230d2B9c",
            "decimals": 6,
            "symbol": "WBTC"
        },
        "WETH": {
            "address": "0xEE8c0E9f1BFFb4Eb878d8f15f368A02a35481242",
            "decimals": 18,
            "symbol": "WETH"
        },
        "WSOL": {
            "address": "0xea17E5a9efEBf1477dB45082d67010E2245217f1",
            "decimals": 9,
            "symbol": "WSOL"
        }
    }
)


def create_client_order_executor(
        orderbook_address: str,
        private_key: str,
        config: NetworkConfig = MONAD_MAINNET,
        kuru_api_url: Optional[str] = None,
        logger=True,
) -> ClientOrderExecutor:
    """Create a ``ClientOrderExecutor`` from a network config.

    By default, this uses ``MONAD_MAINNET``. You can provide a custom
    ``NetworkConfig`` to target other networks or RPC providers.
    """

    web3 = Web3(Web3.HTTPProvider(config.rpc_url))

    return ClientOrderExecutor(
        web3=web3,
        contract_address=orderbook_address,
        private_key=private_key,
        kuru_api_url=kuru_api_url,
        logger=logger,
    )


def create_margin_account(
    private_key: str,
    config: NetworkConfig = MONAD_MAINNET,
) -> MarginAccount:
    """Create a ``MarginAccount`` from a network config.

    Uses the ``rpc_url`` and ``margin_contract_address`` from ``config``.
    """

    if not config.margin_contract_address:
        raise ValueError("NetworkConfig.margin_contract_address must be set to create a MarginAccount")

    web3 = Web3(Web3.HTTPProvider(config.rpc_url))

    return MarginAccount(
        web3=web3,
        contract_address=config.margin_contract_address,
        private_key=private_key,
    )


__all__ = [
    "NetworkConfig",
    "MONAD_MAINNET_CHAIN_ID",
    "MONAD_MAINNET",
    "create_client_order_executor",
    "create_margin_account",
]
