#!/usr/bin/env python3
__author__ = 'Ákos Tóth'

import curses
import sys
import time
import random
import binhex

controlnames = [
"NUL", "SOH", "STX", "ETX", "EOT", "ENQ", "ACK", "BEL",
"BS",  "HT",  "LF",  "VT",  "FF",  "CR",  "SO",  "SI",
"DLE", "DC1", "DC2", "DC3", "DC4", "NAK", "SYN", "ETB",
"CAN", "EM",  "SUB", "ESC", "FS",  "GS",  "RS",  "US",
"SP"
]

if len(sys.argv) < 2:
    print('Usage: ' + sys.argv[0] + ' <code file> [debug|slow|veryslow] [track] [breakpoint line number]')
    exit(1)
debug = 0
track = 0
bp = -1
if len(sys.argv) >= 3:
    try:
        sys.argv.index('debug')
        debug = 1
    except:
        try:
            sys.argv.index('slow')
            debug = 2
        except:
            try:
                sys.argv.index('veryslow')
                debug = 3
            except:
                pass
    try:
        sys.argv.index('track')
        track = 1
    except:
        pass
    for i in range(2, len(sys.argv)):
        try:
            bp = int(sys.argv[2])
            break
        except:
            pass


def pymain(stdscr):
    global debug
    global bp
    global track
    curses.use_default_colors()
    evlog = []
    def eventlog():
        scrstate = ['']*24
        for i in range(24):
            scrstate[i] = stdscr.instr(i, 0, 79)
        memy = 0
        key = None
        filtered = evlog
        filter = None
        search = None
        wrapped = False
        badsearch = False
        dir = 'up'
        while key != 'r' and key != 'R':
            if key == 'w' or key == 'W':
                if memy > 0:
                    memy -= 1
            elif key == 's' or key == 'S':
                memy += 1
            elif key == 'h' or key == 'H':
                memy = 0
            elif key == 'e' or key == 'E':
                memy = max(0, len(filtered) - 21)
            elif key == 'c' or key == 'C':
                filtered = evlog
                filter = None
                memy = 1
            elif key == 'f' or key == 'F':
                stdscr.clear()
                stdscr.addstr(0, 0, 'Enter filter string: ')
                curses.echo()
                stdscr.move(1, 0)
                filter = stdscr.getstr().decode()
                curses.noecho()
                filtered = []
                for i in range(len(evlog)):
                    line = evlog[i]
                    if line.find(filter) != -1:
                        filtered.append(line + ' [in line {0}]'.format(i+1))
                memy = 0
            elif key == 'u' or key == 'U' or (dir == 'up' and search is not None and (key == 'k' or key == 'K')):
                if key == 'u' or key == 'U':
                    stdscr.clear()
                    stdscr.addstr(0, 0, 'Enter search string: ')
                    stdscr.move(1, 1)
                    curses.echo()
                    stdscr.move(1, 0)
                    search = stdscr.getstr().decode()
                    curses.noecho()
                    dir = 'up'
                    badsearch = False

                if not badsearch:
                    wrapped = False
                    found = False
                    for i in range(memy - 1, -1, -1):
                        if filtered[i].find(search) != -1:
                            memy = i
                            found = True
                            break
                    if not found:
                        wrapped = True
                        for i in range(len(filtered) - 1, memy, -1):
                            if filtered[i].find(search) != -1:
                                memy = i
                                found = True
                                break
                        if not found:
                            badsearch = True
            elif key == 'j' or key == 'J' or (dir == 'down' and search is not None and (key == 'k' or key == 'K')):
                if key == 'j' or key == 'J':
                    stdscr.clear()
                    stdscr.addstr(0, 0, 'Enter search string: ')
                    curses.echo()
                    stdscr.move(1, 0)
                    search = stdscr.getstr().decode()
                    curses.noecho()
                    dir = 'down'
                    badsearch = False

                if not badsearch:
                    wrapped = False
                    found = False
                    for i in range(memy + 1, len(filtered)):
                        if filtered[i].find(search) != -1:
                            memy = i
                            found = True
                            break
                    if not found:
                        wrapped = True
                        for i in range(0, memy):
                            if filtered[i].find(search) != -1:
                                memy = i
                                found = True
                                break
                        if not found:
                            badsearch = True
            elif key == 'g' or key == 'G':
                stdscr.clear()
                stdscr.addstr(0, 0, 'Enter search string: ')
                curses.echo()
                stdscr.move(1, 0)
                line = stdscr.getstr().decode()
                curses.noecho()
                try:
                    line = int(line)
                except:
                    pass
                if line > 0:
                    memy = line - 1
            stdscr.clear()
            if len(filtered) == 0:
                stdscr.addstr(0, 0, "Log is empty.")
            #stdscr.addstr(0, 0, "          +0        +1        +2        +3        +4        +5        +6       ")
            for i in range(21):
                dataid = memy + i
                if len(filtered) > dataid:
                    stdscr.addstr(i, 0, filtered[dataid])
            stdscr.addstr(21, 0, "w: up, s: down, h: home, e: end, filter [f: do, c: clear]")
            stdscr.addstr(22, 0, "g: go to line, search [u: up, j: down, k: again], r: return")
            filterstatus = "Unfiltered"
            if filter is not None:
                filterstatus = "Filter: {0}".format(filter)
            searchstatus = "No search"
            if search is not None:
                searchstatus = "Searched for '{0}' {1}wards".format(search, dir)
                if badsearch:
                    searchstatus += ", no results"
                elif wrapped:
                    searchstatus += ", wrapped around"
            stdscr.addstr(23, 0, "Line {0}; {1}; {2}".format(memy + 1, filterstatus, searchstatus))
            key = stdscr.getkey()
        for i in range(24):
            stdscr.addstr(i, 0, scrstate[i])

    def log(what):
        evlog.append(what + " (at pos {0})".format(pos))
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
    # f push flags onto stack
    # F pop flags from stack
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

    # ' set flag [acc % 10]
    # " clear flag [acc % 10]
    # = skip if flag [acc % 10] is set
    # ~ skip if flag [acc % 10] is not set

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
    # : break execution (enter debug screen)
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
    flags = [0] * 10

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
                if track:
                    log("x coordinate loaded with {0} from memory at {1}".format(x, ptr))
                #stdscr.move(y, x)
            elif currchar == 'y':
                y = vars[ptr]
                if track:
                    log("y coordinate loaded with {0} from memory at {1}".format(y, ptr))
                #stdscr.move(y, x)
            elif currchar == 'X':
                x = acc
                if track:
                    log("x coordinate loaded with {0} from accumulator".format(x))
            elif currchar == 'Y':
                y = acc
                if track:
                    log("y coordinate loaded with {0} from accumulator".format(y))
            elif currchar == 'c':
                stdscr.clear()
            elif currchar == 'a':
                acc = vars[ptr]
                if track:
                    log("accumulator loaded with {0} from memory at {1}".format(acc, ptr))
            elif currchar == 'A':
                acc = 0
                if track:
                    log("accumulator loaded with 0")
            elif currchar == '+':
                acc += vars[ptr]
                if track:
                    log("accumulator increased by {0} (={1}) from memory at {2}".format(vars[ptr], acc, ptr))
            elif currchar == '*':
                acc *= vars[ptr]
                if track:
                    log("accumulator multiplied by {0} (={1}) from memory at {2}".format(vars[ptr], acc, ptr))
            elif currchar == '/':
                if vars[ptr] == 0:
                    raise ValueError('Division by zero.')
                acc //= vars[ptr]
                if track:
                    log("accumulator divided by {0} (={1}) from memory at {2}".format(vars[ptr], acc, ptr))
            elif currchar == '-':
                acc -= vars[ptr]
                if track:
                    log("accumulator decreased by {0} (={1}) from memory at {2}".format(vars[ptr], acc, ptr))
            elif currchar == '%':
                if vars[ptr] == 0:
                    raise ValueError('Division by zero.')
                acc %= vars[ptr]
                if track:
                    log("accumulator modulated by {0} (={1}) from memory at {2}".format(vars[ptr], acc, ptr))
            elif currchar == '?':
                acc = stdscr.getch()
                lastread = acc
                if track:
                    if acc < 0 or acc > 255:
                        rd = 'INVALID'
                    else:
                        rd = chr(acc)
                    log("accumulator set to {0} ({1}) from input".format(acc, rd))
            elif currchar == '.':
                stdscr.addstr(y, x, chr(acc % 256))
                if acc > 255:
                    stdscr.chgat(y, x, 1, curses.A_UNDERLINE)
                    if acc > 511:
                        stdscr.chgat(y, x, 1, curses.A_BOLD)
                if track:
                    log("output {0} ({1}) from accumulator".format(acc, chr(acc)))
            elif currchar == 'Z':
                ptr = vars[ptr]
            elif currchar == 'z':
                vars[ptr] = acc
                if track:
                    log("wrote {0} to memory at {1}".format(acc, ptr))
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
                occurred = 0
                if (not CMP and vars[ptr] <= acc) or (CMP and swap <= acc):
                    pos += 1
                    occurred = 1
                if track:
                    if CMP:
                        log('comparison - (CMP=1 -> swap) {0} <= {1} (accumulator), result: {2}'.format(swap, acc, occurred))
                    else:
                        log('comparison - (CMP=0 -> mem) {0} <= {1} (accumulator), result: {2}'.format(vars[ptr], acc, occurred))
            elif currchar == 'S':
                occurred = 0
                if (not CMP and vars[ptr] > acc) or (CMP and swap > acc):
                    pos += 1
                    occurred = 1
                if track:
                    if CMP:
                        log('comparison - (CMP=1 -> swap) {0} > {1} (accumulator), result: {2}'.format(swap, acc, occurred))
                    else:
                        log('comparison - (CMP=0 -> mem) {0} > {1} (accumulator), result: {2}'.format(vars[ptr], acc, occurred))
            elif currchar == 't':
                occurred = 0
                if (not CMP and vars[ptr] >= acc) or (CMP and swap >= acc):
                    pos += 1
                    occurred = 1
                if track:
                    if CMP:
                        log('comparison - (CMP=1 -> swap) {0} >= {1} (accumulator), result: {2}'.format(swap, acc, occurred))
                    else:
                        log('comparison - (CMP=0 -> mem) {0} >= {1} (accumulator), result: {2}'.format(vars[ptr], acc, occurred))
            elif currchar == 'T':
                occurred = 0
                if (not CMP and vars[ptr] < acc) or (CMP and swap < acc):
                    pos += 1
                    occurred = 1
                if track:
                    if CMP:
                        log('comparison - (CMP=1 -> swap) {0} < {1} (accumulator), result: {2}'.format(swap, acc, occurred))
                    else:
                        log('comparison - (CMP=0 -> mem) {0} < {1} (accumulator), result: {2}'.format(vars[ptr], acc, occurred))
            elif currchar == 'q':
                occurred = 0
                if (not CMP and vars[ptr] != acc) or (CMP and swap != acc):
                    pos += 1
                    occurred = 1
                if track:
                    if CMP:
                        log('comparison - (CMP=1 -> swap) {0} != {1} (accumulator), result: {2}'.format(swap, acc, occurred))
                    else:
                        log('comparison - (CMP=0 -> mem) {0} != {1} (accumulator), result: {2}'.format(vars[ptr], acc, occurred))
            elif currchar == 'Q':
                occurred = 0
                if (not CMP and vars[ptr] == acc) or (CMP and swap == acc):
                    pos += 1
                    occurred = 1
                if track:
                    if CMP:
                        log('comparison - (CMP=1 -> swap) {0} == {1} (accumulator), result: {2}'.format(swap, acc, occurred))
                    else:
                        log('comparison - (CMP=0 -> mem) {0} == {1} (accumulator), result: {2}'.format(vars[ptr], acc, occurred))
            elif currchar == 'u':
                occurred = 0
                if 0 != acc:
                    pos += 1
                    occurred = 1
                if track:
                    log('comparison - (constant) 0 != {0} (accumulator), result: {1}'.format(acc, occurred))
            elif currchar == 'U':
                occurred = 0
                if 0 == acc:
                    pos += 1
                    occurred = 1
                if track:
                    log('comparison - (constant) 0 != {0} (accumulator), result: {1}'.format(acc, occurred))
            elif currchar == '$':
                pos += 1
            elif currchar == 'v':
                swap = vars[ptr]
                if track:
                    log('loading {0} into swap from memory at {1}'.format(swap, ptr))
            elif currchar == 'V':
                vars[ptr] = swap
                if track:
                    log('saving {0} from swap to memory at {1}'.format(swap, ptr))
            elif currchar == 'w':
                swap = acc
                if track:
                    log('loading {0} into swap from accumulator'.format(swap))
            elif currchar == 'W':
                acc = swap
                if track:
                    log('saving {0} from swap into accumulator'.format(swap))
            elif currchar in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                id = ord(currchar) - ord('0')
                stack.append(pos)
                subrloops.append(0)
                pos = subrpos[id]
                if track:
                    log('calling subroutine {0}'.format(currchar))
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
                if track:
                    log("stacked {0} from accumulator".format(acc))
            elif currchar == '<':
                if len(datastack) != 0:
                    acc = datastack.pop()
                else:
                    raise IndexError('Stack is empty.')
                if track:
                    log("destacked {0} to accumulator".format(acc))
            elif currchar == ')':
                datastack.append(pos)
                if track:
                    log("stacked {0} from program counter".format(pos))
            elif currchar == '(':
                if len(datastack) != 0:
                    pos = datastack.pop()
                else:
                    raise IndexError('Stack is empty.')
                if track:
                    log("destacked {0} to program counter".format(pos))
            elif currchar == ';':
                datastack.append(ptr)
                if track:
                    log("stacked {0} from pointer".format(ptr))
            elif currchar == ',':
                if len(datastack) != 0:
                    ptr = datastack.pop()
                else:
                    raise IndexError('Stack is empty.')
                if track:
                    log("destacked {0} to pointer".format(ptr))
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
                if track:
                    log("accumulator decreased by 1 (={0})".format(acc))
            elif currchar == 'I':
                acc += 1
                if track:
                    log("accumulator increased by 1 (={0})".format(acc))
            elif currchar == 'e':
                debugstack.append(acc)
            elif currchar == 'E':
                debugstack.clear()
            elif currchar == 'i':
                exit(acc)
            elif currchar == ':':
                debug = 1
            elif currchar == "'":
                fid = acc % 10
                flags[fid] = 1
                if track:
                    log("set flag {0} (acc={1})".format(fid, acc))
            elif currchar == '"':
                fid = acc % 10
                flags[fid] = 0
                if track:
                    log("cleared flag {0} (acc={1})".format(fid, acc))
            elif currchar == '=':
                occurred = 0
                fid = acc % 10
                if flags[fid]:
                    pos += 1
                    occurred = 1
                if track:
                    log("comparison: - flag {0} (acc={1}), result: {2}".format(fid, acc, occurred))
            elif currchar == '~':
                occurred = 0
                fid = acc % 10
                if not flags[fid]:
                    pos += 1
                    occurred = 1
                if track:
                    log("comparison - NOT flag {0} (acc={1}), result: {2}".format(fid, acc, occurred))
            elif currchar == 'f':
                flagint = 0
                for i in range(10):
                    flagint += (2 ** (9-i)) * flags[i]
                stack.append(flagint)
                if track:
                    log("stacked {0} from flags".format(flagint))
            elif currchar == 'F':
                if len(datastack) != 0:
                    flagint = datastack.pop()
                    for i in range(10):
                        if flagint & (2 ** (9-i)):
                            flags[i] = 1
                        else:
                            flags[i] = 0
                    if track:
                        log("destacked {0} to flags".format(flagint))
                else:
                    raise IndexError('Stack is empty.')
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
                scrdbs = [''] * 4
                for i in range(4):
                    scrdbs[i] = stdscr.instr(i + 20, 0, 79)
                stdscr.addstr(20, 0, "                                                                               ")
                stdscr.addstr(21, 0, "                                                                               ")
                stdscr.addstr(22, 0, "                                                                               ")
                stdscr.addstr(23, 0, "                                                                               ")
                flagstr = ''
                for i in range(10):
                    flagstr += str(flags[i]) + ' '
                stdscr.addstr(21, 0, "FLAGS: {0}".format(flagstr))
                colorchar = 7 + (acc % 10) * 2
                stdscr.chgat(21, colorchar, 1, curses.A_BLINK)
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
                        trackint = 0
                        if track:
                            trackint = 1
                        stdscr.addstr(20, 0, "s step, c cont, t track ({0}), l slow, e log, v vslow, b bp here ({1}), m mem  {2}".format(trackint, bp, dbgkey))
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
                        if key == 't' or key == 'T':
                            if track:
                                track = False
                            else:
                                track = True
                        if key == 'e' or key == 'E':
                            eventlog()
                        if key == 'm' or key == 'M':
                            scrstate = ['']*24
                            for i in range(24):
                                scrstate[i] = stdscr.instr(i, 0, 79)
                            memy = 0
                            mode = 'dec'
                            key = None
                            while key != 'r' and key != 'R':
                                if key == 'w' or key == 'W':
                                    if memy > 0:
                                        memy -= 1
                                elif key == 's' or key == 'S':
                                    memy += 1
                                elif key == 'm' or key == 'M':
                                    if mode == 'dec':
                                        mode = 'hex'
                                    elif mode == 'hex':
                                        mode = 'ascii-dec'
                                    elif mode == 'ascii-dec':
                                        mode = 'ascii-hex'
                                    elif mode == 'ascii-hex':
                                        mode = 'dec'
                                stdscr.clear()
                                stdscr.addstr(0, 0, "          +0        +1        +2        +3        +4        +5        +6       ")
                                for i in range(20):
                                    dataid = memy * 7 + i * 7
                                    stdscr.addstr(i+1, 0, "({0})".format(dataid))
                                    for j in range(7):
                                        if len(vars) > dataid + j:
                                            data = vars[dataid+j]
                                            if mode == 'hex':
                                                data = hex(data)
                                            if mode == 'ascii-dec':
                                                if data <= 255:
                                                    if data <= 32:
                                                        data = controlnames[data]
                                                    else:
                                                        data = chr(data)
                                            if mode == 'ascii-hex':
                                                if data <= 255:
                                                    if data <= 32:
                                                        data = controlnames[data]
                                                    else:
                                                        data = chr(data)
                                                else:
                                                    data = hex(data)
                                            stdscr.addstr(i+1, (j+1)*10, "{0}".format(data))
                                stdscr.addstr(22, 0, "w: up, s: down, r: return, m: mode ({0})".format(mode))
                                key = stdscr.getkey()
                            for i in range(24):
                                stdscr.addstr(i, 0, scrstate[i])
                    stdscr.nodelay(1)
                    for i in range(4):
                        stdscr.addstr(i + 20, 0, scrdbs[i])
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

        if track:
            eventlog()

        print("Error occurred: ", sys.exc_info()[0], file=sys.stderr)
        print("Accumulator: ", acc, file=sys.stderr)
        print("X: ", x, file=sys.stderr)
        print("Y: ", y, file=sys.stderr)
        print("Pointer: ", ptr, file=sys.stderr)
        print("Memory current: ", vars[ptr], file=sys.stderr)

        raise

curses.wrapper(pymain)
exit(0)
