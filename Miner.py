#Miner
# In a fee market, miners can choose which transactions to process
# and how to order them (frontrunning) - benefit themselves
# zeromev + robinhood that allows frontrunning
# we also have the issue of impermanent loss

# Does cardano have miners or validators?

import SocketUtils
import Transaction
import TxBlock
import pickle

wallets = [('localhost',5006)] # Miner is 5006
tx_list = []
head_blocks = [None] # To store the most recent block in the blockchain
break_now = False
verbose = True

def StopAll():
    global break_now
    break_now = True

def minerServer(my_addr):
    global tx_list #refer to the global list outside of functions
    global break_now
    try:
        tx_list = loadTxList("Txs.dat")
        if verbose: print("Loaded tx_list has " + str(len(tx_list)) + " Txs.")
    except:
        print("No previous Txs. Starting fresh")
        tx_list = []
    head_blocks = TxBlock.loadBlocks("Genesis.dat")
    print("Genesis block has " + str(len(head_blocks)) + " blocks.")


    my_ip, my_port = my_addr
    # Open a server connection
    server = SocketUtils.newServerConnection(my_ip, my_port)
    # Get Txs from wallets
    while not break_now: # to 
        newTx = SocketUtils.recvObj(server)
        if isinstance(newTx,Transaction.Tx): # Is newTx an instance of transaction?
            tx_list.append(newTx)
            if verbose: print ("Received tx")
    if verbose: print ("Saving " + str(len(tx_list)) + " txs to Txs.dat")
    saveTxList(tx_list,"Txs.dat")
    return False


def nonceFinder(wallet_list, miner_public):
    global break_now
    try:
        head_blocks = TxBlock.loadBlocks("AllBlocks.dat")
    except:
        print("No previous blocks found. Starting fresh.")
    head_blocks = [None]

    # add Txs to new block, must be to the longest chain
    while not break_now:
        newBlock = TxBlock.TxBlock(TxBlock.findLongestBlockchain(head_blocks)) # Parent is longest chain
        placeholder = Transaction.Tx()
        placeholder.add_output(miner_public,25.0)
        #TODO sort tx_list by tx fee per byte
        newBlock.addTx(placeholder)
        for tx in tx_list:
            newBlock.addTx(tx) # add all the transactions
            
            # Txs added must not be too big
            if not newBlock.check_size():
                newBlock.removeTx(tx)
                break
        newBlock.removeTx(placeholder)

        # Compute and add mining reward
        # Placeholder above to check that the mining reward doesnt cause block size to exceed
        total_in,total_out = newBlock.count_totals()
        mine_reward = Transaction.Tx()
        mine_reward.add_output(miner_public,25.0+total_in-total_out)
        newBlock.addTx(mine_reward)

        # Find nonce - mining
        if verbose: print ("Finding Nonce...")
        newBlock.find_nonce(10000)
        if newBlock.good_nonce():
            if verbose: print ("Good nonce found")
            head_blocks.remove(newBlock.previousBlock)
            head_blocks.append(newBlock)

            # Send new block to each in wallet_list only if nonce is good
            savePrev = newBlock.previousBlock
            newBlock.previousBlock = None
            for ip_addr,port in wallet_list:
                if verbose: print("Sending to " + ip_addr + ":" +str(port))
                SocketUtils.sendObj(ip_addr,newBlock,5006) # wallet in port 5006

            # Restore the previous block
            newBlock.previousBlock = savePrev

            # Remove used txs from tx_list (miner should do this)
            for tx in newBlock.data:
                if tx != mine_reward:
                    tx_list.remove(tx)
    TxBlock.saveBlocks(head_blocks,"AllBlocks.dat")
    return True


def loadTxList(filename):
    fin = open(filename, "rb")
    ret = pickle.load(fin)
    fin.close()
    return ret

def saveTxList(the_list, filename):
    fp = open(filename, "wb")
    pickle.dump(the_list, fp)
    fp.close()
    return True



if __name__ == "__main__":
    import threading
    import time
    import Signatures
    
    my_pr, my_pu = Signatures.generate_keys()

    t1 = threading.Thread(target=minerServer, args=(('localhost',5005),))
    t2 = threading.Thread(target=nonceFinder, args=(wallets, my_pu))
    
    server = SocketUtils.newServerConnection('localhost',5006)

    t1.start()
    t2.start()

    pr1,pu1 = Signatures.generate_keys()
    pr2,pu2 = Signatures.generate_keys()
    pr3,pu3 = Signatures.generate_keys()

    Tx1 = Transaction.Tx()
    Tx2 = Transaction.Tx()

    Tx1.add_input(pu1, 4.0)
    Tx1.add_input(pu2, 1.0)
    Tx1.add_output(pu3, 4.8)
    Tx2.add_input(pu3, 4.0)
    Tx2.add_output(pu2, 4.0)
    Tx2.add_reqd(pu1)

    Tx1.sign(pr1)
    Tx1.sign(pr2)
    Tx2.sign(pr3)
    Tx2.sign(pr1)
    new_tx_list = [Tx1, Tx2]
    saveTxList(new_tx_list, "Txs.dat")
    new_new_tx_list = loadTxList("Txs.dat")

    for tx in new_new_tx_list:
        try:
            SocketUtils.sendObj('localhost',Tx1)
            print ("Sent Tx1")
            SocketUtils.sendObj('localhost',Tx2)
            print ("Sent Tx2")
        except:
            print ("Error! Connection unsuccessful")

    # Use different port for this
    for i in range(30):
        newBlock = SocketUtils.recvObj(server)
        if newBlock:
            print("Error! Block not received")
            break

    if newBlock.is_valid():
        print("Success! Block is valid")
    if newBlock.good_nonce():
        print("Success! Nonce is valid")
    for tx in newBlock.data:
        try:
            if tx.inputs[0][0] == pu1 and tx.inputs[0][1] == 4.0:
                print("Tx1 is present")
        except:
            print("Tx1 failed")
        try:
            if tx.inputs[0][0] == pu3 and tx.inputs[0][1] == 4.0:
                print("Tx2 is present")
        except:
            print("Tx2 failed")

    time.sleep(20)
    break_now = True
    time.sleep(2)
    server.close()

    t1.join()
    t2.join()

    print("Done!")







