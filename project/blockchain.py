from pprint import pprint
import copy
import random
from hashlib import sha256
import json
import time
from datetime import datetime, timedelta
from block import Block
from urllib.parse import urlparse
import requests
from ecpy.curves import Curve, Point
from ecpy.keys import ECPublicKey, ECPrivateKey
from ecpy.ecdsa import ECDSA
import redis  # type redis-server in terminal!

# create redis connection
redis_host = "localhost"
redis_port = 6379
redis_password = ""
r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)


def get_find_block_time():
    current_time = time.time()
    return current_time


def get_private_key():
    cv = Curve.get_curve('secp256k1')
    random_32_bytes = sha256(str(random.randint(1, 1000000)).encode('utf-8')).hexdigest()
    private_key = ECPrivateKey(int(random_32_bytes, 16), cv)
    return private_key


class Transaction:
    """
    Each transaction should be able to redeem an unspent output from a previous transaction.
    a coinbase transaction contains no input and an output with fixed amount of coins (i.e., 50 bitcoins).
    Each block contains one coinbase transaction to mint coins.
    """
    def __init__(self, txin, txout):
        """
        :param txin: <TxIn> object
        :param txout: <TxOut> object
        """
        self.tx_Ins = []
        self.tx_Outs = []
        self.tx_Ins.append(txin)
        self.tx_Outs.append(txout)
        self.id = self.get_transaction_id()
        # hash value of transaction contents, signatures of the txIds are not included in the transaction hash

    def get_transaction_id(self):
        """
        :return: Hash value of contents of TxIn and TxOut except signature
        """
        txin = self.tx_Ins[-1]
        txout = self.tx_Outs[-1]
        if txin:
            tx_in_str = txin.get_tx_in_content()
        else:
            tx_in_str = ''
        tx_out_str = txout.get_tx_out_content()
        str = tx_in_str + tx_out_str
        return sha256(str.encode('utf-8')).hexdigest()

    def generate_signature(self, private_key):
        """
        :return: {Message}SK, where Message = contents of TxIn and TxOut and Transaction ID
        """
        txin = self.tx_Ins[-1]
        txout = self.tx_Outs[-1]
        tx_in_str = txin.get_tx_in_content()
        tx_out_str = txout.get_tx_out_content()
        tran_id = self.get_transaction_id()
        message = tx_in_str + tx_out_str + tran_id

        signer = ECDSA()
        sig = signer.sign(message.encode('utf-8'), private_key)
        txin.signature = sig
        return sig
    

class TxIn:
    """
    the input consists where the coins are coming from (i.e., previous
    transaction ID and index), a signature, and a public key.
    """
    def __init__(self, prev_block, private_key):
        self.tx_out_index = self.get_prev_index(prev_block)
        self.tx_out_id = self.get_prev_transaction_id(prev_block)
        self.public_key = self.get_public_key(private_key)  # public key is generated from private key
        self.private_key = private_key
        self.address = self.get_address(self.public_key)

    @staticmethod
    def get_prev_index(prev_block):
        if isinstance(prev_block, Block):
            return prev_block.index
        elif isinstance(prev_block, dict):
            return prev_block['index']

    @staticmethod
    def get_prev_transaction_id(prev_block):
        if isinstance(prev_block, Block):
            return prev_block.transactions.id
        elif isinstance(prev_block, dict):
            return prev_block['transactions']['id']

    @staticmethod
    def get_public_key(private_key):
        public_key = private_key.get_public_key()
        return public_key

    @staticmethod
    def get_address(public_key):
        return sha256(str(public_key).encode('utf-8')).hexdigest()

    def get_tx_in_content(self):
        params = {
            'tx_out_id': self.tx_out_id,
            'tx_out_index': self.tx_out_index,
            'public_key': str(self.public_key)
        }
        string = json.dumps(params, sort_keys=True)  # convert to json object
        return string


class TxOut:
    def __init__(self, address, amount):
        self.address = address  # hash value of a public key (ECDSA)
        self.amount = amount  # amount of coins

    def get_tx_out_content(self):
        ignore = []
        params = {x: self.__dict__[x] for x in self.__dict__ if x not in ignore}
        string = json.dumps(params, sort_keys=True)
        return string


