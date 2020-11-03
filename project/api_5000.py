from uuid import uuid4
from block import *
from flask import Flask, request, jsonify
import requests
import json
import sqlite3
from block import *
from blockchain import *

# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')


def valid_amount(amount, address):
    try:
        if amount < 0 or amount > blockchain.wallets[address]:
            return False
        else:
            return True
    except Exception as e:
        print(repr(e))


# get the blockchain
@app.route('/chain/', methods=['GET'])
def chain():

    # create sqlite3 connection with blockchain.db
    conn_blockchain = sqlite3.connect("blockchain.db")

    # create a cursor object
    c_blockchain = conn_blockchain.cursor()

    # drop existing table called "blockchain" if any
    c_blockchain.execute("DROP TABLE IF EXISTS blockchain")

    # create a table called "blockchain"
    c_blockchain.execute("""
                        CREATE TABLE blockchain(
                        block_index INTEGER PRIMARY KEY,
                        previous_hash TEXT,
                        current_hash TEXT,
                        timestamp TEXT,
                        difficulty INTEGER,
                        nonce INTEGER,
                        transaction_id TEXT,
                        sender TEXT,
                        recipient TEXT,
                        amount NUMERIC
                        )""")

    # initialize a list to store blocks information
    blocks_info = []

    def get_amount(block):
        return block.transactions.tx_Outs[-1].amount

    def get_recipient_address(block):
        return block.transactions.tx_Outs[-1].address

    def get_sender(block):
        if isinstance(block, Block):
            if block.index != 0:
                prev_block = blockchain.chain[block.index-1]
                if isinstance(prev_block, Block):
                    return blockchain.chain[block.index - 1].transactions.tx_Outs[-1].address
                elif isinstance(prev_block, dict):
                    return blockchain.chain[block.index - 1]['transactions']['tx_Outs'][-1]['address']
            elif block.index == 0:
                return 'Coinbase'

        elif isinstance(block, dict):
            if block['index'] != 0:
                return blockchain.chain[block['index']-1]['transactions']['tx_Outs'][-1]['address']
            elif block['index'] == 0:
                return 'Coinbase'

    # loop all blocks in blockcahin and retrieve all data
    for block in blockchain.chain:
        if isinstance(block, Block):
            block_info = {
                'block index': block.index,
                'previous hash': block.previous_hash,
                'timestamp': block.timestamp,
                'difficulty': block.difficulty,
                'nonce': block.nonce,
                'current hash': block.hash,
                'transaction': {
                    'transaction id': block.transactions.id,
                    'amount': get_amount(block),
                    'sender': get_sender(block),
                    'recipient': get_recipient_address(block)
                }
            }

            # create variables to make the code less messy
            index = block_info['block index']
            previous_hash = block_info['previous hash']
            current_hash = block_info['current hash']
            timestamp = block_info['timestamp']
            difficulty = block_info['difficulty']
            nonce = block_info['nonce']
            txid = block_info['transaction']['transaction id']
            sender = block_info['transaction']['sender']
            recipient = block_info['transaction']['recipient']
            amount = block_info['transaction']['amount']

            # insert block information into blockchain.db
            c_blockchain.execute(
                "INSERT INTO blockchain (block_index, previous_hash, current_hash, timestamp, difficulty, "
                "nonce, transaction_id, sender, recipient, amount) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (index, previous_hash, current_hash, timestamp, difficulty, nonce, txid, sender,
                 recipient, amount))

            # add block information into list
            blocks_info.append(block_info)

            # commit the insertion
            conn_blockchain.commit()

        elif isinstance(block, dict):
            block_info = {
                'block index': block['index'],
                'previous hash': block['previous_hash'],
                'timestamp': block['timestamp'],
                'difficulty': block['difficulty'],
                'nonce': block['nonce'],
                'current hash': block['hash'],
                'transaction': {
                    'transaction id': block['transactions']['id'],
                    'amount': block['transactions']['tx_Outs'][-1]['amount'],
                    'sender': get_sender(block),
                    'recipient': block['transactions']['tx_Outs'][-1]['address']
                }
            }

            # create variables to make the code less messy
            index = block_info['block index']
            previous_hash = block_info['previous hash']
            current_hash = block_info['current hash']
            timestamp = block_info['timestamp']
            difficulty = block_info['difficulty']
            nonce = block_info['nonce']
            txid = block_info['transaction']['transaction id']
            sender = block_info['transaction']['sender']
            recipient = block_info['transaction']['recipient']
            amount = block_info['transaction']['amount']

            # insert block information into blockchain.db
            c_blockchain.execute(
                "INSERT INTO blockchain (block_index, previous_hash, current_hash, timestamp, difficulty, "
                "nonce, transaction_id, sender, recipient, amount) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (index, previous_hash, current_hash, timestamp, difficulty, nonce, txid, sender,
                 recipient, amount))

            # add block information into list
            blocks_info.append(block_info)

            # commit the insertion
            conn_blockchain.commit()

    responses = {'Length of Blockchain': len(blockchain.chain),
                 'Blockchain': blockchain.chain,
                 'Blocks information': blocks_info}
    return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 200


