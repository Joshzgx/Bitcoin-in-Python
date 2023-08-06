#!/usr/bin/env python
# coding: utf-8

# In[3]:

from cryptography.hazmat.primitives import hashes

# Creating the hash
digest = hashes.Hash(hashes.SHA256())
digest.update(b"abc") # first data
digest.update(b"123") # second data

hash = digest.finalize()
print(hash)


# Modifying the message to compare the output -- hash is non-malleable
digest = hashes.Hash(hashes.SHA256())
digest.update(b"abc") # first data
digest.update(b"124") # second data

hash = digest.finalize()
print(hash)


#Creating a Blockchain
class someClass:
    string = None
    num = 328901
    def __init__(self, mystring):
        self.string = mystring
    def __repr__(self):
        return self.string + "^^^" + str(self.num) # important to include num in return
                                                   # Otherwise changing it will not be detected later on
        
class CBlock:
    data = None
    previousHash = None # need to store previous hash to prevent tampering
    previousBlock = None
    
    def __init__(self, data, previousBlock):
        self.data = data
        self.previousBlock = previousBlock
        if previousBlock != None:
            self.previousHash = previousBlock.computeHash()
            
    def computeHash(self):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(bytes(str(self.data),'utf8'))  
        digest.update(bytes(str(self.previousHash),'utf8'))  # Very impt. to securing the blockchain 
        return digest.finalize()          # Each prev. hash must be referenced

    def is_valid(self):
        if self.previousBlock == None:
            return True    # dangerous thing to do, only genesis block should be this
        return self.previousBlock.computeHash() == self.previousHash
    
# Showing that we can pass through all of these in a blockchain
# The blockchain can store all of these
if __name__ == '__main__':
    root = CBlock(b'I am root', None)
    B1 = CBlock('I am a child', root)
    B2 = CBlock('I am B1s brother', root)
    B3 = CBlock(12345, B1)
    B4 = CBlock(someClass('Hi there!'), B3)
    B5 = CBlock('Top block', B4)
    
    for b in [B1, B2, B3, B4, B5]:
        if b.previousBlock.computeHash() == b.previousHash:
            print('Success, hash is good')
        else:
            print('Error, hash is not good')

# If we are an attacker,
    # Editing B3's data --> check B4 which is the next block
    B3.data = 12354
    if B4.previousBlock.computeHash() == B4.previousHash:
        print('Error, could not detect tampering')
    else:
        print('Success, tampering detected')

# Try to edit B4 to simulate tampering of the classes
    print(B4.data)
    B4.data.num = 99999
    print(B4.data)
    if B5.previousBlock.computeHash() == B5.previousHash:
        print('Error, could not detect tampering')
    else:
        print('Success, tampering detected')


# In[ ]:




