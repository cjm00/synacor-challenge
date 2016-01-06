import array
import time
import json


class Synacor:
    commands = {0 : "halt",
                1 : "set",
                2 : "push",
                3 : "pop",
                4 : "op_eq",
                5 : "op_gt",
                6 : "jump",
                7 : "jumptest",
                8 : "jumpzero",
                9 : "add",
                10 : "mult",
                11 : "op_mod",
                12 : "op_and",
                13 : "op_or",
                14 : "op_not",
                15 : "rmem",
                16 : "wmem",
                17 : "op_call",
                18 : "op_ret",
                19 : "out",
                20 : "op_in",
                21 : "noop"
                }
                
    arg_len = { 0 : 0,
                1 : 2,
                2 : 1,
                3 : 1,
                4 : 3,
                5 : 3,
                6 : 1,
                7 : 2,
                8 : 2,
                9 : 3,
                10 : 3,
                11 : 3,
                12 : 3,
                13 : 3,
                14 : 2,
                15 : 2,
                16 : 2,
                17 : 1,
                18 : 0,
                19 : 1,
                20 : 1,
                21 : 0
                }
                
    def __init__(self, data):
        self.tape = array.array('H', data)
        self.tape_len = len(self.tape)
        self.head = 0
        self.registers = [0] * 8
        self.stack = list()
        self.user_input = list()
        self.changed_memory = []
        self.fun_calls = set()
        self.debug_head = 0
        
    def read(self, value, register=False):
        if register:
            if 0 <= value < 32768:
                return value
            elif 32768 <= value <= 32775:
                return value - 32768
            elif value > 32775:
                raise ValueError("Invalid Value!")
                
        if 0 <= value < 32768:
            return value
        elif 32768 <= value <= 32775:
            return self.registers[value - 32768]
        elif value > 32775:
            raise ValueError("Invalid Value!")
            
    def debug_read(self, value, register=False):
            if 0 <= value < 32768:
                return value
            elif 32768 <= value <= 32775:
                return chr(65 + value - 32768)
            
    def grab(self, quantity, register=False):
        if quantity == 0:
            return ""
        output = (self.read(self.tape[self.head + 1], register),)
        for k in range(2, quantity+1):
            output += (self.read(self.tape[self.head + k]),)
        return output
        
    def debug_grab(self, quantity, register=False):
        if quantity == 0:
            return ""
        output = (self.debug_read(self.tape[self.head + 1]),)
        for k in range(2, quantity+1):
            output += (self.debug_read(self.tape[self.head + k]),)
        return output
        
    def halt(self):
        print("Synacor program halted.")
        self.head = -1
    
    def set(self):
        a, b = self.grab(2, register=True)
        self.registers[a] = b
        self.head += 3
        
    def push(self):
        a, = self.grab(1)
        self.stack.append(a)
        self.head += 2
        
    def pop(self):
        a, = self.grab(1, register=True)
        self.registers[a] = self.stack.pop()
        self.head += 2
              
    def op_eq(self):
        a, b, c = self.grab(3, register=True)
        #print("op_eq:", a, b, c)
        self.registers[a] = 1 if b == c else 0
        self.head += 4
    
    def op_gt(self):
        a, b, c = self.grab(3, register=True)
        self.registers[a] = 1 if b > c else 0
        self.head += 4
        
    def jump(self):
        #print("jmp:", self.read(self.tape[self.head + 1]))
        self.head, = self.grab(1)
        
    def jumptest(self):
        #print("jt:", self.read(self.tape[self.head + 1]), self.read(self.tape[self.head + 2]))
        a, b = self.grab(2)
        if a:
            self.head = b
        else:
            self.head += 3
        
    def jumpzero(self):
        a, b = self.grab(2)
        if a == 0:
            self.head = b
        else:
            self.head += 3
            
    def add(self):
        a, b, c = self.grab(3, register=True)
        self.registers[a] = (b + c) % 2**15
        self.head += 4
        #print("add:", a, b, c, self.registers[a])
        
    def mult(self):
        a, b, c = self.grab(3, register=True)
        self.registers[a] = (b * c) % 2**15
        self.head += 4
        
    def op_mod(self):
        a, b, c = self.grab(3, register=True)
        self.registers[a] = b % c 
        self.head += 4
        
    def op_and(self):
        a, b, c = self.grab(3, register=True)
        self.registers[a] = b & c 
        self.head += 4
        
    def op_or(self):
        a, b, c = self.grab(3, register=True)
        self.registers[a] = b | c 
        self.head += 4
        
    def op_not(self):
        a, b = self.grab(2, register=True)
        self.registers[a] = (2**15 - 1) - b
        self.head += 3
        
    def rmem(self):
        a, b = self.grab(2, register=True)
        self.registers[a] = self.tape[b]
        self.head += 3
        
    def wmem(self):
        a, b = self.grab(2)
        self.tape[a] = b
        self.head += 3
        self.changed_memory.append((a, b))
        
    def op_call(self):
        a, = self.grab(1)
        self.stack.append(self.head+2)
        self.head = a
        self.fun_calls.add(a)
        
    def op_ret(self):
        self.head = self.stack.pop()
            
    def out(self):
        a, = self.grab(1)
        print(chr(a), sep='', end='', flush=True)
        self.head += 2
        
    def op_in(self):
        a, = self.grab(1, register=True)
        if self.user_input:
            c = self.user_input.pop()
            self.registers[a] = 10 if c == 13 else c
        else:
            b = input("Input: ")
            if '!' in b:
                b = self.override(b)
                          
            self.user_input = [ord(x) for x in b] + [10] # Manually append newline
            self.user_input = self.user_input[::-1]

            c = self.user_input.pop()
            self.registers[a] = 10 if c == 13 else c
                
        self.head += 2
        
    def noop(self):
        self.head += 1
        
    def override(self, cmds):
        while "!resume" != cmds:
            if cmds == "!save":
                self.save()
            elif cmds == "!dump":
                self.dump()
            elif cmds == "!mem":
                print(self.changed_memory)
            elif cmds == "!fun":
                print(self.fun_calls)
            elif cmds == "!fun clear":
                self.fun_calls = set()  
            elif "!debug" in cmds:
                a, b = cmds.split()
                self.debug_read(int(b))
            elif "!set" in cmds:
                _, a, b = cmds.split()
                self.override_set(int(a), int(b))
            cmds = input ("Override Input: ")
                
        out = input("Input: ")
        return out
        
    def override_set(self, a, b):
        self.registers[a] = b
        
    def dump(self):
        print(self.registers)
    
                     
    def BLARG(self):
        print("Not yet implemented!")
        print("Head position:", self.head)
        print("Tape value:", self.tape[self.head])
        self.head = -1
        
        
    def run(self):
        while 0 <= self.head < self.tape_len:
            getattr(self, Synacor.commands[self.read(self.tape[self.head])])()
    
    def debug_run(self):
        while 0 <= self.head < self.tape_len:
            print(Synacor.commands[self.read(self.tape[self.head])], 
                    *self.debug_grab(Synacor.arg_len[self.read(self.tape[self.head])])
                    )
            if not self.user_input:
                print("Done reading input~~~~~~~~~~~~")
            getattr(self, Synacor.commands[self.read(self.tape[self.head])])()
            input()
            
    def save(self):
        with open("save" + str(int(time.time())), "w") as savefile:
            save_dict = {}
            save_dict['tape'] = list(self.tape)
            save_dict['head'] = self.head
            save_dict['registers'] = self.registers
            save_dict['stack'] = self.stack
            save_dict['user_input'] = self.user_input
            save_dict['mem_history'] = self.changed_memory
            json.dump(save_dict, savefile)

    def load(self, save_dict):
        self.tape = save_dict['tape']
        self.tape_len = len(self.tape)
        self.head = save_dict['head']
        self.registers = save_dict['registers']
        self.stack = save_dict['stack']
        self.user_input = save_dict['user_input']
        #self.changed_memory = save_dict['mem_history']

if __name__ == "__main__":
    with open("challenge.bin", "rb") as data:
        challenge = data.read()

    syn = Synacor(challenge)
    with open("save1452022772", "rt") as data:
        save = json.load(data)
        syn.load(save)
    syn.debug_run()

