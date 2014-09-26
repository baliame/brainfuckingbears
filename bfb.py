#!/usr/bin/env python3
__author__ = 'Ákos Tóth'

import curses
import sys
import time
import random

if len(sys.argv) < 2 or len(sys.argv) > 3:
    print('Usage: ' + sys.argv[0] + ' <code file>')
    exit(1)
debug = 0
bp = -1
if len(sys.argv) == 3:
    if sys.argv[2] == 'debug':
        debug = 1
    elif sys.argv[2] == 'slow':
        debug = 2
    elif sys.argv[2] == 'veryslow':
        debug = 3
    else:
        bp = int(sys.argv[2])

def pymain(stdscr):
    global debug
    global bp
    dbgkey = 0
    rand = random.Random()
    rand.seed(time.time())
    curses.curs_set(0)
    stdscr.nodelay(1)

    # Character set:
    # 0 to 9 subroutine id
    # a output *ptr to accumulator
    # A output 0 to accumulator
    # b break current loop unconditionally
    # B continue current loop
    # c clear screen
    # d dump the top of the stack
    # D decrease accumulator
    # e push accumulator onto DEBUG STACK
    # E clear DEBUG STACK
    # i interrupt (exit) with exit code in accumulator
    # I increase accumulator
    # l decrease *ptr by 1
    # L decrease *ptr by 10
    # m increase *ptr by 1
    # M increase *ptr by 10
    # n increase ptr by 1
    # N increase ptr by 10
    # p decrease ptr by 1
    # P decrease ptr by 10
    # q skip next instruction if accumulator does not equal *ptr (CMP = 0) or swap (CMP = 1)
    # Q skip next instruction if accumulator equals *ptr (CMP = 0) or swap (CMP = 1)
    # r load 0 into ptr
    # R load 0 into *ptr
    # s skip next instruction if accumulator is not less than *ptr (CMP = 0) or swap (CMP = 1)
    # S skip next instruction if accumulator is less than *ptr (CMP = 0) or swap (CMP = 1)
    # t skip next instruction if accumulator is not greater than *ptr (CMP = 0) or swap (CMP = 1)
    # T skip next instruction if accumulator is greater than *ptr (CMP = 0) or swap (CMP = 1)
    # u skip next instruction if accumulator is not zero (regardless of CMP)
    # U skip next instruction if accumulator is zero (regardless of CMP)
    # v save *ptr to swap
    # V load *ptr from swap
    # w save accumulator to swap
    # W load accumulator from swap
    # x output *ptr to x coordinate
    # X output accumulator to x coordinate
    # y output *ptr to y coordinate
    # Y output accumulator to y coordinate
    # z load accumulator to *ptr
    # Z load *ptr to ptr
    # & load 'a' into *ptr
    # + add *ptr to accumulator
    # - subtract *ptr from accumulator
    # * multiply *ptr to accumulator
    # / divide accumulator by *ptr (flooring)
    # % modulo accumulator by *ptr
    # ? read key into accumulator
    # . output ascii(accumulator) to screen location

    # { begin subroutine definition
    # ^ return from subroutine
    # } end subroutine definition
    # $ skip next instruction

    # [ begin loop
    # ] return to loop beginning
    # > push accumulator onto stack
    # < pop accumulator from stack
    # ) push program counter onto stack
    # ( pop program counter from stack
    # ; push ptr onto stack
    # , pop ptr from stack
    # @ delay by 10ms
    # # ignore everything until the next newline - - - - do not use ] and } characters in comments
    # ! generate random number into accumulator
    # \ complement CMP flag (if set, compare with swap instead of *ptr)
    # | unset CMP flag
    # any other character is an instruction which is automatically skipped
    # do not use any invalid instructions after q or Q.

    inp = ""
    try:
        with open(sys.argv[1], "r") as f:
            inp = f.read()
    except:
        print("Cannot open file " + sys.argv[1] + ".")
        exit(2)
    pos = 0

    vars = [0] * 4096
    ptr = 0
    acc = 0
    x = 0
    y = 0
    swap = 0
    CMP = 0
    subrpos = [0] * 10
    csubr = 0
    stack = []
    loops = []

    datastack = []
    debugstack = []
    subrloops = []

    lastread = 0

    prog_ended = False
    try:
        while not prog_ended:
            if pos >= len(inp):
                break
            currchar = inp[pos]
            if currchar == 'm':
                vars[ptr] += 1
            elif currchar == 'M':
                vars[ptr] += 10
            elif currchar == 'l':
                vars[ptr] -= 1
            elif currchar == 'L':
                vars[ptr] -= 10
            elif currchar == 'p':
                ptr -= 1
                while ptr < 0:
                    ptr += 4096
            elif currchar == 'P':
                ptr -= 10
                while ptr < 0:
                    ptr += 4096
            elif currchar == 'n':
                ptr += 1
                while ptr > 4095:
                    ptr -= 4096
            elif currchar == 'N':
                ptr += 10
                while ptr > 4095:
                    ptr -= 4096
            elif currchar == 'r':
                ptr = 0
            elif currchar == 'R':
                vars[ptr] = 0
            elif currchar == '&':
                vars[ptr] = ord('a')
            elif currchar == 'x':
                x = vars[ptr]
                #stdscr.move(y, x)
            elif currchar == 'y':
                y = vars[ptr]
                #stdscr.move(y, x)
            elif currchar == 'X':
                x = acc
            elif currchar == 'Y':
                y = acc
            elif currchar == 'c':
                stdscr.clear()
            elif currchar == 'a':
                acc = vars[ptr]
            elif currchar == 'A':
                acc = 0
            elif currchar == '+':
                acc += vars[ptr]
            elif currchar == '*':
                acc *= vars[ptr]
            elif currchar == '/':
                if vars[ptr] == 0:
                    raise ValueError('Division by zero.')
                acc //= vars[ptr]
            elif currchar == '-':
                acc -= vars[ptr]
            elif currchar == '%':
                acc %= vars[ptr]
            elif currchar == '?':
                acc = stdscr.getch()
                lastread = acc
            elif currchar == '.':
                stdscr.addstr(y, x, chr(acc))
            elif currchar == 'Z':
                ptr = vars[ptr]
            elif currchar == 'z':
                vars[ptr] = acc
            elif currchar == '[':
                if len(stack):
                    srl = subrloops.pop()
                    srl += 1
                    subrloops.append(srl)
                loops.append(pos)
            elif currchar == ']':
                pos = loops[len(loops) - 1]
            elif currchar == 'b':
                pos += 1
                depth = 1
                while pos < len(inp) and depth > 0:
                    if inp[pos] == ']':
                        depth -= 1
                        if depth == 0:
                            break
                    elif inp[pos] == '[':
                        depth += 1
                    pos += 1
                if len(stack):
                    srl = subrloops.pop()
                    if srl > 0:
                        srl -= 1
                    else:
                        srl = 0
                    subrloops.append(srl)
                loops.pop()
            elif currchar == 'B':
                pos = loops[len(loops) - 1]
            elif currchar == '^':
                if len(stack):
                    pos = stack.pop()
                    srl = subrloops.pop()
                    for i in range(srl):
                        loops.pop()
                else:
                    prog_ended = True
            elif currchar == 's':
                if (not CMP and vars[ptr] <= acc) or (CMP and swap <= acc):
                    pos += 1
            elif currchar == 'S':
                if (not CMP and vars[ptr] > acc) or (CMP and swap > acc):
                    pos += 1
            elif currchar == 't':
                if (not CMP and vars[ptr] >= acc) or (CMP and swap >= acc):
                    pos += 1
            elif currchar == 'T':
                if (not CMP and vars[ptr] < acc) or (CMP and swap < acc):
                    pos += 1
            elif currchar == 'q':
                if (not CMP and vars[ptr] != acc) or (CMP and swap != acc):
                    pos += 1
            elif currchar == 'Q':
                if (not CMP and vars[ptr] == acc) or (CMP and swap == acc):
                    pos += 1
            elif currchar == 'u':
                if 0 != acc:
                    pos += 1
            elif currchar == 'U':
                if 0 == acc:
                    pos += 1
            elif currchar == '$':
                pos += 1
            elif currchar == 'v':
                swap = vars[ptr]
            elif currchar == 'V':
                vars[ptr] = swap
            elif currchar == 'w':
                swap = acc
            elif currchar == 'W':
                acc = swap
            elif currchar in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                id = ord(currchar) - ord('0')
                stack.append(pos)
                subrloops.append(0)
                pos = subrpos[id]
            elif currchar == '{':
                if csubr < 10:
                    subrpos[csubr] = pos
                    csubr += 1
                pos += 1
                depth = 1
                while pos < len(inp) and depth > 0:
                    if inp[pos] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    elif inp[pos] == '{':
                        depth += 1
                    pos += 1
            elif currchar == '}':
                if len(stack):
                    pos = stack.pop()
                    srl = subrloops.pop()
                    for i in range(srl):
                        loops.pop()
            elif currchar == '@':
                time.sleep(0.01)
            elif currchar == '>':
                datastack.append(acc)
            elif currchar == '<':
                if len(datastack) != 0:
                    acc = datastack.pop()
                else:
                    raise IndexError('Stack is empty.')
            elif currchar == ')':
                datastack.append(pos)
            elif currchar == '(':
                if len(datastack) != 0:
                    pos = datastack.pop()
                else:
                    raise IndexError('Stack is empty.')
            elif currchar == ';':
                datastack.append(ptr)
            elif currchar == ',':
                if len(datastack) != 0:
                    ptr = datastack.pop()
                else:
                    raise IndexError('Stack is empty.')
            elif currchar == '#':
                while pos < len(inp) and inp[pos] != "\n":
                    pos += 1
            elif currchar == '!':
                acc = rand.randint(0, 65535)
            elif currchar == '\\':
                if CMP:
                    CMP = False
                else:
                    CMP = True
            elif currchar == '|':
                CMP = False
            elif currchar == 'd':
                if len(datastack) != 0:
                    datastack.pop()
                else:
                    raise IndexError('Stack is empty.')
            elif currchar == 'D':
                acc -= 1
            elif currchar == 'I':
                acc += 1
            elif currchar == 'e':
                debugstack.append(acc)
            elif currchar == 'E':
                debugstack.clear()
            elif currchar == 'i':
                exit(acc)

            pos += 1
            stdscr.refresh()
            if pos == bp and bp >= 0:
                debug = 1
            if debug:
                # A: accumulator
                # L: last input from ?
                # X: X coordinate
                # Y: Y coordinate
                # P: mempointer
                # V: memvalue
                # >: program counter
                # C: last instruction
                # N: next instruction
                # S: stack size (stack pointer)
                # T: stack top
                # W: swap
                # CMP: CMP flag
                stdscr.addstr(22, 0, "                                                                               ")
                stdscr.addstr(23, 0, "                                                                               ")
                stdscr.addstr(22, 0, "A {0}".format(acc))
                stdscr.addstr(22, 10, "L {0}".format(lastread))
                stdscr.addstr(22, 20, "X {0}".format(x))
                stdscr.addstr(22, 30, "> {0}".format(pos))
                stdscr.addstr(22, 40, "W {0}".format(swap))
                stdscr.addstr(22, 50, "S {0}".format(len(datastack)))
                val = 0
                if CMP:
                    val = 1
                stdscr.addstr(22, 60, "CMP {0}".format(val))
                stdscr.addstr(23, 0, "P {0}".format(ptr))
                stdscr.addstr(23, 10, "V {0}".format(vars[ptr]))
                stdscr.addstr(23, 20, "Y {0}".format(y))
                stdscr.addstr(23, 30, "C {0}".format(currchar))
                if pos < len(inp):
                    stdscr.addstr(23, 40, "N {0}".format(inp[pos]))
                else:
                    stdscr.addstr(23, 40, "END")
                if len(datastack):
                    stdscr.addstr(23, 50, "T {0}".format(datastack[len(datastack) - 1]))
                else:
                    stdscr.addstr(23, 50, "T ---")
                stdscr.addstr(22, 70, "qQsStTuU".format(val))
                compdata = ""
                if (not CMP and vars[ptr] != acc) or (CMP and swap != acc):  # q
                    compdata += "1"
                else:
                    compdata += "0"
                if (not CMP and vars[ptr] == acc) or (CMP and swap == acc):  # Q
                    compdata += "1"
                else:
                    compdata += "0"
                if (not CMP and vars[ptr] <= acc) or (CMP and swap <= acc):  # s
                    compdata += "1"
                else:
                    compdata += "0"
                if (not CMP and vars[ptr] > acc) or (CMP and swap > acc):    # S
                    compdata += "1"
                else:
                    compdata += "0"
                if (not CMP and vars[ptr] >= acc) or (CMP and swap >= acc):  # t
                    compdata += "1"
                else:
                    compdata += "0"
                if (not CMP and vars[ptr] < acc) or (CMP and swap < acc):    # T
                    compdata += "1"
                else:
                    compdata += "0"
                if 0 != acc:                                                 # u
                    compdata += "1"
                else:
                    compdata += "0"
                if 0 == acc:                                                 # U
                    compdata += "1"
                else:
                    compdata += "0"
                stdscr.addstr(23, 70, compdata)

                if debug == 1:
                    stdscr.nodelay(0)
                    goodinp = False
                    while not goodinp:
                        stdscr.addstr(21, 0, "                                                                               ")
                        stdscr.addstr(21, 0, "s step, c continue, l slow, v veryslow, b breakpoint here ({0})  {1}".format(bp, dbgkey))
                        key = stdscr.getkey()
                        dbgkey = key
                        if key == 'b' or key == 'B':
                            bp = pos
                        if key == 'c' or key == 'C':
                            goodinp = True
                            debug = 0
                        if key == 's' or key == 'S':
                            goodinp = True
                            debug = 1
                        if key == 'l' or key == 'L':
                            goodinp = True
                            debug = 2
                        if key == 'v' or key == 'V':
                            goodinp = True
                            debug = 3
                    stdscr.nodelay(1)
                    time.sleep(0.3)
                elif debug == 2:
                    time.sleep(0.1)
                elif debug == 3:
                    time.sleep(1)
    except Exception as e:
        stdscr.addstr(0, 0, "Fatal error at pos {0} (char {1}, instruction {2})".format(pos, pos+1, inp[pos]))
        stdscr.addstr(1, 0, "Error type: {0}".format(type(e)))
        stdscr.addstr(2, 0, "ACC = {0}".format(acc))
        stdscr.addstr(3, 0, "PTR = {0}".format(ptr))
        stdscr.addstr(4, 0, "MEM = {0}".format(vars[ptr]))
        stdscr.addstr(5, 0, "SWP = {0}".format(swap))
        stdscr.addstr(6, 0, "X = {0}".format(x))
        stdscr.addstr(7, 0, "Y = {0}".format(y))
        stdscr.addstr(8, 0, "LASTIN = {0}".format(lastread))
        stdscr.addstr(9, 0, "STACKLEN = {0}".format(len(datastack)))
        stackall = ""
        while len(datastack):
            stackall += str(datastack.pop())
            stackall += " "
        stdscr.addstr(10, 0, "STACK: {0}".format(stackall))
        stdscr.addstr(11, 0, "DEBUG: {0}".format(debugstack))

        stdscr.nodelay(0)
        stdscr.getch()

        print("Error occurred: ", sys.exc_info()[0], file=sys.stderr)
        print("Accumulator: ", acc, file=sys.stderr)
        print("X: ", x, file=sys.stderr)
        print("Y: ", y, file=sys.stderr)
        print("Pointer: ", ptr, file=sys.stderr)
        print("Memory current: ", vars[ptr], file=sys.stderr)

        raise

curses.wrapper(pymain)
exit(0)
