from web3 import Web3
from typing import Optional
import json
import os


# Load ERC20 ABI
with open(os.path.join(os.path.dirname(__file__), "abi/ierc20.json"), "r") as f:
    erc20_abi = json.load(f)


class InsufficientBalanceError(Exception):
    pass


class MarginAccount:
    def __init__(
        self, web3: Web3, contract_address: str, private_key: Optional[str] = None
    ):
        """
        Initialize the MarginAccount SDK

        Args:
            web3: Web3 instance
            contract_address: Address of the deployed MarginAccount contract
            private_key: Private key for signing transactions (optional)
        """
        self.web3 = web3
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.private_key = private_key

        if self.private_key:
            self.wallet_address = self.web3.eth.account.from_key(
                self.private_key
            ).address

        # Load ABI from JSON file
        with open(
            os.path.join(os.path.dirname(__file__), "abi/marginaccount.json"), "r"
        ) as f:
            contract_abi = json.load(f)

        self.contract = self.web3.eth.contract(
            address=self.contract_address, abi=contract_abi
        )

        # Native token address constant
        self.NATIVE = "0x0000000000000000000000000000000000000000"

    async def deposit(
        self,
        token: str,
        amount: int,
    ) -> str:
        """
        Deposit tokens into the margin account

        Args:
            user: Address of the user to credit
            token: Token address (use NATIVE for ETH)
            amount: Amount to deposit (in wei)
            from_address: Address sending the transaction

        Returns:
            transaction_hash: Hash of the submitted transaction
        """
        token = Web3.to_checksum_address(token)

        # Check if token is not native and needs approval
        if token != self.NATIVE:

            token_contract = self.web3.eth.contract(address=token, abi=erc20_abi)
            balance = token_contract.functions.balanceOf(self.contract_address).call()
            if balance > amount:
                raise InsufficientBalanceError(
                    f"Withdrawal failed: requested {amount}, but only {balance} available."
                )

            # Check allowance
            allowance = token_contract.functions.allowance(
                self.wallet_address, self.contract_address
            ).call()
            if allowance < amount:
                print(
                    f"Insufficient allowance. Current: {allowance}, Required: {amount}"
                )
                print("Approving tokens for deposit...")
                allowance_tx = token_contract.functions.approve(
                    self.contract_address, amount
                ).build_transaction(
                    {
                        "from": self.wallet_address,
                        "nonce": self.web3.eth.get_transaction_count(
                            self.wallet_address
                        ),
                    }
                )
                signed_tx = self.web3.eth.account.sign_transaction(
                    allowance_tx, self.private_key
                )
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                print(f"Approval transaction hash: {receipt.transactionHash.hex()}")

        balance = token_contract.functions.balanceOf(self.contract_address).call()
        if balance > amount:
            raise InsufficientBalanceError(
                f"Withdrawal failed: requested {amount}, but only {balance} available."
            )
        # Build transaction
        transaction = self.contract.functions.deposit(
            self.wallet_address, token, amount
        )

        # Handle ETH deposits
        value = amount if token == self.NATIVE else 0

        # Get gas estimate and nonce
        gas_estimate = transaction.estimate_gas(
            {"from": self.wallet_address, "value": value}
        )
        nonce = self.web3.eth.get_transaction_count(self.wallet_address)

        # Build transaction dict
        transaction_dict = {
            "from": self.wallet_address,
            "nonce": nonce,
            "gas": gas_estimate,
            "gasPrice": self.web3.eth.gas_price,
            "value": value,
        }

        if self.private_key:
            # Sign and send transaction
            raw_transaction = transaction.build_transaction(transaction_dict)
            signed_txn = self.web3.eth.account.sign_transaction(
                raw_transaction, self.private_key
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"Deposit transaction submitted: {tx_hash.hex()}")
        else:
            raise Exception(
                "Private key is required to deposit tokens into the margin account"
            )

        return tx_hash.hex()

    async def withdraw(
        self,
        token: str,
        amount: int,
    ) -> str:
        """
        Withdraw tokens from the margin account

        Args:
            amount: Amount to withdraw (in wei)
            token: Token address (use NATIVE for ETH)
            from_address: Address sending the transaction

        Returns:
            transaction_hash: Hash of the submitted transaction
        """

        token = Web3.to_checksum_address(token)

        # Check if token is not native and needs approval
        if token != self.NATIVE:

            token_contract = self.web3.eth.contract(address=token, abi=erc20_abi)
            balance = token_contract.functions.balanceOf(self.contract_address).call()
            if balance > amount:
                raise InsufficientBalanceError(
                    f"Withdrawal failed: requested {amount}, but only {balance} available."
                )

        else:
            balance = token_contract.functions.balanceOf(self.contract_address).call()
            if balance > amount:
                raise InsufficientBalanceError(
                    f"Withdrawal failed: requested {amount}, but only {balance} available."
                )

        # Build transaction
        transaction = self.contract.functions.withdraw(amount, token)

        # Get gas estimate and nonce
        gas_estimate = transaction.estimate_gas({"from": self.wallet_address})
        nonce = self.web3.eth.get_transaction_count(self.wallet_address, "pending")

        # Build transaction dict
        transaction_dict = {
            "from": self.wallet_address,
            "nonce": nonce,
            "gas": gas_estimate,
            "gasPrice": self.web3.eth.gas_price,
        }

        if self.private_key:
            # Sign and send transaction
            raw_transaction = transaction.build_transaction(transaction_dict)
            signed_txn = self.web3.eth.account.sign_transaction(
                raw_transaction, self.private_key
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        else:
            raise Exception(
                "Private key is required to withdraw tokens from the margin account"
            )

        return tx_hash.hex()

    async def get_balance(self, user_address: str, token: str) -> int:
        return self.contract.functions.getBalance(user_address, token).call()


__all__ = ["MarginAccount"]
