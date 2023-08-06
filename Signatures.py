#!/usr/bin/env python
# coding: utf-8

# In[4]:

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes #breaks up data
from cryptography.hazmat.primitives.asymmetric import padding #makes hashes more secure
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization


# Creating Public and Private Keys
def generate_keys():
    private = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public = private.public_key()
    
    # to serialise the keys
    pu_ser = public.public_bytes(            # pem to express public and private key
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
        # we do not serialise the private key yet,
        # to remind ourselves that saving the private key should be password protected
    )
    return private, pu_ser

# Creating Signatures
def sign(message, private):
    message = bytes(str(message), 'utf-8') # message must be in bytes
    sig = private.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), #SHA256 is the hash we use
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
    )
    return sig

# Create Verification
def verify(message, sig, pu_ser):
    public = serialization.load_pem_public_key(
        pu_ser,
        #password=None,    # public key does not need password
    )
    message = bytes(str(message), 'utf-8')
    try:
        public.verify(
            sig,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:   # To catch error of invalid signature
        return False
    except:                    # To catch all other errors
        print("Error executing public_key.verify")
        return False

# Create file to save and load private keys
def savePrivate(pr_key, filename):
    pem = pr_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()   
    )

    fp = open(filename, "wb") # wb means write binary
    fp.write(pem)
    fp.close()
    return

def loadPrivate(filename):
    fin = open(filename, "rb") # rb means read binary
    pr_key = serialization.load_pem_private_key(
        fin.read(),
        password=None,
    )
    fin.close()
    return pr_key

# Create file to save and load public keys
# We already have the serialised public key
def savePublic(pu_key, filename):
    fp = open(filename, "wb")
    fp.write(pu_key)
    fp.close()
    return True

def loadPublic(filename):
    fin = open(filename, "rb")
    pu_key = fin.read()
    fin.close()
    return pu_key

def loadKeys(pr_file, pu_file):
    return loadPrivate(pr_file), loadPublic(pu_file)

# Testing the message we want to go through
if __name__ == '__main__':
    pr, pu = generate_keys()
    print(pr)
    print(pu)
    
    message = b'this is a secret message' # b in front stands for bytes, cannot encrypt strings
    sig = sign(message, pr)   # private key to encrypt message
    print(sig)
    
    correct = verify(message, sig, pu)
    
    if correct:
        print("Success! Good sig")
    else:
        print("Error, Signature is bad")
        
# Try to be an attacking generating our own public and private key
    pr2, pu2 = generate_keys()
    sig2 = sign(message, pr2)
    
    correct = verify(message, sig2, pu) # attacker uses his signature, but my public key
    if correct:
        print("Error, bad signature checks out")
    else:
        print("Success, bad signature detected")
    

# Try to temper with the message
    badmessage = message + b'Q'
    correct = verify(badmessage, sig, pu) # attacker uses my signature, my public key, but bad message
    if correct:
        print("Error, bad message checks out")
    else:
        print("Success, bad message detected")

# Test saving and loading private keys
    savePrivate(pr2, "private.key")
    pr_load = loadPrivate("private.key")
    sig3 = sign(message, pr_load)
    correct = verify(message, sig3, pu2)
    if correct:
        print("Success, good loaded private key")
    else:
        print("Error, bad loaded private key")
    
# Test saving and loading public keys
    savePublic(pu2, "public.key")
    pu_load = loadPublic("public.key")
    correct = verify(message, sig3, pu_load)
    if correct:
        print("Success, good loaded public key")
    else:
        print("Error, bad loaded public key")
