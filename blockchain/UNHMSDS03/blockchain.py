import json
import hashlib
import datetime as date

class Block:
    last_index = 0  # Class variable to keep track of the last index used

    def __init__(self, **kwargs):
        self.index = kwargs.get('index')
        self.timestamp = kwargs.get('timestamp')
        self.data = kwargs.get('data')
        self.previous_hash = kwargs.get('previous_hash')
        self.hash = kwargs.get('hash')
        Block.last_index = self.index  # Update last_index

    def calculate_hash(self):
        hash_string = str(self.index) + str(self.timestamp) + str(self.data) + str(self.previous_hash)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def to_dict(self):
        return {
            'index': self.index,
            'timestamp': str(self.timestamp),
            'data': self.data,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }
    
    @staticmethod
    def from_dict(json_data):
        return Block(**json_data)
    
    @classmethod
    def from_dict_to_block(cls, dict_data):
        return cls(**dict_data)
    
class Blockchain:
    def __init__(self):
        self.chain = self.load_chain()  # Load chain from file or create a new one if no file found

    def create_genesis_block(self):
        return Block(0, date.datetime.now(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]
    
    def create_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.hash = new_block.calculate_hash()
        return new_block

    def add_block(self, new_block):
        # new_block.previous_hash = self.get_latest_block().hash
        # new_block.hash = new_block.calculate_hash()
        self.chain.append(new_block)
        self.save_chain()  # Save chain to file after adding the new block

    def is_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True
    
    def load_chain(self):
        try:
            with open('blockchain.json', 'r') as f:
                chain_data = json.load(f)
                if chain_data:
                    Block.last_index = chain_data[-1]['index']  # Set last_index to the index of the last block loaded
                return [Block(**block) for block in chain_data]
        except FileNotFoundError:
            return [self.create_genesis_block()]

    def save_chain(self):
        with open('blockchain.json', 'w') as f:
            chain_data = [{'index': block.index,
                           'timestamp': str(block.timestamp),
                           'data': block.data,
                           'previous_hash': block.previous_hash,
                           'hash': block.hash} for block in self.chain]
            json.dump(chain_data, f, indent=4)

