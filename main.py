import datetime
import hashlib
import json
import random
import string

from PyQt5.QtWidgets import QScrollArea
from flask import Flask
from PyQt5 import QtWidgets


class Block:
    def __init__(self, index: int, timestamp: datetime, transactions: list, previous_hash: str) -> None:
        """
        Parameters:
        index (int): The index of the block in the chain
        timestamp (datetime): The timestamp of when the block was created
        transactions (list): A list of transaction dictionaries
        previous_hash (str): The hash of the previous block in the chain
        """
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Method to calculate the SHA-256 hash of the block data

        Returns:
        str: The calculated hash value
        """
        data = str(self.index) + str(self.timestamp) + str(self.transactions) + str(self.previous_hash) + str(
            self.nonce)
        sha = hashlib.sha256()
        sha.update(data.encode('utf-8'))
        return sha.hexdigest()


class Blockchain:
    def __init__(self):
        """
        Initializes the chain with the genesis block
        """

        # List of blocks in the chain, initialized with the genesis block
        self.chain = [self.create_genesis_block()]
        # List of pending transactions to be added to the next mined block in the chain
        self.pending_transactions = []

    def create_genesis_block(self) -> Block:
        """
        Method to create the first block in the chain (the genesis block)

        Returns:
        Block: The genesis block object
        """
        return Block(index=0, timestamp=datetime.datetime.now(), transactions=[], previous_hash="0")

    def add_block(self, block: Block) -> None:
        """
        Method to add a new block to the chain

        Parameters:
        block (Block): The block object to add to the chain
        """
        self.chain.append(block)

    def mine_block(self, miner_address: str) -> bool:
        """
        Method to mine a new block by adding pending transactions to a new block and adding it to the chain

        Parameters:
        miner_address (str): The address of the miner who mined the block
        """

        # Check if there are any pending transactions to be added to the block
        if len(self.pending_transactions) == 0:
            return False
        # Create a new block with the pending transactions and add it to the chain
        block = Block(index=len(self.chain), timestamp=datetime.datetime.now(),
                      transactions=self.pending_transactions, previous_hash=self.chain[-1].hash)
        # Find a nonce value that makes the block hash satisfy a certain condition
        block.nonce = self.proof_of_work(block.hash)
        # Add the block to the chain
        self.add_block(block)
        # Reward the miner by adding a transaction to the pending transactions list
        reward_transaction = {
            'sender': "Blockchain",
            'recipient': miner_address,
            'amount': 1,
            'id': self.generate_transaction_id()
        }
        self.pending_transactions = [reward_transaction]
        return True

    def generate_transaction_id(self) -> str:
        """
        Method to generate a random transaction ID

        Returns:
        str: The generated transaction ID
        """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    def proof_of_work(self, block_hash: str) -> int:
        """
        Method to find a nonce value that makes the block hash satisfy a certain condition (in this case, the first 4 digits must be 0)

        Parameters:
        block_hash (str): The hash of the block to mine

        Returns:
        int: The nonce value that satisfies the condition
        """
        nonce = 0
        while self.valid_proof(block_hash, nonce) is False:
            nonce += 1
        return nonce

    def valid_proof(self, block_hash: str, nonce: int) -> bool:
        """
        Method to check if the given nonce value makes the block hash satisfy a certain condition

        Parameters:
        block_hash (str): The hash of the block to check
        nonce (int): The nonce value to check

        Returns:
        bool: True if the nonce value satisfies the condition, False otherwise
        """

        # Calculate the hash of the block with the given nonce value
        guess = f'{block_hash}{nonce}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        # Check if the first 4 digits of the hash are 0
        return guess_hash[:4] == "0000"

    def add_transaction(self, sender: str, recipient: str, amount: float) -> None:
        """
        Method to add a new transaction to the list of pending transactions

        Parameters:
        sender (str): The address of the sender of the transaction
        recipient (str): The address of the recipient of the transaction
        amount (float): The amount to be transferred in the transaction
        """
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'id': self.generate_transaction_id()
        }
        self.pending_transactions.append(transaction)

    def get_balance(self, address: str) -> float:
        """
        Method to calculate the balance of the given address by iterating through all transactions in the blockchain

        Parameters:
        address (str): The address to get the balance for

        Returns:
        float: The balance of the address
        """
        balance = 0
        for block in self.chain:
            for transaction in block.transactions:
                if transaction['sender'] == address:
                    balance -= transaction['amount']
                elif transaction['recipient'] == address:
                    balance += transaction['amount']
        return balance

    def get_transaction_by_id(self, transaction_id: str) -> dict:
        """
        Method to search for a transaction in the blockchain by its ID

        Parameters:
        transaction_id (str): The ID of the transaction to search for

        Returns:
        dict: The transaction with the given ID, or None if no transaction is found
        """
        for block in self.chain:
            for transaction in block.transactions:
                if transaction['id'] == transaction_id:
                    return transaction
        return None

    def is_chain_valid(self) -> bool:
        """
        Method to check if the blockchain is valid by verifying the hashes and previous hashes of each block

        Returns:
        bool: True if the blockchain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True


