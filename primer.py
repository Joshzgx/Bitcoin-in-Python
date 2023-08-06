#!/usr/bin/env python
# coding: utf-8

# In[14]:


#Function

def myfunc(int_in):
    return int_in / 5 * 100

# Classes collection together functions and data
# Can have different instances

class myclass:
    oneval = 17
    def div(self, int_in):
        return int_in / self.oneval
    
    def __init__(self, inval):
        self.oneval = inval
    
C = myclass(4)
B = myclass(10)

print(C.oneval)
print(C.div(34))
print(B.div(34))

