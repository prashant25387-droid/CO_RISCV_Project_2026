import sys

DATA_START  = 0x10000
STACK_BASE  = 0x00000100
STACK_TOP   = 0x0000017C
MAX_INSTRUCTIONS = 100000

def bin32(x):
    return "0b" + format(x & 0xFFFFFFFF, "032b")

def sign_extend(val, bits):
    if val & (1 << (bits - 1)):
        val -= (1 << bits)
    return val

def signed(x):
    x &= 0xFFFFFFFF
    return x if x < (1 << 31) else x - (1 << 32)

def load_program(file):
    mem = {}
    pc = 0
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and all(c in "01" for c in line):
                mem[pc] = int(line, 2)
                pc += 4
    return mem

def valid_address(addr):
    if STACK_BASE <= addr <= STACK_TOP:
        return True
    if DATA_START <= addr < DATA_START + 128:
        return True
    return False

def simulate(input_file, output_file):
    instr_mem = load_program(input_file)
    data_mem  = {}

    reg = [0] * 32
    reg[2] = STACK_TOP

    pc = 0
    trace = []
    error = False
    error_msg = ""
    instruction_count = 0

    while True:
        instruction_count += 1
        if instruction_count > MAX_INSTRUCTIONS:
            error = True
            error_msg = "Infinite loop detected"
            break

        if pc not in instr_mem:
            error = True
            error_msg = f"Invalid PC access at 0x{pc:08X}"
            break

        current_pc = pc
        instr = instr_mem[pc]
        opcode = instr & 0x7F
        next_pc = pc + 4

        # R TYPE
        if opcode == 0b0110011:
            rd = (instr >> 7) & 0x1F
            rs1 = (instr >> 15) & 0x1F
            rs2 = (instr >> 20) & 0x1F
            funct3 = (instr >> 12) & 0x7
            funct7 = (instr >> 25) & 0x7F

            if funct3 == 0:
                reg[rd] = reg[rs1] + reg[rs2] if funct7 == 0 else reg[rs1] - reg[rs2]
            elif funct3 == 1:
                reg[rd] = reg[rs1] << (reg[rs2] & 31)
            elif funct3 == 2:
                reg[rd] = 1 if signed(reg[rs1]) < signed(reg[rs2]) else 0
            elif funct3 == 3:
                reg[rd] = 1 if reg[rs1] < reg[rs2] else 0
            elif funct3 == 4:
                reg[rd] = reg[rs1] ^ reg[rs2]
            elif funct3 == 5:
                if funct7 == 0:
                    reg[rd] = (reg[rs1] & 0xFFFFFFFF) >> (reg[rs2] & 31)
                else:
                    reg[rd] = signed(reg[rs1]) >> (reg[rs2] & 31)
            elif funct3 == 6:
                reg[rd] = reg[rs1] | reg[rs2]
            elif funct3 == 7:
                reg[rd] = reg[rs1] & reg[rs2]

            reg[rd] &= 0xFFFFFFFF

        # I TYPE 
        elif opcode == 0b0010011:
            rd = (instr >> 7) & 0x1F
            rs1 = (instr >> 15) & 0x1F
            funct3 = (instr >> 12) & 0x7
            imm = sign_extend((instr >> 20) & 0xFFF, 12)

            if funct3 == 0:
                reg[rd] = reg[rs1] + imm
            elif funct3 == 2:
                reg[rd] = 1 if signed(reg[rs1]) < imm else 0
            elif funct3 == 4:
                reg[rd] = reg[rs1] ^ imm
            elif funct3 == 6:
                reg[rd] = reg[rs1] | imm
            elif funct3 == 7:
                reg[rd] = reg[rs1] & imm

            reg[rd] &= 0xFFFFFFFF

        # LOAD
        elif opcode == 0b0000011:
            rd = (instr >> 7) & 0x1F
            rs1 = (instr >> 15) & 0x1F
            imm = sign_extend((instr >> 20) & 0xFFF, 12)
            addr = (reg[rs1] + imm) & 0xFFFFFFFF

            if addr % 4 != 0:
                error = True
                error_msg = f"Misaligned memory access at address 0x{addr:05x}"
                break

            if not valid_address(addr):
                error = True
                error_msg = f"Invalid memory address: 0x{addr:08X}"
                break

            reg[rd] = data_mem.get(addr, 0)

        # STORE
        elif opcode == 0b0100011:
            rs1 = (instr >> 15) & 0x1F
            rs2 = (instr >> 20) & 0x1F
            imm = sign_extend(((instr >> 25) << 5) | ((instr >> 7) & 0x1F), 12)
            addr = (reg[rs1] + imm) & 0xFFFFFFFF

            if addr % 4 != 0:
                error = True
                error_msg = f"Misaligned memory access at address 0x{addr:05x}"
                break

            if not valid_address(addr):
                error = True
                error_msg = f"Invalid store address: 0x{addr:08X}"
                break

            data_mem[addr] = reg[rs2] & 0xFFFFFFFF

        # BRANCH 
        elif opcode == 0b1100011:
            rs1 = (instr >> 15) & 0x1F
            rs2 = (instr >> 20) & 0x1F
            funct3 = (instr >> 12) & 0x7

            imm = sign_extend(
                ((instr >> 31) & 1) << 12
                | ((instr >> 7) & 1) << 11
                | ((instr >> 25) & 0x3F) << 5
                | ((instr >> 8) & 0xF) << 1,
                13,
            )

            if rs1 == 0 and rs2 == 0 and imm == 0:
                trace.append(
                    bin32(current_pc)
                    + " "
                    + " ".join(bin32(reg[i]) for i in range(32))
                )
                break

            if funct3 == 0 and reg[rs1] == reg[rs2]:
                next_pc = current_pc + imm
            elif funct3 == 1 and reg[rs1] != reg[rs2]:
                next_pc = current_pc + imm

        # JAL
        elif opcode == 0b1101111:
            rd = (instr >> 7) & 0x1F
            imm = sign_extend(
                ((instr >> 31) & 1) << 20
                | ((instr >> 12) & 0xFF) << 12
                | ((instr >> 20) & 1) << 11
                | ((instr >> 21) & 0x3FF) << 1,
                21,
            )

            reg[rd] = (pc + 4) & 0xFFFFFFFF
            next_pc = (current_pc + imm) & 0xFFFFFFFF

        # JALR 
        elif opcode == 0b1100111:
            rd  = (instr >> 7)  & 0x1F
            rs1 = (instr >> 15) & 0x1F
            imm = sign_extend((instr >> 20) & 0xFFF, 12)

            temp = (pc + 4) & 0xFFFFFFFF
            target = (reg[rs1] + imm) & 0xFFFFFFFF
            target = target & ~1

            reg[rd] = temp
            next_pc = target

        else:
            error = True
            error_msg = f"Invalid instruction at PC 0x{current_pc:08X}"
            break

        pc = next_pc & 0xFFFFFFFF
        reg[0] = 0

        trace.append(
            bin32(pc)
            + " "
            + " ".join(bin32(reg[i]) for i in range(32))
        )

    with open(output_file, "w") as f:
        if error:
            print("Error:", error_msg)
            f.write("Error: " + error_msg)
        else:
            for i in range(len(trace)):
                f.write(trace[i])
                if i != len(trace) - 1:
                    f.write("\n")

            for addr in range(DATA_START, DATA_START + 128, 4):
                f.write("\n")
                f.write(
                    "0x"
                    + format(addr, "08X")
                    + ":"
                    + bin32(data_mem.get(addr, 0))
                )

if __name__ == "__main__":
    simulate(sys.argv[1], sys.argv[2])
