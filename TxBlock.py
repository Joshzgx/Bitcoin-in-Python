#TxBlock
from Blockchain import CBlock
from Signatures import generate_keys, sign, verify
from Transaction import Tx
import pickle
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import random
from cryptography.hazmat.primitives import hashes
import time

reward = 25.0
leading_zeros = 2
next_char_limit = 200  # lower no. for harder mining difficulty

class TxBlock (CBlock):
    nonce = "AAAAAAA"
    def __init__(self, previousBlock):
        super(TxBlock, self).__init__([], previousBlock)
    
    def addTx(self, Tx_in):
        self.data.append(Tx_in)

    def removeTx(self, Tx_in):
        if Tx_in in self.data:
            self.data.remove(Tx_in)
            return True
        return False

    def count_totals(self):
        total_in = 0
        total_out = 0
        for tx in self.data:
            for addr, amt, inx in tx.inputs:
                total_in = total_in + amt
            for addr, amt in tx.outputs:
                total_out = total_out + amt
        return total_in, total_out
    
    def check_size(self):
        savePrev = self.previousBlock
        self.previousBlock = None
        this_size = len(pickle.dumps(self))
        self.previousBlock = savePrev
        if this_size > 10000: #checking the size here
            return False
        return True

    def is_valid(self):
        if not super(TxBlock, self).is_valid():
            return False
        spends = {} # empty dictionary to keep track
        for tx in self.data:
            if not tx.is_valid():
                return False
            for addr, amt, inx in tx.inputs:
                if addr in spends:
                    spends[addr] = spends[addr] + amt
                else:
                    spends[addr] = amt
                if not inx == getLastTxIndex(addr,self.previousBlock) + 1:
                    return False
            
            for addr, amt in tx.outputs:
                if addr in spends:
                    spends[addr] = spends[addr] - amt
                else:
                    spends[addr] = - amt
        for this_addr in spends:
            print("Balance: " + str(getBalance(this_addr,self.previousBlock)))
            print("Spends: " + str(spends[this_addr]))
            if spends[this_addr] - getBalance(this_addr,self.previousBlock) > 0.0000000000001:
                return False

        total_in, total_out = self.count_totals()
        if total_out - total_in - reward > 0.000000000001:
            return False
        if not self.check_size(): #size needed for validity
            return False
        return True
    
    def good_nonce(self):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(bytes(str(self.data),'utf8'))
        digest.update(bytes(str(self.previousHash),'utf8'))
        digest.update(bytes(str(self.nonce),'utf8'))
        this_hash = digest.finalize()
       
        if this_hash[:leading_zeros] != bytes(''.join([ '\x4f' for i in range(leading_zeros)]),'utf8'):
            return False
        return int(this_hash[leading_zeros]) < next_char_limit
    
    def find_nonce(self,n_tries=1000000): # try 1million times
        for i in range(n_tries):
            self.nonce = ''.join([ 
                   chr(random.randint(0,255)) for i in range(10*leading_zeros)])
            if self.good_nonce():
                return self.nonce  
        return None
    
def findLongestBlockchain(head_blocks):
    longest = -1 # So anything is larger than -1
    long_head = None
    for b in head_blocks:
        current = b
        this_len = 0
        while current != None: # track backwards by one block each time
            this_len = this_len + 1
            current = current.previousBlock # to eventually find genesis block
        if this_len > longest: # then now we'll know the length of the blockchain
            long_head = b
            longest = this_len
    return long_head

# Function to save/load headblocks
def saveBlocks(block_list, filename):
    fp = open(filename, "wb")
    pickle.dump(block_list, fp)
    fp.close()
    return True

def loadBlocks(filename):
    fin = open(filename, "rb")
    ret = pickle.load(fin)
    fin.close()
    return ret

