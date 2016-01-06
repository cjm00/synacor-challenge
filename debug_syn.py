import syn
import json


def register_format(value):
    if 0 <= value < 32768:
        return str(value) + "\n"
    elif 32768 <= value <= 32775:
        return "reg " + str(value - 32768) + "\n"

class DebugSyn(syn.Synacor):
    def disassemble(self, filename):
        self.debug_head = 0
        with open(filename, "w") as output:
            while self.debug_head < self.tape_len:
                a = self.tape[self.debug_head]
                if a in syn.Synacor.commands:
                    output.write(syn.Synacor.commands[a] + "\n")
                    if syn.Synacor.arg_len[a]:
                        for k in range(syn.Synacor.arg_len[a]):
                            self.debug_head += 1
                            output.write(register_format(self.tape[self.debug_head]))
                        #output.write("\n")
                        
                    else:
                        #output.write("\n")
                        pass
                else:
                    output.write(str(a) + "\n")
                self.debug_head += 1



    
if __name__ == "__main__":
    with open("challenge.bin", "rb") as data:
        challenge = data.read()

    syndebug = DebugSyn(challenge)
    with open("save1452022772", "rt") as data:
        save = json.load(data)
        syndebug.load(save)
    syndebug.disassemble("savegamedis.txt")
    