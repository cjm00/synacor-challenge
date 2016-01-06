import itertools as it

def magic_lock(args):
    return args[0] + args[1]*args[2]**2 + args[3]**3 - args[4]
    
def coins():
    c = [2,3,5,7,9]
    for x in it.permutations(c):
        if magic_lock(x) == 399:
            print(x)
        


    