def getBalance(pu_key, head_block): # is head_block last_block?
    this_block = head_block
    bal = 0.0
    while this_block != None:
        for tx in this_block.data:
            for addr,amt,inx in tx.inputs:
                if addr == pu_key:
                    bal = bal - amt
            for addr,amt in tx.outputs:
                if addr == pu_key:
                    bal = bal + amt
        this_block = this_block.previousBlock
    return bal

def getLastTxIndex(pu_key, head_block):
    this_block = head_block
    index = -1
    while this_block != None:
        for tx in this_block.data:
            for addr,amt,inx in tx.inputs:
                if addr == pu_key:
                    return inx
        this_block = this_block.previousBlock
    return -1

if __name__ == "__main__":
    pr1, pu1 = generate_keys()
    pr2, pu2 = generate_keys()
    pr3, pu3 = generate_keys()

    indeces = {pu1:0, pu2:0, pu3:0}
    def indexed_input(Tx_inout, public_key, amt, index_map):
        Tx_inout.add_input(public_key, amt, index_map[public_key])
        index_map[public_key] = index_map[public_key] + 1

    Tx1 = Tx()
    indexed_input(Tx1, pu1, 1, pu_indeces)
    Tx1.add_output(pu2, 1)
    Tx1.sign(pr1)

    if Tx1.is_valid():
        print("Success! Tx is valid")

    savefile = open("tx.dat", "wb")
    pickle.dump(Tx1, savefile)
    savefile.close()

    loadfile = open("tx.dat", "rb")
    newTx = pickle.load(loadfile)

    if newTx.is_valid():
        print("Success! Loaded tx is valid")
    loadfile.close()

    root = TxBlock(None)
    # Add some initial mining rewards
    mine1 = Tx()
    mine1.add_output(pu1, 8.0)
    mine1.add_output(pu2, 8.0)
    mine1.add_output(pu3, 8.0)

    root.addTx(Tx1)
    root.addTx(mine1)

    Tx2 = Tx()
    indexed_input(Tx1, pu1, 1, pu_indeces)
    Tx2.add_input(pu2,1.1)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr2)
    root.addTx(Tx2)

    B1 = TxBlock(root)
    Tx3 = Tx()
    indexed_input(Tx1, pu1, 1, pu_indeces)
    Tx3.add_input(pu3,1.1)
    Tx3.add_output(pu1, 1)
    Tx3.sign(pr3)
    B1.addTx(Tx3)
    
    Tx4 = Tx()
    indexed_input(Tx1, pu1, 1, pu_indeces)
    Tx4.add_input(pu1,1)
    Tx4.add_output(pu2, 1)
    Tx4.add_reqd(pu3)
    Tx4.sign(pr1)
    Tx4.sign(pr3)
    B1.addTx(Tx4)
    start = time.time()
    print(B1.find_nonce())
    elapsed = time.time() - start
    print("elapsed time: " + str(elapsed) + " s.")
    if elapsed < 60:
        print("ERROR! Mining is too fast")
    if B1.good_nonce():
        print("Success! Nonce is good!")
    else:
        print("ERROR! Bad nonce")
    

    savefile = open("block.dat", "wb")
    pickle.dump(B1, savefile)
    savefile.close()

    loadfile = open("block.dat" ,"rb")
    load_B1 = pickle.load(loadfile)

    for b in [root, B1, load_B1, load_B1.previousBlock]:
        if b.is_valid():
            print ("Success! Valid block")
        else:
            print ("ERROR! Bad block")

    if B1.good_nonce():
        print("Success! Nonce is good after save and load!")
    else:
        print("ERROR! Bad nonce after load")
    
    # Test one bad block, B2. Hence skip it
    B2 = TxBlock(B1)
    Tx5 = Tx()
    indexed_input(Tx1, pu1, 1, pu_indeces)
    Tx5.add_input(pu3, 1)
    Tx5.add_output(pu1, 100)
    Tx5.sign(pr3)
    B2.addTx(Tx5)

    load_B1.previousBlock.addTx(Tx4)
    for b in [B2, load_B1]:
        if b.is_valid():
            print ("ERROR! Bad block verified.")
        else:
            print ("Success! Bad blocks detected")

    # Test mining rewards and tx fees
    pr4, pu4 = generate_keys()
    B3 = TxBlock(B1) # skipped B2 since it is a bad block
    B3.addTx(Tx2)
    B3.addTx(Tx3)
    B3.addTx(Tx4)
    Tx6 = Tx()
    Tx6.add_output(pu4,25)
    B3.addTx(Tx6)
    if B3.is_valid():
        print ("Success! Block reward succeeds")
    else:
        print("ERROR! Block reward fail")

    B4 = TxBlock(B3)
    B4.addTx(Tx2)
    B4.addTx(Tx3)
    B4.addTx(Tx4)
    Tx7 = Tx()
    Tx7.add_output(pu4,25.2)
    B4.addTx(Tx7)
    if B4.is_valid():
        print ("Success! Tx fees succeeds")
    else:
        print("ERROR! Tx fees fail")

    #Greedy miner
    B5 = TxBlock(B4)
    B5.addTx(Tx2)
    B5.addTx(Tx3)
    B5.addTx(Tx4)
    Tx8 = Tx()
    Tx8.add_output(pu4,26.2)
    B5.addTx(Tx8)
    if not B5.is_valid():
        print ("Success! Greedy miner detected")
    else:
        print("ERROR! Greedy miner not detected")
    
    # Test some other transactions following B4
    # We want to limit block size
    B6 = TxBlock(B4) # Since B5 is invalid greedy miner
    this_pu = pu4
    this_pr = pr4
    for i in range(30):
        newTx = Tx()
        new_pr, new_pu = generate_keys()
        newTx.add_input(this_pu,0.3)
        newTx.add_output(new_pu,0.3)
        newTx.sign(this_pr)
        B6.addTx(newTx)
        this_pu, this_pr = new_pu, new_pr
        savePrev = B6.previousBlock
        B6.previousBlock = None
        this_size = len(pickle.dumps(B6))
        print("Size = " + str(this_size))
        B6.previousBlock = savePrev
        if B6.is_valid() and this_size > 10000:
            print("Error! Big blocks are valid when should be invalid: size = ", str(this_size))
        elif (not B6.is_valid()) and this_size <= 10000:
            print("Error! Small blocks are invalid when should be valid: size = ", str(this_size))
        else:
            print("Success! Block size check passed.")

    # Test an overspending scenarios
    overspend = Tx()
    overspend.add_input(pu1, 45.0)
    overspend.add_output(pu2, 44.5)
    overspend.sign(pr1)
    B7 = TxBlock(B4)
    B7.addTx(overspend)
    if B7.is_valid():
        print("Error! Overspend not detected")
    else:
        print("Success! Overspend detected")

    overspend1 = Tx()
    overspend1.add_input(pu1, 5.0)
    overspend1.add_output(pu2, 4.5)
    overspend1.sign(pr1)

    overspend2 = Tx()
    overspend2.add_input(pu1, 15.0)
    overspend2.add_output(pu3, 14.5)
    overspend2.sign(pr1)

    overspend3 = Tx()
    overspend3.add_input(pu1, 5.0)
    overspend3.add_output(pu4, 4.5)
    overspend3.sign(pr1)

    overspend4 = Tx()
    overspend4.add_input(pu1, 8.0)
    overspend4.add_output(pu2, 4.5)
    overspend4.sign(pr1)

    B8 = TxBlock(B4)
    B8.addTx(overspend1)
    B8.addTx(overspend2)
    B8.addTx(overspend3)
    B8.addTx(overspend4)

    if B8.is_valid():
        print("Error! Overspend 1,2,3,4 not detected")
    else:
        print("Success! Overspend 1,2,3,4 detected")

    


    

    

    
    
