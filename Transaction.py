#!/usr/bin/env python
# coding: utf-8

# In[7]:

import Signatures  # from signatures.py file
# Signatures.sign
# Signatures.verify

class Tx:
    inputs = None   # list of input addresses
    outputs = None   # list of output addresses
    sigs = None 
    reqd = None      # to facilitate escrow transactions -- list of required sigs that are not inputs
    
    def __init__(self):
        self.inputs = []
        self.outputs = []
        self.sigs = []
        self.reqd = []
        
    def add_input(self, from_addr, amount, index=0):
        self.inputs.append((from_addr, amount, index)) # append in a tuple to string tgt address and amount
    
    def add_output(self, to_addr, amount):
        self.outputs.append((to_addr, amount))
    
    def add_reqd(self, addr):
        self.reqd.append(addr)
    
    def sign(self, private):
        message = self.__gather()  #this is a private member function
        newsig = Signatures.sign(message, private)  # sign with private key
        self.sigs.append(newsig) # add to list of signatures
    
    def is_valid(self):
        total_in = 0
        total_out = 0
        
        message = self.__gather()
        for addr, amount, inx in self.inputs:   #check all the inputs are valid
            found = False
            for s in self.sigs:   # run through the signatures to find it
                if Signatures.verify(message, s, addr): 
                    found = True
            if not found:
                return False
            # Detect negative inputs  
            if amount < 0:
                return False
            # To detect mismatch between inputs and outputs
            total_in = total_in + amount
            
        # Detect escrow transactions
        for addr in self.reqd:     # check all required addresses are valid
            found = False
            for s in self.sigs:   
                if Signatures.verify(message, s, addr): 
                    found = True
            if not found:
                return False
            
        # Detect negative outputs  
        for addr, amount in self.outputs:
            if amount < 0:
                return False
        
        total_out = total_out + amount
        
        # Detect mismatch between inputs and outputs - but need to allow for miner rewards
        #if total_out > total_in:
        #    print("Outputs exceed inputs")
        #    return False
        
        return True
    
    def __gather(self):
        data = []
        data.append(self.inputs)
        data.append(self.outputs)
        data.append(self.reqd)
        return data
    
    def __repr__(self):
        reprstr = "INPUTS: \n"
        for addr, amount, inx in self.inputs:
            reprstr = reprstr + str(amount) + "from" + str(addr) + " inx = " + str(inx) + "\"n"
        reprstr = reprstr + "OUTPUTS: \n"
        
        for addr, amount in self.outputs:
            reprstr = reprstr + str(amount) + "to" + str(addr) + "\n"
        reprstr = reprstr + "REQD: \n"
        
        for r in self.reqd:
            reprstr = reprstr + str(r) + "\n"
        reprstr = reprstr + "SIGS: \n"
        
        for s in self.sigs:
            reprstr = reprstr + str(s) + "\n"
        reprstr = reprstr + "END \n"
        return reprstr
    
if __name__ == "__main__":
    pr1, pu1 = Signatures.generate_keys()
    pr2, pu2 = Signatures.generate_keys()
    pr3, pu3 = Signatures.generate_keys()
    pr4, pu4 = Signatures.generate_keys()

# First valid transaction
    Tx1 = Tx()  # Tx1 initialises a transaction
    Tx1.add_input(pu1, 1)
    Tx1.add_output(pu2, 1)
    Tx1.sign(pr1)

# Test a transaction with more than one output
    Tx2 = Tx()
    Tx2.add_input(pu1, 2)   # sends more output
    Tx2.add_output(pu2, 1)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr1)           # signature is always the input
    
# Test an escrow transaction
    Tx3 = Tx()
    Tx3.add_input(pu3, 1.2)   # pu3 sends 1.2 to pu1
    Tx3.add_output(pu1, 1.1)  # but here pu1 only receives 1.1 (not miner fee here)
    Tx3.add_reqd(pu4)         # Escrow transaction needs required signature
    Tx3.sign(pr3)
    Tx3.sign(pr4)             # This is the required signature
    
    # Test the validity in a loop
    for t in [Tx1, Tx2, Tx3]:
        if t.is_valid():
            print("Success! Tx is valid")
        else:
            print("Error, Tx is invalid")


            
# Simluate some attackers
            
# Test wrong key used to sign
    Tx4 = Tx()
    Tx4.add_input(pu1, 1)
    Tx4.add_output(pu2, 1)
    Tx4.sign(pr2)     # Error simluated here where pu2 uses their sig to sign
    
# Escrow transaction not signed by arbiter
    Tx5 = Tx()
    Tx5.add_input(pu3, 1.2)   
    Tx5.add_output(pu1, 1.1)
    Tx5.add_reqd(pu4)         # Escrow transaction needs required signature
    Tx5.sign(pr3)             # not signed by arbiter to simulate error
    
# Two input addresses but only signed by one
    Tx6 = Tx()
    Tx6.add_input(pu3, 1)  
    Tx6.add_input(pu4, 0.1)   
    Tx6.add_output(pu1, 1.1)
    Tx6.sign(pr3)         # Only pu3 is signed

# Tampered tx index
    Tx7 = Tx()
    Tx7.add_input(pu3, 1)  
    Tx7.add_input(pu4, 0.1)   
    Tx7.add_output(pu1, 1.1)
    Tx7.sign(pr3)
    tmp = Tx7.inputs[0]
    Tx7.inputs[0] = (tmp[0], tmp[1], 78)
    
# Signature that uses negative inputs (to receive unlimited coins)
    Tx8 = Tx()
    Tx8.add_input(pu2, -1)  
    Tx8.add_output(pu1, -1)
    Tx8.sign(pr2)
    
# Modified Tx after it has been signed
    Tx9 = Tx()
    Tx9.add_input(pu1, 1)
    Tx9.add_output(pu2, 1)
    Tx9.sign(pr1)
    # outputs = [(pu2,1)]
    # changed to = [(pu3,1)]
    Tx9.outputs[0] = (pu3, 1)   # replace first element in tuple with pu3
    
    for t in [Tx4, Tx5, Tx6, Tx7, Tx8, Tx9]:
        if t.is_valid():
            print("Error! Bad Tx is valid")
        else:
            print("Succsess, Bad Tx is invalid")

        


# In[ ]:




