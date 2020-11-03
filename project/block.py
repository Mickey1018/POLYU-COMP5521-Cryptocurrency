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

    def __jsonencode__(self):
        return {'block': self.__dict__}


class AdvancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__jsonencode__'):
            return obj.__jsonencode__()
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


# test
# test_block = Block(100, '0', time.time(), {}, 4, 0)
# print(test_block.compute_hash())
# print(test_block.hash)
# print(test_block.compute_hash())
# print(test_block.__dict__)
# print(test_block.toJSON())
# print(type(test_block.toJSON()))