app = Flask(__name__)
blockchain = Blockchain()


class BlockchainGUI(QtWidgets.QMainWindow):
    def __init__(self):
        """
        Constructor method for BlockchainGUI class which responsible for setting up the GUI window
        """
        super().__init__()

        # Set up the GUI window
        self.setWindowTitle("Blockchain GUI")
        # self.setFixedSize(800, 600)

        # Set up the main widget and layout
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Add a button to toggle full screen
        self.toggle_full_screen_button = QtWidgets.QPushButton("Toggle Full Screen")
        self.toggle_full_screen_button.clicked.connect(self.toggle_full_screen)
        self.layout.addWidget(self.toggle_full_screen_button)

        # Add a label for the current state of the blockchain
        self.chain_text_edit = QtWidgets.QTextEdit()
        self.chain_text_edit.setReadOnly(True)

        # Create a scroll area for the chain label
        self.scroll_area = QScrollArea(self.central_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = QtWidgets.QWidget()
        self.scroll_area.setWidget(self.scroll_area_widget_contents)

        # Create a new layout for the scroll area widget contents
        self.scroll_area_layout = QtWidgets.QVBoxLayout(self.scroll_area_widget_contents)
        self.scroll_area_layout.addWidget(self.chain_text_edit)

        # Add the scroll area to the main layout
        self.layout.addWidget(self.scroll_area)

        # Add a button to add a transaction to the blockchain
        self.add_transaction_button = QtWidgets.QPushButton("Add Transaction")
        self.add_transaction_button.clicked.connect(self.add_transaction)
        self.layout.addWidget(self.add_transaction_button)

        # Add a button to mine a new block in the blockchain
        self.mine_block_button = QtWidgets.QPushButton("Mine Block")
        self.mine_block_button.clicked.connect(self.mine_block)
        self.layout.addWidget(self.mine_block_button)

        # Add a label for the address input field
        # Add a label for the balance
        self.balance_label = QtWidgets.QLabel("Balance:")
        self.layout.addWidget(self.balance_label)

        # Add an input field for the address to check the balance
        self.balance_address_input = QtWidgets.QLineEdit()

        # Add a button to show the balance for the given address
        self.show_balance_button = QtWidgets.QPushButton("Show Balance")
        self.show_balance_button.clicked.connect(self.show_balance)
        self.layout.addWidget(self.show_balance_button)

        # Add an input field for the miner's address
        self.address_label = QtWidgets.QLabel("Address:")
        self.layout.addWidget(self.address_label)
        self.address_input = QtWidgets.QLineEdit()
        self.layout.addWidget(self.balance_address_input)

        # Add a label for the transaction input fields
        self.transaction_label = QtWidgets.QLabel("Add Transaction:")
        self.layout.addWidget(self.transaction_label)

        # Add input fields for the sender, recipient, and amount of the transaction
        self.sender_input = QtWidgets.QLineEdit()
        self.sender_input.setPlaceholderText("Sender Address")
        self.layout.addWidget(self.sender_input)
        self.recipient_input = QtWidgets.QLineEdit()
        self.recipient_input.setPlaceholderText("Recipient Address")
        self.layout.addWidget(self.recipient_input)
        self.amount_input = QtWidgets.QLineEdit()
        self.amount_input.setPlaceholderText("Amount")
        self.layout.addWidget(self.amount_input)

        # Add a button to search for a transaction by its ID
        self.search_transaction_button = QtWidgets.QPushButton("Search Transaction")
        self.search_transaction_button.clicked.connect(self.search_transaction)
        self.layout.addWidget(self.search_transaction_button)

        # Add a label for the transaction ID input field
        self.transaction_id_label = QtWidgets.QLabel("Transaction ID:")
        self.layout.addWidget(self.transaction_id_label)

        # Add an input field for the transaction ID
        self.transaction_id_input = QtWidgets.QLineEdit()
        self.layout.addWidget(self.transaction_id_input)

        # Add Copy Blockchain Content button
        self.copy_blockchain_button = QtWidgets.QPushButton("Copy Blockchain Content")
        self.copy_blockchain_button.clicked.connect(self.copy_blockchain)
        self.layout.addWidget(self.copy_blockchain_button)

        # Update the chain label with the current state of the blockchain
        self.update_chain_label()

    def toggle_full_screen(self) -> None:
        """
        Method to toggle the full-screen mode of the window
        """
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def update_chain_label(self) -> None:
        """
        Method to update the chain label with the current state of the blockchain
        """
        chain_text = "Blockchain:\n"

        # Loop through each block in the blockchain and add its information to the chain label
        for block in blockchain.chain:
            block_text = f"Index: {block.index}\nTimestamp: {block.timestamp}\nTransactions: {json.dumps(block.transactions)}\nPrevious Hash: {block.previous_hash}\nHash: {block.hash}\n\n"
            chain_text += block_text

        # Update the chain label
        self.chain_text_edit.setText(chain_text)

    def add_transaction(self) -> None:
        """
        Method to add a new transaction to the blockchain and update the GUI
        """

        # Get the sender, recipient, and amount from the input fields
        sender = self.sender_input.text()
        recipient = self.recipient_input.text()
        amount = float(self.amount_input.text())

        # Add the transaction to the blockchain
        blockchain.add_transaction(sender, recipient, amount)

        # Clear the input fields
        self.sender_input.setText("")
        self.recipient_input.setText("")
        self.amount_input.setText("")
        self.update_chain_label()

    def mine_block(self) -> None:
        """
        Method to mine a new block in the blockchain and update the GUI
        """

        # Get the miner's address from the input field
        miner_address = self.address_input.text()

        # Mine the block
        mined = blockchain.mine_block(miner_address)

        # If the block was mined, clear the input field and update the chain label
        if mined:
            self.address_input.setText("")
            self.update_chain_label()
            QtWidgets.QMessageBox.information(self, "Block Mined", "Block mined successfully!")
        else:  # If the block was not mined, display a warning message
            QtWidgets.QMessageBox.warning(self, "No Transactions", "There are no transactions to mine!")

    def search_transaction(self) -> None:
        """
        Method to search for a transaction in the blockchain by its ID and display the result in a message box
        """

        # Get the transaction ID from the input field
        transaction_id = self.transaction_id_input.text()

        # Search for the transaction in the blockchain
        transaction = blockchain.get_transaction_by_id(transaction_id)

        # If the transaction was found, display its information in a message box
        if transaction is not None:
            message = f"Transaction ID: {transaction['id']}\nSender: {transaction['sender']}\nRecipient: {transaction['recipient']}\nAmount: {transaction['amount']}"
            QtWidgets.QMessageBox.information(self, "Transaction Found", message)
        else:  # If the transaction was not found, display a warning message
            QtWidgets.QMessageBox.warning(self, "Transaction Not Found", "No transaction was found with that ID!")

    def show_balance(self) -> None:
        """
        Method to show the balance for a given address in a message box
        """

        # Get the address from the input field
        address = self.balance_address_input.text()

        # Get the balance for the given address
        balance = blockchain.get_balance(address)

        # Display the balance in a message box
        message = f"Address: {address}\nBalance: {balance}"
        QtWidgets.QMessageBox.information(self, "Balance", message)

    def copy_blockchain(self) -> None:
        """
            Method to copy the entire blockchain content to the clipboard
            """

        # Copy the blockchain content to the clipboard
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.chain_text_edit.toPlainText())

        # Display a message box to inform the user that the blockchain content has been copied
        QtWidgets.QMessageBox.information(self, "Blockchain Copied",
                                          "The entire blockchain content has been copied to the clipboard!")


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = BlockchainGUI()
    window.show()
    app.exec_()
