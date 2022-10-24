import sys
from copy import deepcopy
import enum
import random
import pygame

BASE_WIDTH  = 64
BASE_HEIGHT = 32
SCALE_FACTOR = 10

WINDOW_WIDTH  = BASE_WIDTH  * SCALE_FACTOR
WINDOW_HEIGHT = BASE_HEIGHT * SCALE_FACTOR

_KB = 1024
_4KB = 4 * _KB

main_memory = [0] * _4KB

pygame.init()

def empty_display(): # 64 pixels wide * 32 pixels tall
    res = []
    base = [False] * 64
    for x in range(32):
        res += [base[:]]
    return res

def safe_push(stack, x):
    copy = stack[:]
    copy.append(x)
    assert len(copy) <= 16
    return copy

def safe_pop(stack):
    assert len(stack) > 0
    copy = stack[:]
    return copy[:-1]

def top(stack):
    assert len(stack) > 0
    return stack[:][-1]

def empty_memory():
    return [0] * _4KB

def reg_index(reg):
    assert len(reg) == 1 and type(reg) == str
    REG = reg.upper()
    return "0123456789ABCDEF".find(REG)

def reg_value(state, reg):
    regs = state['regs']
    assert reg_index(reg) < len(regs)
    return regs[reg_index(reg)]

def set_reg(state, reg, value):
    new_state = state
    regs = new_state['regs']
    print("reg: {}, value: {}".format(reg, value))
    assert reg_index(reg) < len(regs)
    assert value < 2**15 and value >= -(2 ** 15)
    regs[reg_index(reg)] = value
    new_state['regs'] = regs
    return new_state

def memory_with_loaded_fonts(_mem):
    mem = _mem[:]
    assert len(mem) == 4096
    [
            (_0_start, _0_end),
            (_1_start, _1_end),
            (_2_start, _2_end),
            (_3_start, _3_end),
            (_4_start, _4_end),
            (_5_start, _5_end),
            (_6_start, _6_end),
            (_7_start, _7_end),
            (_8_start, _8_end),
            (_9_start, _9_end),
            (_A_start, _A_end),
            (_B_start, _B_end),
            (_C_start, _C_end),
            (_D_start, _D_end),
            (_E_start, _E_end),
            (_F_start, _F_end)
    ] = [(x, x + 5) for x in range(0x50, 0x9F, 5)[:16]]
    
    assert _0_start == 0x50 and _F_end == 0xA0

    _0 = [0xF0, 0x90, 0x90, 0x90, 0xF0]; mem[_0_start : _0_end] = _0
    _1 = [0x20, 0x60, 0x20, 0x20, 0x70]; mem[_1_start : _1_end] = _1
    _2 = [0xF0, 0x10, 0xF0, 0x80, 0xF0]; mem[_2_start : _2_end] = _2
    _3 = [0xF0, 0x10, 0xF0, 0x10, 0xF0]; mem[_3_start : _3_end] = _3
    _4 = [0x90, 0x90, 0xF0, 0x10, 0x10]; mem[_4_start : _4_end] = _4
    _5 = [0xF0, 0x80, 0xF0, 0x10, 0xF0]; mem[_5_start : _5_end] = _5
    _6 = [0xF0, 0x80, 0xF0, 0x90, 0xF0]; mem[_6_start : _6_end] = _6
    _7 = [0xF0, 0x10, 0x20, 0x40, 0x40]; mem[_7_start : _7_end] = _7
    _8 = [0xF0, 0x90, 0xF0, 0x90, 0xF0]; mem[_8_start : _8_end] = _8
    _9 = [0xF0, 0x90, 0xF0, 0x10, 0xF0]; mem[_9_start : _9_end] = _9
    _A = [0xF0, 0x90, 0xF0, 0x90, 0x90]; mem[_A_start : _A_end] = _A
    _B = [0xE0, 0x90, 0xE0, 0x90, 0xE0]; mem[_B_start : _B_end] = _B
    _C = [0xF0, 0x80, 0x80, 0x80, 0xF0]; mem[_C_start : _C_end] = _C
    _D = [0xE0, 0x90, 0x90, 0x90, 0xE0]; mem[_D_start : _D_end] = _D
    _E = [0xF0, 0x80, 0xE0, 0x80, 0xF0]; mem[_E_start : _E_end] = _E
    _F = [0xF0, 0x80, 0xF0, 0x80, 0x80]; mem[_F_start : _F_end] = _F

    assert len(mem) == 4096

    return mem