@app.route('/get_keys_and_address/', methods=['GET'])
def generate_key_pairs():

    # generate private key
    private_key = get_private_key()

    # keep track of private key
    blockchain.private_key.append(private_key)

    # get latest block
    prev_block = blockchain.get_latest_block()

    # create TxIn object
    txin = TxIn(prev_block, blockchain.private_key[-1])

    # get public key from TxIn object
    public_key = txin.public_key

    # get address from TxIn object
    address = txin.get_address(txin.public_key)

    responses = {'recipient private key': blockchain.private_key[-1],
                 'recipient public key': public_key,
                 'recipient address': address}

    return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 200


@app.route('/transactions/new/', methods=['POST'])
def new_transaction():

    # retrieve json data
    values = request.get_json()

    # Check that the required fields are in the POST data
    required = ['sender address', 'recipient address', 'amount']
    if not all(k in values for k in required):
        return json.dumps({'message': 'please input sender address, recipient address and amount!!'},
                          default=lambda x: getattr(x, '__dict__', str(x))), 400

    # assign variables
    amount = values['amount']
    sender_address = values['sender address']
    recipient_address = values['recipient address']

    # check if a amount in tx is valid or not
    if not valid_amount(amount, sender_address):
        return json.dumps({'message': 'invalid address or amount'},
                          default=lambda x: getattr(x, '__dict__', str(x))), 400

    # get latest block
    prev_block = blockchain.get_latest_block()

    # create three objects: TxIn, TxOut and Transaction
    txin = TxIn(prev_block, blockchain.private_key[-1])
    txout = TxOut(values['recipient address'], values['amount'])
    tx = Transaction(txin, txout)

    # check if a transaction is valid with p2pkh algorithm
    if P2PKH(blockchain.private_key[-1], tx, txin, txout):

        # if valid with p2pkh, add this transaction to list of 'unconfirmed_transaction'
        blockchain.unconfirmed_transactions.append(tx)

        # update user account
        blockchain.wallets[sender_address] -= amount
        blockchain.wallets[recipient_address] = 50 + amount

        # store the current account in redis (in-memory database)
        r.set(sender_address, '{:.2f}'.format(blockchain.wallets[sender_address]))
        r.set(recipient_address, '{:.2f}'.format(blockchain.wallets[recipient_address]))

        p2pkh_message = 'pass p2pkh check, valid transaction!'

        if isinstance(prev_block, Block):
            responses = {'P2PKH message': p2pkh_message,
                         'message': f'Transaction will be added to Block {prev_block.index + 1}'}
            return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 200
        elif isinstance(prev_block, dict):
            responses = {'P2PKH message': p2pkh_message,
                         'message': f"Transaction will be added to Block {prev_block['index'] + 1}"}
            return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 200

    else:
        p2pkh_message = 'cannot pass p2pkh check, invalid transaction'

        responses = {'P2PKH message': p2pkh_message}

        return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 400


@app.route('/mine/', methods=['GET'])
def mine():
    if blockchain.mine_block():
        responses = {'message': 'mine block successfully!'}
        return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 200
    else:
        responses = {'message': 'cannot mine new block'}
        return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 400


@app.route('/accounts/', methods=['GET'])
def accounts():

    responses = []

    # retrieve data from redis in-memory database
    for key in blockchain.wallets.keys():
        if r.get(key):
            response = {'user': key,
                        'amount of bitcoin': float(r.get(key))}
            responses.append(response)

    return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 200


@app.route('/nodes/register/', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    responses = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 200


@app.route('/nodes/resolve/', methods=['GET'])
def consensus():

    replaced = blockchain.resolve_conflicts()

    if replaced:
        responses = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        responses = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 200


@app.route('/get_chain/<url>/', methods=['GET'])
def get_chain(url):
    response = requests.get(f'http://localhost:{url}/chain/')
    if response.status_code == 200:
        responses = {f'blockchain from {url}': response.json()}
        return json.dumps(responses, default=lambda x: getattr(x, '__dict__', str(x))), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port, debug=True)
    # app.run(host='192.168.0.157', port=port, debug=True)