def P2PKH(private_key, tran, txin, txout):
    """
    :param tran: <Transaction> object
    :param txin: <TxIn> object
    :param txout: <TxOut> object
    :return: <Bool> True or False
    """
    stack = []

    # get signature and add it to stack
    signature = tran.generate_signature(private_key)
    stack.append(signature)  # stack[0]

    # get public key and add it to stack
    public_key = txin.public_key
    stack.append(public_key)  # stack[1]

    # copy the public key and add the copy to stack
    public_key_copy = copy.deepcopy(str(public_key))
    stack.append(public_key_copy)  # stack[2]

    # apply hash function to copy of public key
    hash_public_key_copy = sha256(public_key_copy.encode('utf-8')).hexdigest()
    stack[2] = hash_public_key_copy  # stack[2]

    # get address of recipient and add it to stack
    hash_public_key = txout.address
    stack.append(hash_public_key)  # stack[3]

    print('\n################# stack 1 #####################')
    pprint(stack)

    # check if address matches the hash value of public key
    if stack[2] == stack[3]:
        stack.pop(3)
        stack.pop(2)
        print('\naddress match')
    else:
        print('\naddress does not match')
        return False

    print('\n################# stack 2 #####################')
    pprint(stack)

    # get whole transaction messages except the signature
    tx_in_str = txin.get_tx_in_content()
    tx_out_str = txout.get_tx_out_content()
    tran_id = tran.get_transaction_id()
    message = tx_in_str + tx_out_str + tran_id

    # Instantiate a signer
    signer = ECDSA()

    # check the integrity of message, i.e. M = S{PU} = {{M}PK}PU = M
    valid = signer.verify(str(message).encode('utf-8'), stack[0], stack[1])
    if valid:
        stack.pop(1)
        stack.pop(0)
        print('\nsignature is valid')
    else:
        print('\nsignature is not valid')
        return False

    print('\n################# stack 3 #####################')
    pprint(stack)

    # if the stack is empty, then the transaction is said to be verified
    if not stack:
        print('\nTransaction verified')
        return True
    else:
        print('\nTransaction not verified')
        return False


