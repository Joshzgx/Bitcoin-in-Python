#Wallet has issues

# Eth blockchain vs Btc blockchain
# difference is in duplicate Txs

import SocketUtils
import Transaction
import TxBlock
import Signatures
import pickle

head_blocks = [None]
wallets = [('localhost',5006)] # wallet is 5006
miners = [('localhost',5005)]
break_now = False
my_public,my_private = Signatures.generate_keys()
tx_index = 0 #

def StopAll():
    global break_now
    break_now = True

def walletServer(my_addr):
    global head_blocks
    try:
        head_blocks = TxBlock.loadBlocks("WalletBlocks.dat")
    except:
        print("WS:No previous blocks found. Starting fresh.")
        head_blocks = TxBlock.loadBlocks("Genesis.dat")

    server = SocketUtils.newServerConnection('localhost',5006)
    while not break_now:
        newBlock = SocketUtils.recvObj(server)
        if isinstance(newBlock,TxBlock.TxBlock):
            print("Received Block")
            found = False
            # Add new block to the blockchain
            for b in head_blocks:
                if b == None:
                    if newBlock.previousHash == None: # if no hash it is parent /genesis
                            found = True
                            newBlock.previousBlock = b 
                            # Check validity of signature of the new block
                            if not newBlock.is_valid():
                                print("Error! newBlock is not valid")
                            else:
                                head_blocks.remove(b)
                                head_blocks.append(newBlock)
                                print("Added to head blocks")

                    elif newBlock.previousHash == b.computeHash(): # this is the new headblock
                        found = True
                        newBlock.previousBlock = b 
                        if not newBlock.is_valid():
                            print("Error! newBlock is not valid")
                        else:
                            head_blocks.remove(b)
                            head_blocks.append(newBlock)
                            print("Added to head blocks")
                    else:
                        this_block = b
                        while this_block != None:
                            if newBlock.previousHash == this_block.previousHash: # if they have same parent
                                found = True
                                newBlock.previousBlock = this_block.previousBlock
                                if not newBlock in head_blocks:
                                    head_blocks.append(newBlock) # sister block is a candidate for valid headblock
                                print("Added new sister block")
                            this_block = this_block.previousBlock
                    if not found:
                        print("Error! Couldn't find a parent for newBlock")
                        # TODO handle orphaned blocks - store those away to find parent and handle
    
    TxBlock.saveBlocks(head_blocks,"WalletBlocks.dat") # Save the headblock
    server.close()
    return True

def getBalance(pu_key):
    long_chain = TxBlock.findLongestBlockchain(head_blocks)
    return TxBlock.getBalance(pu_key, long_chain)

def sendCoins(pu_send, amt_send, pr_send, pu_recv, amt_recv): # wallet can show private keys of sender
    newTx = Transaction.Tx()
    # Assign every transaction with an index to make it unique
    # So we can order transactions
    newTx.add_input(pu_send, amt_send, tx_index) # called tx nonce in Eth
    newTx.add_output(pu_recv, amt_recv)
    newTx.sign(pr_send)
    for ip,port in miners:
        SocketUtils.sendObj(ip,newTx,port)
    tx_index = tx_index + 1
    return True

# Function to load keys
def loadKeys(pr_file, pu_file):
    return Signatures.loadPrivate(pr_file), Signatures.loadPublic(pu_file)



# Tests
if __name__ == "__main__":
    import Signatures
    import threading
    import time
    import Miner

    # Try to simulate a thief that does replay attacks
    # Thief might pose as a miner
    # but thief cannot resign private keys
    def Thief(my_addr):
        my_ip, my_port = my_addr
        # Open a server connection
        server = SocketUtils.newServerConnection(my_ip, my_port)
        # Get Txs from wallets
        while not break_now: # to 
            newTx = SocketUtils.recvObj(server)
            if isinstance(newTx,Transaction.Tx): 
                for ip,port in miners: # but thief is disguising as miner
                    # so thief needs to not include himself in this loop
                    if not (ip == my_ip and port == my_port): # "if not me"
                        SocketUtils.sendObj(ip,newTx,port) # Received the tx and send it out again


    miner_pr, miner_pu = Signatures.generate_keys()

    t1 = threading.Thread(target=Miner.minerServer, args=(('localhost',5005),))
    t2 = threading.Thread(target=Miner.nonceFinder, args=(wallets, miner_pu))
    t3 = threading.Thread(target=walletServer, args=(('localhost',5006),))
            
    t1.start()
    t2.start()
    t3.start()

    pr1,pu1 = loadKeys("private.key", "public.key")
    pr2,pu2 = Signatures.generate_keys()
    pr3,pu3 = Signatures.generate_keys()

    # Query Balances
    bal1 = getBalance(pu1)
    print(bal1)
    bal2 = getBalance(pu2)
    print(bal2)
    bal3 = getBalance(pu3)
    print(bal3)

    # Send coins from wallet that only has private keys of pr1
    # Simulate block of transactions that should be too big
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)

    # t2.start()
    time.sleep(60) # give time for miner to mine

    # Save/Load all blocks
    TxBlock.saveBlocks(head_blocks, "AllBlocks.dat")
    head_blocks = TxBlock.loadBlocks("AllBlocks.dat")

    # Query Balances Test
    new1 = getBalance(pu1)
    print("Balance 1 =" + str(new1))
    new2 = getBalance(pu2)
    print("Balance 2 =" + str(new2))
    new3 = getBalance(pu3)
    print("Balance 3 =" + str(new3))

    # Verify Balances
    if abs(new1-bal1 + 2.0) > 0.00000001:
        print("Error! Wrong balance for pu1")
    else:
        print("Success! Good Balance of pu1")

    if abs(new2-bal2 - 1.0) > 0.00000001:
        print("Error! Wrong balance for pu2")
    else:
        print("Success! Good Balance of pu2") 
    
    if abs(new3-bal3 - 0.3) > 0.00000001:
        print("Error! Wrong balance for pu3")
    else:
        print("Success! Good Balance of pu3") 

    # Thief will try to duplicate transactions
    miners.append(('localhost',5007)) # thief will try to look like miner
    t4 = threading.Thread(target=Thief,args=(('localhost',5007),))
            # extra comma to remind args is a tuple with one element
            # the element should be a tuple with (localhost, port)
    t4.start()
    sendCoins(pu2, 0.2, pr2, pu1, 0.2)
    time.sleep(20)
    # Check balances
    newnew1 = getBalance(pu1)
    print(newnew1)
    if abs(newnew1 - new1 - 0.2) > 0.0000000001:
        print("Error! Duplicate Txs accepted")
    else:
        print("Success! Duplicate Txs rejected")


    Miner.StopAll()

    # Since there might be shorter sister chains, 
    # Need to test what happens if newTx is added to that
    num_heads = len(head_blocks)
    sister = TxBlock.TxBlock(head_blocks[0].previousBlock.previousBlock) # 2 blocks back
    sister.previousBlock = None
    SocketUtils.sendObj('localhost', sister, 5006) # send to wallet (5006)
    time.sleep(10)
    if (len(head_blocks) == num_heads + 1):
        print("Success! New head_block created")
    else:
        print("Error! Failed to add sister block")

    StopAll()

    t1.join()
    t2.join()
    t3.join()

    print("Exit Successful")