def memory_with_loaded_fonts_from_state(state):
    mem = state['memory'][:]
    return memory_with_loaded_fonts(mem)

def default_state():
    return {
        'is_running': True,
        'pc': 0x200, # program counter
        'index': 0,
        'sound_timer': 0,
        'delay_timer': 0,
        'memory': memory_with_loaded_fonts(empty_memory()),
        'display': empty_display(),
        'stack': [], # stack for subroutines
        'regs': [0] * 16,
        'keys': [False] * 16,
    }


def fetch_opcode(state):
    new_state = state
    pc  = state['pc']
    mem = state['memory']
    print("PC: {}".format(pc))
    op1, op2 = mem[pc], mem[pc + 1]
    new_state['pc'] = pc + 2
    return (op1 << 8 | op2, new_state)

( Nop
, ClearScreen
, Return
, Jump
, Call
, SkipCondEq
, SkipCondNEq
, SkipCondRegEq
, SkipCondRegNEq
, Set
, Add
, SetR
, BinOr
, BinAnd
, BinXor
, AddR
, Sub12
, Sub21
, ShiftL
, ShiftR
, SetIndex
, JumpOffset
, Random
, Display
, SkipIfPressed
, SkipIfNotPressed
, RegFromDelayTimer
, DelayTimerFromReg
, SoundTimerFromReg
, AddToIndex
, GetPressedValue
, FontCharacter
, HexToDecimalToIndex
, StoreRegs
, LoadRegs 
) = range(35)

def op_to_str(op):
    if op == Nop:                 return "Nop"
    if op == ClearScreen:         return "ClearScreen"
    if op == Return:              return "Return"
    if op == Jump:                return "Jump"
    if op == Call:                return "Call"
    if op == SkipCondEq:          return "SkipCondEq"
    if op == SkipCondNEq:         return "SkipCondNEq"
    if op == SkipCondRegEq:       return "SkipCondRegEq"
    if op == SkipCondRegNEq:      return "SkipCondRegNEq"
    if op == Set:                 return "Set"
    if op == Add:                 return "Add"
    if op == SetR:                return "SetR"
    if op == BinOr:               return "BinOr"
    if op == BinAnd:              return "BinAnd"
    if op == BinXor:              return "BinXor"
    if op == AddR:                return "AddR"
    if op == Sub12:               return "Sub12"
    if op == Sub21:               return "Sub21"
    if op == ShiftL:              return "ShiftL"
    if op == ShiftR:              return "ShiftR"
    if op == SetIndex:            return "SetIndex"
    if op == JumpOffset:          return "JumpOffset"
    if op == Random:              return "Random"
    if op == Display:             return "Display"
    if op == SkipIfPressed:       return "SkipIfPressed"
    if op == SkipIfNotPressed:    return "SkipIfNotPressed"
    if op == RegFromDelayTimer:   return "RegFromDelayTimer"
    if op == DelayTimerFromReg:   return "DelayTimerFromReg"
    if op == SoundTimerFromReg:   return "SoundTimerFromReg"
    if op == AddToIndex:          return "AddToIndex"
    if op == GetPressedValue:     return "GetPressedValue"
    if op == FontCharacter:       return "FontCharacter"
    if op == HexToDecimalToIndex: return "HexToDecimalToIndex"
    if op == StoreRegs:           return "StoreRegs"
    if op == LoadRegs:            return "LoadRegs"
    return "Undefined"

def instruction_to_str(x):
    res = str(tuple([op_to_str(x[0])] + list(x)[1:]))
    return res