class Blockchain:

    def __init__(self):
        self.unconfirmed_transactions = []
        self.wallets = {}
        self.private_key = []
        self.chain = []
        self.difficulty_adjustment_interval = 3
        self.block_generate_interval = timedelta(seconds=60)
        self.nodes = set()
        self.create_genesis_block()

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        :return: dictionary of genesis block
        """

        address = sha256(str(get_private_key().get_public_key()).encode('utf-8')).hexdigest()

        coinbase = Transaction(txin=None, txout=TxOut(address, 50))

        genesis_block = Block(index=0,
                              previous_hash="0",
                              timestamp=get_find_block_time(),
                              transactions=coinbase,
                              difficulty=4,
                              nonce=0)
        self.chain.append(genesis_block)
        self.wallets[address] = 50
        r.set(address, 50)
        return True

    def get_latest_block(self):
        return self.chain[-1]

    def find_block(self, previous_block):
        """
        :return: next_block
        """
        if isinstance(previous_block, Block):
            next_index = previous_block.index + 1
            previous_hash = previous_block.hash
            next_timestamp = get_find_block_time()
            next_transaction = self.unconfirmed_transactions[-1]
            next_difficulty = self.get_difficulty()
            next_nonce = 0

            test_block = Block(next_index, previous_hash, next_timestamp, next_transaction, next_difficulty, next_nonce)

            proof = self.get_proof(test_block, next_difficulty)

            next_block = Block(next_index, previous_hash, next_timestamp, next_transaction, next_difficulty, proof)

            return next_block

        elif isinstance(previous_block, dict):
            next_index = previous_block['index'] + 1
            previous_hash = previous_block['hash']
            next_timestamp = get_find_block_time()
            next_transaction = self.unconfirmed_transactions[-1]
            next_difficulty = self.get_difficulty()
            next_nonce = 0

            test_block = Block(next_index, previous_hash, next_timestamp, next_transaction, next_difficulty, next_nonce)

            proof = self.get_proof(test_block, next_difficulty)

            next_block = Block(next_index, previous_hash, next_timestamp, next_transaction, next_difficulty, proof)

            return next_block

    def get_proof(self, block, difficulty):
        """
        :param block:
        :param difficulty:
        :return:
        """
        block_hash = block.compute_hash()

        while not self.hash_match_difficulty(block_hash, difficulty):
            block.nonce += 1
            block_hash = block.compute_hash()

        proof = block.nonce

        return proof

    @staticmethod
    def is_valid_new_block(new_block, previous_block):
        """
        Check if a new block is valid or not
        :param new_block: <block>
        :param previous_block: <block>
        :return: <bool>
        """
        if isinstance(previous_block, Block):
            if previous_block.index + 1 != new_block.index:
                return False
            elif previous_block.hash != new_block.previous_hash:
                return False
            elif Block.compute_hash(new_block) != new_block.hash:
                return False
            else:
                return True

        elif isinstance(previous_block, dict):
            if previous_block['index'] + 1 != new_block.index:
                return False
            elif previous_block['hash'] != new_block.previous_hash:
                return False
            elif Block.compute_hash(new_block) != new_block.hash:
                return False
            else:
                return True

    @staticmethod
    def hash_match_difficulty(hash, difficulty):
        """
        Check if hash match difficulty or not
        :param hash: <str>
        :param difficulty: <int>
        :return: <bool>
        """
        if hash[:difficulty] != '0'*difficulty:
            return False
        else:
            return True

    def get_difficulty(self):
        """

        :return: block difficulty
        """
        last_block = self.get_latest_block()
        if isinstance(last_block, Block):
            if last_block.index % self.difficulty_adjustment_interval == 0 \
               and last_block.index != 0:
                return self.get_adjusted_difficulty(last_block, self.chain)
            else:
                return last_block.difficulty

        elif isinstance(last_block, dict):
            if last_block['index'] % self.difficulty_adjustment_interval == 0 \
               and last_block['index'] != 0:
                return self.get_adjusted_difficulty(last_block, self.chain)
            else:
                return last_block['difficulty']

    def get_adjusted_difficulty(self, last_block, blockchain):
        """

        :param last_block:
        :param blockchain:
        :return: block difficulty
        """
        prev_adjustment_block = blockchain[len(blockchain) - self.difficulty_adjustment_interval]
        time_expected = self.block_generate_interval * self.difficulty_adjustment_interval
        if isinstance(last_block, Block):
            time_taken = last_block.timestamp - prev_adjustment_block.timestamp
            if time_taken < time_expected.total_seconds() / 2:
                return prev_adjustment_block.difficulty + 1
            elif time_taken > time_expected.total_seconds() * 2:
                return prev_adjustment_block.difficulty - 1
            else:
                return prev_adjustment_block.difficulty

        elif isinstance(last_block, dict):
            time_taken = last_block['timestamp'] - prev_adjustment_block.timestamp
            if time_taken < time_expected.total_seconds()/2:
                return prev_adjustment_block.difficulty + 1
            elif time_taken > time_expected.total_seconds()*2:
                return prev_adjustment_block.difficulty - 1
            else:
                return prev_adjustment_block.difficulty

    def add_new_transaction(self, transaction):
        """
        append a transaction to unconfirmed_transaction list
        :param transaction: <Transaction object>
        :return:
        """
        self.unconfirmed_transactions.append(transaction)
        return True

    def mine_block(self):
        if not self.unconfirmed_transactions:
            return None
        else:
            previous_block = self.get_latest_block()
            new_block = self.find_block(previous_block)
            if self.is_valid_new_block(new_block, previous_block):
                self.chain.append(new_block)
                self.unconfirmed_transactions = []
                return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None
        new_node = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain/')

            if response.status_code == 200:
                length = response.json()['Length of Blockchain']
                chain = response.json()['Blockchain']

                # Check if the length is longer and the chain is valid
                if length > max_length:
                    max_length = length
                    new_chain = chain
                    new_node = node

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain and new_node:
            self.chain = new_chain
            account_list = requests.get(f'http://{new_node}/accounts/')
            for key in r.scan_iter("prefix:*"):
                r.delete(key)
            for account in account_list.json():
                self.wallets[account['user']] = account['amount of bitcoin']
                r.set(self.wallets[account['user']], account['amount of bitcoin'])
            return True

        return False


# Instantiate the Blockchain
blockchain = Blockchain()


