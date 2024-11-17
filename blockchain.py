import hashlib
import json
import time
from uuid import uuid4
from flask import Flask, request, jsonify


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        # genesis block
        self.new_block(proof=100, previous_hash=1)

    def new_block(self, proof, previous_hash=None):
        """
        Function to create a new block in the blockchain.
        :param proof: <int> the proof given by the proof of work algorithm
        :param previous_hash: (Optional) <str> hash of previous block
        :return: <dict> new block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Function to create a new transaction in the blockchain.
        :param sender: <str> the address of the sender
        :param recipient: <str> the address of the recipient
        :param amount: <int> the amount
        :return: <int> the new transaction's index'
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof):
        """
        Function for the proof of work algorithm. The algorithm:
        - Find a number p' such that hash(pp') has 4 leading 0s
        - p is the previous proof and p' is the new proof
        :param last_proof: <int> the previous proof
        :return: <int> the new proof
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def hash(block):
        """
        Function to create a new SHA-256 hash for blocks.
        :param block: <str> the block
        :return: <str> SHA-256 hash
        """

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Function to validate the proof given by proof of work. Does the proof has 4 leading 0s.
        :param last_proof: <int> the previous proof
        :param proof: <int> the current proof
        :return: <bool> True if correct, False otherwise
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    @property
    def last_block(self):
        return self.chain[-1]


# API FUNCTIONALITY
app = Flask(__name__)

# generate a global unique address for the above node
node_id = str(uuid4()).replace('-', '')

# initialize blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    # run proof of work algorithm
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block['proof'])
    blockchain.new_transaction(
        sender="0",
        recipient=node_id,
        amount=1,
    )

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # check if required details are in the POST request
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return "Missing values", 400

    # create a new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


