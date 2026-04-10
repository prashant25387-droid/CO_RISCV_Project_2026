import sys

DATA_START=0x10000
STACK_BASE=0x00000100
STACK_TOP=0x0000017C
MAX_INSTRUCTIONS=100000

def bin32(x):
    return "0b"+format(x&0xFFFFFFFF,"032b")


def sign_extend(val,bits):
    if val&(1<<(bits-1)):
        val-=(1<<bits)
    return val


def to_signed(x):
    x&=0xFFFFFFFF
    return x if x<(1<<31) else x-(1<<32)



def load_program(file):
    mem={}
    pc=0
    with open(file,"r",encoding="utf-8",errors="ignore") as f:
        for line in f:
            line=line.strip()
            if line=="":
                continue
            if not all(c in "01" for c in line):
                continue
            mem[pc]=int(line,2)
            pc+=4
    return mem


    def valid_address(addr):
    if addr%4!=0:
        return False
    if STACK_BASE<=addr<=STACK_TOP:
        return True
    if DATA_START<=addr<DATA_START+128:
        return True
    return False



#simulator
def simulate(input_file,output_file):
    mem=load_program(input_file)
    reg=[0]*32
    reg[2]=STACK_TOP
    pc=0
    trace=[]
    error=False
    instruction_count=0

    while True:
        instruction_count+=1
        if instruction_count>MAX_INSTRUCTIONS:
            break

        current_pc=pc
        instr=mem.get(pc,0)
        opcode=instr&0x7F
        next_pc=pc+4

        if opcode==0b0110011:
            rd=(instr>>7)&0x1F
            rs1=(instr>>15)&0x1F
            rs2=(instr>>20)&0x1F
            funct3=(instr>>12)&0x7
            funct7=(instr>>25)&0x7F

            if funct3==0:
                if funct7==0:
                    reg[rd]=reg[rs1]+reg[rs2]
                else:
                    reg[rd]=reg[rs1]-reg[rs2]
            elif funct3==1:
                reg[rd]=reg[rs1]<<(reg[rs2]&31)
            elif funct3==2:
                reg[rd]=1 if to_signed(reg[rs1])<to_signed(reg[rs2]) else 0
            elif funct3==3:
                reg[rd]=1 if (reg[rs1]&0xFFFFFFFF)<(reg[rs2]&0xFFFFFFFF) else 0
            elif funct3==4:
                reg[rd]=reg[rs1]^reg[rs2]
            elif funct3==5:
                if funct7==0:
                    reg[rd]=(reg[rs1]&0xFFFFFFFF)>>(reg[rs2]&31)
                else:
                    reg[rd]=to_signed(reg[rs1])>>(reg[rs2]&31)
            elif funct3==6:
                reg[rd]=reg[rs1]|reg[rs2]
            elif funct3==7:
                reg[rd]=reg[rs1]&reg[rs2]

            reg[rd]&=0xFFFFFFFF

        
        
        #I Type(ALU)
        elif opcode==0b0010011:
            rd=(instr>>7)&0x1F
            rs1=(instr>>15)&0x1F
            funct3=(instr>>12)&0x7
            imm=sign_extend((instr>>20)&0xFFF,12)

            if funct3==0:
                reg[rd]=reg[rs1]+imm
            elif funct3==2:
                reg[rd]=1 if to_signed(reg[rs1])<imm else 0
            elif funct3==3:
                reg[rd]=1 if (reg[rs1]&0xFFFFFFFF)<(imm&0xFFFFFFFF) else 0
            elif funct3==4:
                reg[rd]=reg[rs1]^imm
            elif funct3==6:
                reg[rd]=reg[rs1]|imm
            elif funct3==7:
                reg[rd]=reg[rs1]&imm
            elif funct3==1:
                shamt=(instr>>20)&31
                reg[rd]=reg[rs1]<<shamt
            elif funct3==5:
                shamt=(instr>>20)&31
                funct7=(instr>>25)&0x7F
                if funct7==0:
                    reg[rd]=(reg[rs1]&0xFFFFFFFF)>>shamt
                else:
                    reg[rd]=to_signed(reg[rs1])>>shamt

            reg[rd]&=0xFFFFFFFF

        
        
        #load
        elif opcode==0b0000011:
            rd=(instr>>7)&0x1F
            rs1=(instr>>15)&0x1F
            funct3=(instr>>12)&0x7
            imm=sign_extend((instr >> 20) & 0xFFF, 12)
            addr=(reg[rs1]+imm)&0xFFFFFFFF

            if funct3!=2 or not valid_address(addr):
                print(f"Error at instruction {instruction_count}")
                return

            reg[rd]=mem.get(addr,0)&0xFFFFFFFF

        
        
        #store
        elif opcode==0b0100011:
            rs1=(instr>>15)&0x1F
            rs2=(instr>>20)&0x1F
            funct3=(instr>>12)&0x7
            imm=sign_extend(
                ((instr >> 25) << 5) | ((instr >> 7) & 0x1F), 12
            )
            addr=(reg[rs1]+imm)&0xFFFFFFFF

            if funct3!=2 or not valid_address(addr):
                print(f"Error at instruction {instruction_count}")
                return

            mem[addr]=reg[rs2]&0xFFFFFFFF

        
        
        #branch
        elif opcode==0b1100011:
            rs1=(instr>>15)&0x1F
            rs2=(instr>>20)&0x1F
            funct3=(instr>>12)&0x7
            imm=sign_extend(((instr>>31)&1)<<12|((instr>>7)&1)<<11|((instr>>25)&0x3F)<<5|((instr>>8)&0xF)<<1,13)

            
            #halt
            if funct3==0 and rs1==0 and rs2==0 and imm==0:
                reg[0]=0
                trace.append(bin32(current_pc)+" "+" ".join(bin32(reg[i]) for i in range(32)))
                break

            
            taken=False
            if funct3==0: taken=reg[rs1]==reg[rs2]
            elif funct3==1: taken=reg[rs1]!=reg[rs2]
            elif funct3==4: taken=to_signed(reg[rs1])<to_signed(reg[rs2])
            elif funct3==5: taken=to_signed(reg[rs1])>=to_signed(reg[rs2])
            elif funct3==6: taken=(reg[rs1]&0xFFFFFFFF)<(reg[rs2]&0xFFFFFFFF)
            elif funct3==7: taken=(reg[rs1]&0xFFFFFFFF)>=(reg[rs2]&0xFFFFFFFF)

            if taken:
                next_pc=current_pc+imm

        
        #jal
        elif opcode==0b1101111:
            rd=(instr>>7)&0x1F
            imm=sign_extend(((instr>>31)&1)<<20|((instr>>12)&0xFF)<<12|((instr>>20)&1)<<11|((instr>>21)&0x3FF)<<1,21)
            reg[rd]=(pc+4)&0xFFFFFFFF
            next_pc=(current_pc+imm)&0xFFFFFFFF
            reg[rd]&=0xFFFFFFFF

        
        #jalr
        elif opcode==0b1100111:
            rd=(instr>>7)&0x1F
            rs1=(instr>>15)&0x1F
            imm=sign_extend((instr >> 20) & 0xFFF, 12)
            tmp=(pc+4)&0xFFFFFFFF
            next_pc=((reg[rs1]+imm)&0xFFFFFFFF)&~1
            reg[rd]=tmp

        
        
        #LUI
        elif opcode==0b0110111:
            rd=(instr>>7)&0x1F
            imm=(instr>>12)&0xFFFFF
            reg[rd]=(imm<<12)&0xFFFFFFFF

        
        #AUIPC
        elif opcode==0b0010111:
            rd=(instr>>7)&0x1F
            imm=(instr>>12)&0xFFFFF
            reg[rd]=(current_pc+(imm<<12))&0xFFFFFFFF

        else:
            print(f"Error at instruction {instruction_count}")
            return

        pc=next_pc&0xFFFFFFFF
        reg[0]=0

        trace.append(bin32(pc)+" "+" ".join(bin32(reg[i]) for i in range(32)))

    with open(output_file,"w") as f:
        for i in range(len(trace)):
            f.write(trace[i])
            if i!=len(trace)-1:
                f.write("\n")

        if not error:
            for addr in range(DATA_START,DATA_START+128,4):
                f.write("\n")
                f.write("0x"+format(addr,"08X")+":"+bin32(mem.get(addr,0)))

if __name__=="__main__":
    simulate(sys.argv[1],sys.argv[2])
