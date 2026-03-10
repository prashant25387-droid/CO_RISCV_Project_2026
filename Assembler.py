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

R = {
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

I = {
"addi":("000","0010011"),
"lw":("010","0000011"),
"sltiu":("011","0010011"),
"jalr":("000","1100111")
}

S = {"sw":("010","0100011")}

B = {
"beq":("000","1100011"),
"bne":("001","1100011"),
"blt":("100","1100011"),
"bge":("101","1100011"),
"bltu":("110","1100011"),
"bgeu":("111","1100011")
}

U = {
"lui":"0110111",
"auipc":"0010111"
}

J = {"jal":"1101111"}

def tobinary(v,bits):
    return format(int(v) & ((1<<bits)-1), f'0{bits}b')


def encodeR(op,rd,rs1,rs2):
    f7,f3,opc = R[op]
    return f7 + registers[rs2] + registers[rs1] + f3 + registers[rd] + opc


def encodeI(op,rd,rs1,imm):
    f3,opc = I[op]
    return tobinary(imm,12) + registers[rs1] + f3 + registers[rd] + opc


def encodeS(rs2,rs1,imm):
    f3,opc = S["sw"]
    imm = tobinary(imm,12)
    return imm[:7] + registers[rs2] + registers[rs1] + f3 + imm[7:] + opc


def encodeB(op,rs1,rs2,imm):
    f3,opc = B[op]
    imm = tobinary(imm,13)
    return imm[0] + imm[2:8] + registers[rs2] + registers[rs1] + f3 + imm[8:12] + imm[1] + opc


def encodeU(op,rd,imm):
    opc = U[op]
    return tobinary(imm,20) + registers[rd] + opc


def encodeJ(rd,imm):
    opc = J["jal"]
    imm = tobinary(imm,21)
    return imm[0] + imm[10:20] + imm[9] + imm[1:9] + registers[rd] + opc


def assemble(inp,out):

    with open(inp) as f:
        lines = f.readlines()

    pc = 0
    labels = {}

    for line in lines:

        line = line.split("#")[0].strip()

        if line == "":
            continue

        if ":" in line:
            label = line.split(":")[0].strip()
            labels[label] = pc

            rest = line.split(":",1)[1].strip()

            if rest == "":
                continue

        pc += 4

    pc = 0
    output = []
    halt = False

    for line in lines:

        line = line.split("#")[0].strip()

        if line == "":
            continue

        if ":" in line:
            line = line.split(":",1)[1].strip()
            if line == "":
                continue

        p = line.replace(","," ").replace("("," ").replace(")"," ").split()

        op = p[0]

        try:

            if op in R:
                output.append(encodeR(op,p[1],p[2],p[3]))

            elif op == "addi":
                output.append(encodeI(op,p[1],p[2],p[3]))

            elif op == "lw":
                output.append(encodeI(op,p[1],p[3],p[2]))

            elif op == "sw":
                output.append(encodeS(p[1],p[3],p[2]))

            elif op in B:

                if p[1]=="zero" and p[2]=="zero" and p[3]=="0":
                    halt = True

                offset = labels[p[3]]-pc if p[3] in labels else int(p[3])

                output.append(encodeB(op,p[1],p[2],offset))

            elif op in U:
                output.append(encodeU(op,p[1],p[2]))

            elif op == "jal":

                offset = labels[p[2]]-pc if p[2] in labels else int(p[2])

                output.append(encodeJ(p[1],offset))

            elif op == "jalr":
                output.append(encodeI(op,p[1],p[2],p[3]))

            else:
                print(f"Error on line {pc//4+1}: Unknown instruction")
                return

        except KeyError as e:
            print(f"Error on line {pc//4+1}: Invalid register {e}")
            return

        pc += 4


    if not halt:
        print("Error: Missing Virtual Halt instruction")


    with open(out,"w") as f:
        for i in output:
            f.write(i+"\n")


    print(f"Successfully assembled to {out}")

if __name__ == "__main__":

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    assemble(input_file, output_file)
