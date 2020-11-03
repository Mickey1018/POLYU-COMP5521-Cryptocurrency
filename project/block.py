from hashlib import sha256
import json


class Block:
    def __init__(self, index, previous_hash, timestamp, transactions, difficulty, nonce):
        """
        Constructs a new block
        :param index: <int>
        :param previous_hash: <str>
        :param transactions: <Transaction object>
        :param difficulty: <int>
        :param nonce: <int>
        """
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.difficulty = difficulty
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        ignore = ['hash']
        block_params = {x: self.__dict__[x] for x in self.__dict__ if x not in ignore}
        block_string = json.dumps(str(block_params), sort_keys=True)
        return sha256(block_string.encode()).hexdigest()
