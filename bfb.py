#!/usr/bin/python3
__author__ = 'Ákos Tóth'

import curses
import sys
import time
import random

if len(sys.argv) < 2 or len(sys.argv) > 3:
    print('Usage: ' + sys.argv[0] + ' <code file>')
    exit(1)
debug = 0
if len(sys.argv) == 3:
    if sys.argv[2] == 'debug':
        debug = 1
    elif sys.argv[2] == 'slow':
        debug = 2
    elif sys.argv[2] == 'veryslow':
        debug = 3

def pymain(stdscr):
    rand = random.Random()
    rand.seed()
    curses.curs_set(0)
    stdscr.nodelay(1)

    # Character set:
    # n increase ptr by 1
    # N increase ptr by 10
    # p decrease ptr by 1
    # P decrease ptr by 10
    # m increase *ptr by 1
    # M increase *ptr by 10
    # l decrease *ptr by 1
    # L decrease *ptr by 10
    # r load 0 into ptr
    # R load 0 into *ptr
    # & load 'a' into *ptr
    # x output *ptr to x coordinate
    # X output accumulator to x coordinate
    # y output *ptr to y coordinate
    # Y output accumulator to y coordinate
    # c clear screen
    # a output *ptr to accumulator
    # A output 0 to accumulator
    # + add *ptr to accumulator
    # * multiply *ptr to accumulator
    # % modulo accumulator by *ptr
    # / divide accumulator by *ptr (flooring)
    # - subtract *ptr from accumulator
    # ? read key into accumulator
    # . output ascii(accumulator) to screen location
    # Z load *ptr to ptr
    # z load accumulator to *ptr
    # [ begin loop
    # ] return to loop beginning
    # b break current loop unconditionally
    # ^ return from subroutine
    # q skip next instruction if accumulator does not equal *ptr
    # Q skip next instruction if accumulator equals *ptr
    # 0 to 9 subroutine id
    # { begin subroutine definition
    # } end subroutine definition
    # > push accumulator onto stack
    # < pop accumulator from stack
    # ) push program counter onto stack
    # ( pop program counter from stack
    # @ delay by 10ms
    # # ignore everything until the next newline
    # ! generate random number into accumulator
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
    subrpos = [0] * 10
    csubr = 0
    stack = []
    loops = []

    datastack = []

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
            elif currchar == 'y':
                y = vars[ptr]
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
                stdscr.addch(x, y, chr(acc))
            elif currchar == 'Z':
                ptr = vars[ptr]
            elif currchar == 'z':
                vars[ptr] = acc
            elif currchar == '[':
                loops.append(pos)
            elif currchar == ']':
                pos = loops[len(loops) - 1]
            elif currchar == 'b':
                while pos < len(inp) and inp[pos] != ']':
                    pos += 1
                loops.pop()
            elif currchar == '^':
                if len(stack):
                    pos = stack.pop()
                else:
                    prog_ended = True
            elif currchar == 'q':
                if vars[ptr] != acc:
                    pos += 1
            elif currchar == 'Q':
                if vars[ptr] == acc:
                    pos += 1
            elif currchar in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                id = ord(currchar) - ord('0')
                stack.append(pos)
                pos = subrpos[id]
            elif currchar == '{':
                subrpos[csubr] = pos
                csubr += 1
                while pos < len(inp) and inp[pos] != '}':
                    pos += 1
            elif currchar == '}':
                if len(stack):
                    pos = stack.pop()
                else:
                    prog_ended = True
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
            elif currchar == '#':
                while pos < len(inp) and inp[pos] != "\n":
                    pos += 1
            elif currchar == '!':
                acc = rand.randint(0, 65535)

            pos += 1
            stdscr.refresh()
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

                stdscr.addstr(22, 0, "                                                            ")
                stdscr.addstr(23, 0, "                                                            ")
                stdscr.addstr(22, 0, "A {0}".format(acc))
                stdscr.addstr(22, 10, "L {0}".format(lastread))
                stdscr.addstr(22, 20, "X {0}".format(x))
                stdscr.addstr(22, 30, "> {0}".format(pos))
                stdscr.addstr(22, 50, "S {0}".format(len(datastack)))
                stdscr.addstr(23, 0, "P {0}".format(ptr))
                stdscr.addstr(23, 10, "V {0}".format(vars[ptr]))
                stdscr.addstr(23, 20, "Y {0}".format(y))
                stdscr.addstr(23, 30, "C {0}".format(currchar))
                if pos < len(inp):
                    stdscr.addstr(23, 40, "N {0}".format(inp[pos]))
                else:
                    stdscr.addstr(23, 40, "END".format(inp[pos]))
                if len(datastack):
                    stdscr.addstr(23, 50, "T {0}".format(datastack[len(datastack) - 1]))
                else:
                    stdscr.addstr(23, 50, "T ---")

                if debug == 1:
                    stdscr.nodelay(0)
                    stdscr.getch()
                    stdscr.nodelay(1)
                    time.sleep(0.3)
                elif debug == 2:
                    time.sleep(0.1)
                elif debug == 3:
                    time.sleep(1)
    except:
        curses.nocbreak()
        curses.echo()
        print("Error occurred: ", sys.exc_info()[0], file=sys.stderr)
        print("Accumulator: ", acc, file=sys.stderr)
        print("X: ", x, file=sys.stderr)
        print("Y: ", y, file=sys.stderr)
        print("Pointer: ", ptr, file=sys.stderr)
        print("Memory current: ", vars[ptr], file=sys.stderr)
        raise

curses.wrapper(pymain)
exit(0)