import curses

class CursesIO:
    def __init__(self, lights=False):
        self.stdscr = curses.initscr()
        self.walls = {'0000': curses.ACS_HLINE, '0001': curses.ACS_HLINE,
                      '0010': curses.ACS_HLINE, '0100': curses.ACS_VLINE,
                      '1000': curses.ACS_VLINE, '0011': curses.ACS_HLINE,
                      '0101': curses.ACS_ULCORNER, '0110': curses.ACS_URCORNER,
                      '1001': curses.ACS_LLCORNER, '1010': curses.ACS_LRCORNER,
                      '1100': curses.ACS_VLINE, '0111': curses.ACS_TTEE,
                      '1011': curses.ACS_BTEE, '1101': curses.ACS_LTEE,
                      '1110': curses.ACS_RTEE, '1111': curses.ACS_PLUS}
        self.moves = {curses.KEY_UP: [0, -1], curses.KEY_DOWN: [0, 1],
                      curses.KEY_RIGHT: [1, 0], curses.KEY_LEFT: [-1, 0],
                      104: [-1, 0], 106: [0, 1], 107: [0, -1], 108: [1, 0],
                      121: [-1, -1], 117: [1, -1], 98: [-1, 1], 110: [1, 1]}
        self.controls = {59: 'routeto', 10: 'confirm', 63: 'help',
                         114: 'reset', 113: 'quit', 122: 'undo',
                         120: 'redo', 115: 'solve'}


        curses.curs_set(0)
        curses.noecho()
        self.stdscr.keypad(1)
        self.emptychar = ' ' if not lights else '.'
        self.printoffset = [0, 1]
        self.titleoffset = [0, 0]

    def pgrid(self, cells, adjacentseenwall, elephant):
        for cell in cells.flat:
            if cell.stuff == 'wall' and cell.seen:
                tblr = ''.join(['1' if adjacentseenwall(cell, o[0], o[1])
                                else '0' for o in
                                [[0, -1], [0, 1], [-1, 0], [1, 0]]])
                chartop = self.walls[tblr]
            elif cell.stuff == 'player':
                if elephant:
                    chartop = 'E'
                else:
                    chartop = '@'
            elif cell.stuff == 'block':
                if cell.floor == 'target':
                    chartop = '*'
                else:
                    chartop = 'O'
            else:
                if cell.seen:
                    if cell.floor == 'target':
                        chartop = '.'
                    else:
                        chartop = self.emptychar
                else:
                    if cell.floor == 'target':
                        chartop = '.'
                    else:
                        chartop = ' '
            plocx = cell.x + self.printoffset[0]
            plocy = cell.y + self.printoffset[1]
            if 0 <= plocx < 80 and 0 <= plocy < 24:
                self.pchar(cell.x + self.printoffset[0], cell.y + self.printoffset[1], chartop)

    def getmove(self):
        return self.stdscr.getch()

    def pchar(self, x, y, char):
        self.stdscr.addch(y, x, char)

    def ptitle(self, level, levelname):
        self.stdscr.addstr(self.titleoffset[0], self.titleoffset[1], ' ' * 80)
        self.stdscr.addstr(self.titleoffset[0], self.titleoffset[1],
                           'Sokoban - Level %d%s' % (level, (' - ' + levelname) if levelname else ''))

    def translate(self, input):
        if input not in self.moves:
            return False
        return self.moves[input]

    def initlevel(self, cells):
        return

    def translatecontrol(self, input):
        if input not in self.controls:
            return False
        return self.controls[input]

    def endio(self):
        curses.endwin()

    def selecttile(self, proom):
        coords = [proom.x + self.printoffset[0], proom.y + self.printoffset[1]]
        self.stdscr.move(coords[1], coords[0])
        curses.curs_set(1)
        cval = 0
        while cval not in [10, 59]:
            cval = self.stdscr.getch()
            if cval in self.moves:
                move = self.moves[cval]
                coords[0] += move[0]
                coords[1] += move[1]
                self.stdscr.move(coords[1], coords[0])
        curses.curs_set(0)
        coords[0] = coords[0] - self.printoffset[0]
        coords[1] = coords[1] - self.printoffset[1]
        return coords

    def refresh(self):
        self.stdscr.refresh()

    def clear(self):
        self.stdscr.clear()

    def printhelp(self, helpfile):
        line = helpfile.readline()
        lineno = 0
        while line:
            self.stdscr.addstr(lineno, 0, line)
            lineno += 1
            line = helpfile.readline()

    def anykey(self):
        self.stdscr.getch()