def decode_opcode(opcode):
    assert opcode >= 0 and opcode < 2 ** 16

    def digit_to_reg(d):
        assert d >= 0 and d < 16
        return "0123456789ABCDEF"[d]

    def first_digit (opcode): return opcode >> 12
    def second_digit(opcode): return (opcode >> 8) & 15
    def third_digit (opcode): return (opcode >> 4) & 15
    def fourth_digit(opcode): return opcode & 15

    def last_three  (opcode): return opcode & ((1 << 12) - 1)
    def last_two    (opcode): return opcode & ((1 << 8) - 1)

    def opcode_in_hex(opcode):
        return "0x{}{}{}{}".format(
            digit_to_reg(first_digit (opcode)),
            digit_to_reg(second_digit(opcode)),
            digit_to_reg(third_digit (opcode)),
            digit_to_reg(fourth_digit(opcode))
        )

    fr_dg = first_digit(opcode)

    if opcode == 0x00E0:
        return (ClearScreen, )
    if opcode == 0x00EE:
        return (Return, )
    if fr_dg == 0x0:
        return (Nop, )
    if fr_dg == 0x1:
        return (Jump, last_three(opcode))
    if fr_dg == 0x2:
        return (Call, last_three(opcode))
    if fr_dg == 0x3:
        reg = digit_to_reg(second_digit(opcode))
        return (SkipCondEq, reg, last_two(opcode))
    if fr_dg == 0x4:
        reg = digit_to_reg(second_digit(opcode))
        return (SkipCondNEq, reg, last_two(opcode))
    if fr_dg == 0x5:
        reg1 = digit_to_reg(second_digit(opcode))
        reg2 = digit_to_reg(third_digit (opcode))
        return (SkipCondRegEq, reg1, reg2)
    if fr_dg == 0x9:
        reg1 = digit_to_reg(second_digit(opcode))
        reg2 = digit_to_reg(third_digit (opcode))
        return (SkipCondRegNEq, reg1, reg2)
    if fr_dg == 0x6:
        reg = digit_to_reg(second_digit(opcode))
        return (Set, reg, last_two(opcode))
    if fr_dg == 0x7:
        reg = digit_to_reg(second_digit(opcode))
        return (Add, reg, last_two(opcode))
    if fr_dg == 0x8:
        lst_dg = fourth_digit(opcode)

        reg1 = digit_to_reg(second_digit(opcode))
        reg2 = digit_to_reg(third_digit(opcode))

        if lst_dg == 0x0:
            return (SetR, reg1, reg2)
        if lst_dg == 0x1:
            return (BinOr, reg1, reg2)
        if lst_dg == 0x2:
            return (BinAnd, reg1, reg2)
        if lst_dg == 0x3:
            return (BinXor, reg1, reg2)
        if lst_dg == 0x4:
            return (AddR, reg1, reg2)
        if lst_dg == 0x5:
            return (Sub12, reg1, reg2)
        if lst_dg == 0x7:
            return (Sub21, reg1, reg2)
        if lst_dg == 0x6:
            return (ShiftL, reg1, reg2)
        if lst_dg == 0xE:
            return (ShiftR, reg1, reg2)

    if fr_dg == 0xA:
        return (SetIndex, last_three(opcode))
    if fr_dg == 0xB:
        return (JumpOffset, last_three(opcode))
    if fr_dg == 0xC:
        reg = digit_to_reg(second_digit(opcode))
        and_val = last_two(opcode)
        return (Random, reg, and_val)
    if fr_dg == 0xD:
        reg1 = digit_to_reg(second_digit(opcode))
        reg2 = digit_to_reg(third_digit(opcode))
        height = fourth_digit(opcode)
        return (Display, reg1, reg2, height)
    if fr_dg == 0xE and last_two(opcode) == 0x9E:
        reg = digit_to_reg(second_digit(opcode))
        return (SkipIfPressed, reg)
    if fr_dg == 0xE and last_two(opcode) == 0xA1:
        reg = digit_to_reg(second_digit(opcode))
        return (SkipIfNotPressed, reg)

    if fr_dg == 0xF:
        reg = digit_to_reg(second_digit(opcode))
        lst_dgs = last_two(opcode)

        if lst_dgs == 0x07:
            return (RegFromDelayTimer, reg)
        if lst_dgs == 0x15:
            return (DelayTimerFromReg, reg)
        if lst_dgs == 0x18:
            return (SoundTimerFromReg, reg)
        if lst_dgs == 0x1E:
            return (AddToIndex, reg)
        if lst_dgs == 0x0A:
            return (GetPressedValue, reg)
        if lst_dgs == 0x29:
            return (FontCharacter, reg)
        if lst_dgs == 0x33:
            return (HexToDecimalToIndex, reg)
        if lst_dgs == 0x55:
            return (StoreRegs, reg)
        if lst_dgs == 0x65:
            return (LoadRegs, reg)

    print("Unknown instruction! {}".format(opcode_in_hex(opcode)))
    assert False

