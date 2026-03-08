import sys


registers = {
"x0":"00000","zero":"00000",
"x1":"00001","ra":"00001",
"x2":"00010","sp":"00010",
"x3":"00011","gp":"00011",
"x4":"00100","tp":"00100",
"x5":"00101","t0":"00101",
"x6":"00110","t1":"00110",
"x7":"00111","t2":"00111",
"x8":"01000","s0":"01000","fp":"01000",
"x9":"01001","s1":"01001",
"x10":"01010","a0":"01010",
"x11":"01011","a1":"01011",
"x12":"01100","a2":"01100",
"x13":"01101","a3":"01101",
"x14":"01110","a4":"01110",
"x15":"01111","a5":"01111",
"x16":"10000","a6":"10000",
"x17":"10001","a7":"10001",
"x18":"10010","s2":"10010",
"x19":"10011","s3":"10011",
"x20":"10100","s4":"10100",
"x21":"10101","s5":"10101",
"x22":"10110","s6":"10110",
"x23":"10111","s7":"10111",
"x24":"11000","s8":"11000",
"x25":"11001","s9":"11001",
"x26":"11010","s10":"11010",
"x27":"11011","s11":"11011",
"x28":"11100","t3":"11100",
"x29":"11101","t4":"11101",
"x30":"11110","t5":"11110",
"x31":"11111","t6":"11111"
}
 

R_TYPE = {
"add":("0000000","000","0110011"),
"sub":("0100000","000","0110011"),
"sll":("0000000","001","0110011"),
"slt":("0000000","010","0110011"),
"sltu":("0000000","011","0110011"),
"xor":("0000000","100","0110011"),
"srl":("0000000","101","0110011"),
"or":("0000000","110","0110011"),
"and":("0000000","111","0110011")
}

I_TYPE = {
"addi":("000","0010011"),
"lw":("010","0000011"),
"sltiu":("011","0010011"),
"jalr":("000","1100111")
}

S_TYPE = {
"sw":("010","0100011")
}

B_TYPE = {
"beq":("000","1100011"),
"bne":("001","1100011"),
"blt":("100","1100011"),
"bge":("101","1100011"),
"bltu":("110","1100011"),
"bgeu":("111","1100011")
}

U_TYPE = {
"lui":"0110111",
"auipc":"0010111"
}

J_TYPE = {
"jal":"1101111"
}



def tobinary(v,bits):
    return format(v & ((1<<bits)-1), f'0{bits}b')

 

def collectlabel(lines):
    labels={}
    pc=0

    for line in lines:

        line=line.strip()
        if line=="":
            continue

        if ":" in line:
            label=line.split(":")[0]
            labels[label]=pc

            if line.split(":")[1].strip()=="":
                continue

        pc+=4

    return labels

 
def encodeR(op,rd,rs1,rs2):

    funct7,funct3,opcode=R_TYPE[op]

    return (
        funct7 +
        registers[rs2] +
        registers[rs1] +
        funct3 +
        registers[rd] +
        opcode
    )

 

def encodeI(op,rd,rs1,imm):

    funct3,opcode=I_TYPE[op]
    imm_bin=tobinary(int(imm),12)

    return (
        imm_bin +
        registers[rs1] +
        funct3 +
        registers[rd] +
        opcode
    )

 

def encodeLW(rd,offset,rs1):

    funct3,opcode=I_TYPE["lw"]
    imm_bin=tobinary(int(offset),12)

    return (
        imm_bin +
        registers[rs1] +
        funct3 +
        registers[rd] +
        opcode
    )

 

def encodeSW(rs2,offset,rs1):

    funct3,opcode=S_TYPE["sw"]

    imm=tobinary(int(offset),12)

    return (
        imm[:7] +
        registers[rs2] +
        registers[rs1] +
        funct3 +
        imm[7:] +
        opcode
    )

 

def encodeB(op,rs1,rs2,offset):

    funct3,opcode=B_TYPE[op]

    imm=tobinary(offset,13)

    return (
        imm[0] +
        imm[2:8] +
        registers[rs2] +
        registers[rs1] +
        funct3 +
        imm[8:12] +
        imm[1] +
        opcode
    )

 

def encodeU(op,rd,imm):

    opcode=U_TYPE[op]

    imm_bin=tobinary(int(imm),20)

    return imm_bin + registers[rd] + opcode

 

def encodeJ(rd,offset):

    opcode=J_TYPE["jal"]

    imm=tobinary(offset,21)

    return (
        imm[0] +
        imm[10:20] +
        imm[9] +
        imm[1:9] +
        registers[rd] +
        opcode
    )

 

def assemble(input_file,output_file):

    with open(input_file) as f:
        lines=f.readlines()

    labels=collectlabel(lines)

    pc=0
    output=[]

    for line in lines:

        line=line.strip()

        if line=="":
            continue

        if ":" in line:
            line=line.split(":")[1].strip()
            if line=="":
                continue

        parts=line.replace(","," ").replace("("," ").replace(")"," ").split()

        op=parts[0]

        if op in R_TYPE:

            rd,rs1,rs2=parts[1],parts[2],parts[3]
            binary=encodeR(op,rd,rs1,rs2)

        elif op=="addi" or op=="sltiu":

            rd,rs1,imm=parts[1],parts[2],parts[3]
            binary=encodeI(op,rd,rs1,imm)

        elif op=="lw":

            rd,offset,rs1=parts[1],parts[2],parts[3]
            binary=encodeLW(rd,offset,rs1)

        elif op=="sw":

            rs2,offset,rs1=parts[1],parts[2],parts[3]
            binary=encodeSW(rs2,offset,rs1)

        elif op in B_TYPE:

            rs1,rs2,label=parts[1],parts[2],parts[3]

            offset=labels[label]-pc
            binary=encodeB(op,rs1,rs2,offset)

        elif op=="jal":

            rd,label=parts[1],parts[2]

            offset=labels[label]-pc
            binary=encodeJ(rd,offset)

        elif op=="jalr":

            rd,rs1,imm=parts[1],parts[2],parts[3]
            binary=encodeI(op,rd,rs1,imm)

        elif op in U_TYPE:

            rd,imm=parts[1],parts[2]
            binary=encodeU(op,rd,imm)

        else:
            raise Exception(f"Invalid instruction: {op}")

        output.append(binary)
        pc+=4

    with open(output_file,"w") as f:
        for inst in output:
            f.write(inst+"\n")

 
if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Usage: python assembler.py input.asm output.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    assemble(input_file, output_file)

Ṇ