def exec_instruction(state, instruction):
    new_state = state
    op = instruction[0]

    if op == ClearScreen:
        new_state['dipslay'] = empty_display()

    if op == Return:
        stack = new_state['stack']
        pc = top(stack)
        stack = safe_pop(stack)
        new_state['stack'] = stack
        new_state['pc']    = pc

    if op == Nop:
        pass

    if op == Jump:
        (_, new_pc) = instruction
        new_state['pc'] = new_pc

    if op == Call:
        (_, new_pc) = instruction
        stack = safe_push(new_state['stack'], new_state['pc'])
        new_state['pc'] = new_pc
        new_state['stack'] = stack

    if op == SkipCondEq:
        (_, reg, val) = instruction
        reg_val = reg_value(new_state, reg)
        if reg_val == val:
            new_state['pc'] = new_state['pc'] + 2

    if op == SkipCondNEq:
        (_, reg, val) = instruction
        reg_val = reg_value(new_state, reg)
        if reg_val != val:
            new_state['pc'] = new_state['pc'] + 2

    if op == SkipCondRegEq:
        (_, reg1, reg2) = instruction
        reg_val1 = reg_value(new_state, reg1)
        reg_val2 = reg_value(new_state, reg2)
        if reg_val1 == reg_val2:
            new_state['pc'] = new_state['pc'] + 2

    if op == SkipCondRegNEq:
        (_, reg1, reg2) = instruction
        reg_val1 = reg_value(new_state, reg1)
        reg_val2 = reg_value(new_state, reg2)
        if reg_val1 != reg_val2:
            new_state['pc'] = new_state['pc'] + 2

    if op == Set:
        (_, reg, val) = instruction
        new_state = set_reg(new_state, reg, val)

    if op == Add:
        (_, reg, val) = instruction
        reg_val = reg_value(new_state, reg) + val
        new_state = set_reg(new_state, reg, reg_val)

    if op == SetR:
        (_, reg1, reg2) = instruction
        reg_val2 = reg_value(new_state, reg2)
        new_state = set_reg(new_state, reg1, reg_val2)

    if op == BinOr:
        (_, reg1, reg2) = instruction
        reg_val1 = reg_value(new_state, reg1)
        reg_val2 = reg_value(new_state, reg2)
        new_val = reg_val1 | reg_val2
        new_state = set_reg(new_state, reg1, new_val)

    if op == BinAnd:
        (_, reg1, reg2) = instruction
        reg_val1 = reg_value(new_state, reg1)
        reg_val2 = reg_value(new_state, reg2)
        new_val = reg_val1 & reg_val2
        new_state = set_reg(new_state, reg1, new_val)

    if op == BinXor:
        (_, reg1, reg2) = instruction
        reg_val1 = reg_value(new_state, reg1)
        reg_val2 = reg_value(new_state, reg2)
        new_val = reg_val1 ^ reg_val2
        new_state = set_reg(new_state, reg1, new_val)

    if op == AddR:
        (_, reg1, reg2) = instruction
        reg_val1 = reg_value(new_state, reg1)
        reg_val2 = reg_value(new_state, reg2)
        new_val = reg_val1 + reg_val2
        new_state = set_reg(new_state, reg1, new_val)

    if op == Sub12:
        (_, reg1, reg2) = instruction
        reg_val1 = reg_value(new_state, reg1)
        reg_val2 = reg_value(new_state, reg2)
        new_val = reg_val1 - reg_val2
        new_state = set_reg(new_state, reg1, new_val)

    if op == Sub21:
        (_, reg1, reg2) = instruction
        reg_val1 = reg_value(new_state, reg1)
        reg_val2 = reg_value(new_state, reg2)
        new_val = reg_val2 - reg_val2
        new_state = set_reg(new_state, reg1, new_val)

    if op == ShiftL:
        (_, reg1, reg2) = instruction
        reg_val1 = reg_value(new_state, reg1)
        new_val = reg_val1 << 1
        shifted_out = reg_val1 & (1 << 15)
        new_state = set_reg(new_state, reg1, new_val)
        new_state = set_reg(new_state, "F", shifted_out)

    if op == ShiftR:
        (_, reg1, reg2) = instruction
        reg_val1 = reg_value(new_state, reg1)
        new_val = reg_val1 >> 1
        shifted_out = reg_val1 & 1
        new_state = set_reg(new_state, reg1, new_val)
        new_state = set_reg(new_state, "F", shifted_out)

    if op == SetIndex:
        (_, val) = instruction
        new_state['index'] = val

    if op == JumpOffset:
        # TODO Make configurable
        (_, val) = instruction
        reg_val0 = reg_val(new_state, "0")
        new_state['pc'] = val + reg_val0

    if op == Random:
        (_, reg, val) = instruction
        randval = random.randint(0,1000) & val
        new_state = set_reg(new_state, reg, randval)

    if op == Display:
        (_, rx, ry, h) = instruction
        x = reg_value(new_state, rx) & 63
        y = reg_value(new_state, ry) & 31

        set_vf = 0

        old_display = new_state['display']
        display = old_display[:]
        index   = new_state['index']
        memory  = new_state['memory']

        x_vals = range(x, min(x + 8, 64))
        y_vals = range(y, min(y + h, 32))

        for i, y in zip(range(h), y_vals):
            b = memory[index + i]
            for offset, x in zip(range(8), x_vals):
                if (b >> (7 - offset)) & 1 == 1:
                    if display[y][x] == True:
                        display[y][x] = False
                        set_vf = 1
                    else:
                        display[y][x] = True

        new_state['display'] = display
        new_state = set_reg(new_state, "F", set_vf)

    if op == SkipIfPressed:
        (_, reg) = instruction
        assert reg >= 0 and reg < 16
        reg_val = reg_value(new_state, reg)
        keys = new_state['keys']
        if keys[reg_val] == True:
            new_state['pc'] += 2

    if op == SkipIfNotPressed:
        (_, reg) = instruction
        assert reg >= 0 and reg < 16
        reg_val = reg_value(new_state, reg)
        keys = new_state['keys']
        if keys[reg_val] == False:
            new_state['pc'] += 2

    if op == RegFromDelayTimer:
        (_, reg) = instruction
        new_state = set_reg(new_state, reg, new_state['delay'])

    if op == DelayTimerFromReg:
        (_, reg) = instruction
        reg_val = reg_value(new_state, reg)
        new_state['delay'] = reg_val

    if op == SoundTimerFromReg:
        (_, reg) = instruction
        reg_val = reg_value(new_state, reg)
        new_state['sound'] = reg_val

    if op == AddToIndex:
        (_, reg) = instruction
        reg_val = reg_value(new_state, reg)
        new_state['index'] += reg_val

    if op == GetPressedValue:
        (_, reg) = instruction
        keys = new_state['keys']
        stored = False
        for i, x in enumerate(keys):
            if x == True:
                new_state = set_reg(new_state, reg, i)
                stored = True
                break

        if stored == False:
            new_state['pc'] -= 2

    if op == FontCharacter:
        (_, reg) = instruction
        reg_val = reg_value(new_state, reg)
        assert reg_val >= 0 and reg_val < 16
        new_state['index'] = reg_val * 5 + 0x50

    if op == HexToDecimalToIndex:
        (_, reg) = instruction
        reg_val = reg_value(new_state, reg)
        memory = new_state['memory']
        index  = new_state['index']
        memory[index + 0] = reg_val // 100
        memory[index + 1] = (reg_val // 10) % 10
        memory[index + 2] = reg_val % 10
        new_state['memory'] = memory

    if op == StoreRegs:
        (_, reg) = instruction
        regs = new_state['regs']
        memory = new_state['memory']
        index = new_state['index']
        end = reg_index(reg)
        regs = regs[:end + 1]
        for i, val in enumerate(regs):
            memory[index + i] = val
        new_state['memory'] = memory

    if op == LoadRegs:
        (_, reg) = instruction
        regs = new_state['regs']
        memory = new_state['memory']
        index = new_state['index']
        end = reg_index(reg)
        for i, val in enumerate(range(index, index + end + 1)):
            regs[i] = val
        new_state['regs'] = regs

    return new_state

def fetch_decode_exec(state):
    new_state = state
    (opcode, new_state) = fetch_opcode(state)
    instruction         = decode_opcode(opcode)
    #print("PC: {}, {}".format(new_state['pc'] - 2, instruction_to_str(instruction)))
    new_state           = exec_instruction(new_state, instruction)
    return new_state

def draw_to_terminal(state):
    display = state['display']
    res = '\n'.join([''.join(['  ' if x == False else '##' for x in line]) for line in display])
    print(res)
    return res

def draw_screen_impure(state, window):
    (screen, scale_factor) = window

    def color_is(val):
        if val == True: return (255, 255, 255) # White
        else:           return (  0,   0,   0) # Black

    display = state['display']
    for _y in range(len(display)):
        for _x in range(len(display[_y])):
            x_vals = range(_x * scale_factor, (_x + 1) * scale_factor)
            y_vals = range(_y * scale_factor, (_y + 1) * scale_factor)

            color = color_is(display[_y][_x])
            
            for x in x_vals:
                for y in y_vals:
                    screen.set_at((x, y), color)

    pygame.display.flip()

def get_pressed_keys(state, keymap, keys):
    new_state = state
    pressed_keys = [False] * 16
    for i, x in enumerate(keys):
        c = chr(i)
        if c in keymap.keys() and x == 1:
            pressed_keys[keymap[c]] = True
    new_state['keys'] = pressed_keys
    pygame.event.pump()
    return new_state

def tick(state, keymap, keys, window):
    new_state = state.copy()
    new_state = get_pressed_keys(new_state, keymap, keys)
    new_state = fetch_decode_exec(new_state)
    draw_screen_impure(new_state, window)
    return new_state

def load_rom(state, fname):
    new_state = state
    def read_rom(fname):
        with open(fname, "rb") as f:
            data = [x for x in f.read()]
        return data

    rom_data = read_rom(fname)
    memory = new_state['memory']
    memory = memory[0:0x200] + rom_data + [0] * (4096 - (len(rom_data) + 0x200))
    new_state['memory'] = memory
    return new_state

def default_keymap():
    return {'1': 0x1, '2': 0x2, '3': 0x3, '4': 0xc,
            'q': 0x4, 'w': 0x5, 'e': 0x6, 'r': 0xd,
            'a': 0x7, 's': 0x8, 'd': 0x9, 'f': 0xe,
            'z': 0xa, 'x': 0x0, 'c': 0xb, 'v': 0xf}

def load_keymap():
    # TODO Read from configuration file
    return default_keymap()

def main():
    args = sys.argv
    assert len(args) != 1
    rom_name = args[1]
    state = load_rom(default_state(), rom_name)
    keymap = load_keymap()
    
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    window = (screen, SCALE_FACTOR)

    while True:
        keys = pygame.key.get_pressed()
        state = tick(state, keymap, keys, window)

if __name__ == "__main__":
    main()
