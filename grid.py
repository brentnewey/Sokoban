from random import randrange, choice
from math import pow, sqrt
from os.path import exists

from numpy import array, column_stack, row_stack, newaxis, vstack, hstack

DIMX = 79
DIMY = 23

def flatten(lst):
    for elem in lst:
        if type(elem) in (tuple, list):
            for i in flatten(elem):
                yield i
        else:
            yield elem

def distance(x1, y1, x2, y2):
    return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))

class Cell():
    def __init__(self, x, y, stuff, seen):
        self.mazed = False
        self.distance = 0
        self.visited = False
        self.current = False
        self.movechain = []
        self.seen = seen
        self.x = x
        self.y = y
        self.stuff = stuff
        self.floor = None
        self.changed = False

    def getdistance():
        return self.distance
    

class Grid():
    def __init__(self, dimx, dimy, omniscient, ioobj):
        self.dimx = dimx
        self.dimy = dimy
        self.omniscient = omniscient
        self.ioobj = ioobj
        self.cells = array([[Cell(j, i, 'wall', self.omniscient) for i in range(0, dimy)] for
                            j in range(0, dimx)])
        self.free = False
        self.sightradius = 10
        self.elephant = False
        self.emptychar = '.'
        self.movehistory = []
        self.moveindex = -1
        self.levelname = None
        self.levelset = 'm1'
        self.secs = None

    def adjacentoffset(self, room, x, y):
        if 0 <= room.x + x < self.dimx and 0 <= room.y + y < self.dimy:
            return self.cells[room.x + x, room.y + y]

    def adjacentwall(self, room, x, y):
        offcell = self.adjacentoffset(room, x, y)
        return offcell if offcell and offcell.stuff == 'wall' else None

    def adjacentorempty(self, room, x, y):
        if (room.x + x) < 0 or (room.y + y) < 0:
            return 1
        if (room.x + x) >= self.dimx or (room.y + y) >= self.dimy:
            return 1
        offcell = self.adjacentoffset(room, x, y)
        return offcell if offcell and offcell.stuff in ['wall', 'space'] and offcell.seen else None

    def adjacentseenwall(self, room, x, y):
        offcell = self.adjacentoffset(room, x, y)
        return offcell if offcell and offcell.stuff == 'wall' and offcell.seen else None

    def alladjacent(self, room, adjdef, key):
        retrooms = [self.adjacentoffset(room, c[0], c[1]) for c in adjdef]
        return filter(key, retrooms)

    def adjacentunmazed(self, room):
        return self.alladjacent(room, [[0, -2], [0, 2], [-2, 0], [2, 0]],
                                lambda r: r and not r.mazed)

    def adjacentrooms(self, room):
        return self.alladjacent(room, [[0, -1], [0, 1], [-1, 0], [1, 0]],
                                lambda r: r and not r.stuff)

    def adjacentfloors(self, room):
        return self.alladjacent(room, [[0, -1], [0, 1], [-1, 0], [1, 0]],
                                lambda r: r and r.stuff != 'wall')

    def breakwall(self, fromroom, toroom):
        self.cells[(fromroom.x + toroom.x) / 2,
                   (fromroom.y + toroom.y) / 2].stuff = None

    def stackx(self, back=False):
        newx = len(self.cells[..., 0])
        col = array([Cell(0 if back else newx, c, 'wall', True) for
                     c in range(0, len(self.cells[0, ...]))])
        if back:
            for cell in self.cells.flat:
                cell.x += 1
            self.cells = vstack((col[newaxis], self.cells))
        else:
            self.cells = row_stack((self.cells, col[newaxis]))
        self.dimx += 1

    def stacky(self, back=False):
        newy = len(self.cells[0, ...])
        col = array([[Cell(c, 0 if back else newy, 'wall', True)] for
                     c in range(0, len(self.cells[..., 0]))])
        if back:
            for cell in self.cells.flat:
                cell.y += 1
            self.cells = hstack((col, self.cells))
        else:
            self.cells = column_stack((self.cells, col))
        self.dimy += 1


    def mazeprep(self):
        for cell in self.cells.flat:
            if (cell.x % 2 and cell.y % 2 and cell.x < self.dimx - 1 and
                cell.y < self.dimy - 1):
                cell.stuff = None

    def mazify(self):
        self.mazeprep()
        roomchain = []
        room = choice(filter(lambda c: not c.stuff, self.cells.flat))
        room.mazed = True
        roomchain.append(room)
        while roomchain:
            pickrooms = self.adjacentunmazed(room)
            if pickrooms:
                pickroom = choice(pickrooms)
                self.breakwall(room, pickroom)
                pickroom.mazed = True
                roomchain.append(pickroom)
                room = pickroom
            else:
                room = roomchain.pop()

    def makeboard(self):
        for cell in self.cells.flat:
            cell.stuff = None
        for cell in self.getsides():
            cell.stuff = 'wall'

    def getsides(self):
        sides = [[0, Ellipsis, 1, 0], [self.dimx - 1, Ellipsis, -1, 0],
                 [Ellipsis, 0, 0, 1], [Ellipsis, self.dimy - 1, 0, -1]]
        sidecells = [[c for c in self.cells[s[0], s[1]] if
                      not self.adjacentoffset(c, s[2], s[3]).stuff] for
                     s in sides]
        return list(flatten(sidecells))

    def getsidewalls(self):
        sides = [[0, Ellipsis, 1, 0], [self.dimx - 1, Ellipsis, -1, 0],
                 [Ellipsis, 0, 0, 1], [Ellipsis, self.dimy - 1, 0, -1]]
        sidecells = [[c for c in self.cells[s[0], s[1]]] for
                     s in sides]
        return list(flatten(sidecells))

    def makeexit(self):
        deadcell = choice(self.getsides())
        deadcell.stuff = None
        return deadcell

    def playerroom(self):
        prooms = [c for c in self.cells.flat if c.stuff == 'player']
        if prooms:
            return prooms[0]

    def pgrid(self):
        changed = [c for c in self.cells.flat if c.changed]
        self.ioobj.pgrid(self.cells, self.adjacentorempty, self.elephant, changed)
        for cell in self.cells.flat:
            cell.changed = False

    def initlevel(self):
        self.ioobj.initlevel(self.cells)

    def ptitle(self):
        self.ioobj.ptitle(self.level, self.levelname)

    def placeplayer(self):
        room = choice([c for c in self.cells.flat if not c.stuff])
        room.stuff = 'player'
        return room

    def undomove(self):
        if self.moveindex == -1:
            return
        proom = self.playerroom()
        move = self.movehistory[self.moveindex]

        undo = [0 - move[1], 0 - move[2]]
        self.moveplayer(proom.x + undo[0], proom.y + undo[1], record=False, reset=False)
        if move[0] == 'block':
            broom = self.cells[proom.x + move[1], proom.y + move[2]]
            self.moveblock(broom, proom.x, proom.y)
            broom.changed = True
        self.moveindex -= 1

    def redomove(self):
        if self.moveindex == len(self.movehistory) - 1:
            return
        proom = self.playerroom()
        move = self.movehistory[self.moveindex + 1]
        self.moveplayer(proom.x + move[1], proom.y + move[2], record=False, reset=False)
        self.moveindex += 1
        

    def moveblock(self, blockcell, x, y):
        blockcell.stuff = None
        self.cells[x, y].stuff = 'block'

    def moveplayer(self, x, y, record=True, reset=True):
        if reset and self.moveindex < len(self.movehistory) - 1:
            while len(self.movehistory) > self.moveindex + 1:
                self.movehistory.pop(len(self.movehistory) - 1)
            
        proom = self.playerroom()
        offsetx = x - proom.x
        offsety = y - proom.y
        if offsetx and offsety:
            if self.cells[proom.x + offsetx, proom.y + offsety].stuff or (self.cells[proom.x, proom.y + offsety].stuff and self.cells[proom.x + offsetx, proom.y].stuff):
                return False


        if self.cells[x, y].stuff in ['block']:
            if not self.cells[x + offsetx, y + offsety].stuff:
                self.cells[x + offsetx, y + offsety].stuff = 'block'
                self.cells[x + offsetx, y + offsety].changed = True
            else:
                return
            if record:
                self.movehistory.append(['block', offsetx, offsety])
                self.moveindex += 1
        else:
            if record:
                self.movehistory.append(['move', offsetx, offsety])
                self.moveindex += 1

        proom.changed = True
        proom.stuff = None
        self.cells[x, y].changed = True
        self.cells[x, y].stuff = 'player'


    def finalmove(self):
        self.free = True

    def victory(self):
        targets = [c for c in self.cells.flat if c.floor == 'target']
        blocks = [c for c in self.cells.flat if c.stuff == 'block']
        isvictory = True
        for t in targets:
            if t not in blocks:
                isvictory = False
                break
        if isvictory:
            self.free = True

    def save(self, setname):
        setname = 'levels/' + setname
        beforelines = []
        afterlines = []
        if exists(setname):
            setfile = open(setname, 'r')

            line = setfile.readline()
            while line:
                if line[0:len(str(self.level)) + 2] == '; %d' % self.level:
                    break
                beforelines.append(line)
                line = setfile.readline()

            dowrite = False
            while line:
                if line[0:len(str(self.level + 1)) + 2] == '; %d' % (self.level + 1):
                    dowrite = True
                    afterlines.append('\n')
                if dowrite:
                    afterlines.append(line)
                line = setfile.readline()
            setfile.close()
        setfile = open(setname, 'w')
        for line in beforelines:
            setfile.write(line)
        setfile.write('; %d\n' % self.level)
        if self.levelname:
            setfile.write("'%s'\n\n" % self.levelname)
        else:
            setfile.write("\n")
        for i in range(0, len(self.cells[0, ...])):
            for j in range(0, len(self.cells[..., 0])):
                if self.cells[j, i].stuff == 'player' and self.cells[j, i].floor == 'target':
                    setfile.write('+')
                elif self.cells[j, i].stuff == 'player':
                    setfile.write('@')
                elif self.cells[j, i].stuff == 'block' and self.cells[j, i].floor == 'target':
                    setfile.write('*')
                elif self.cells[j, i].stuff == 'block':
                    setfile.write('$')
                elif self.cells[j, i].floor == 'target':
                    setfile.write('.')
                elif self.cells[j, i].stuff == 'wall':
                    cell = self.cells[j, i]
                    writechar = ' '
                    for coord in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0),
                                  (-1, 1), (0, 1), (1, 1)):
                        if (cell.x + coord[0]) < 0 or (cell.y + coord[1]) < 0:
                            continue
                        if (cell.x + coord[0]) >= self.dimx or (cell.y + coord[1]) >= self.dimy:
                            continue
                        if self.cells[cell.x + coord[0], cell.y + coord[1]].stuff != 'wall':
                            writechar = '#'
                            break
                    setfile.write(writechar)
                else:
                    setfile.write(' ')
            setfile.write('\n')
        for line in afterlines:
            setfile.write(line)

    def loadlevel(self):
        for c in self.cells.flat:
            c.stuff = None
            c.floor = None
        self.levelname = None
        levels = open('levels/' + self.levelset)
        line = levels.readline()
        lineno = 1
        start = False
        y = 0
        maxx = 0
        minx = None
        fills = []
        while line:
            if start:
                x = 0
                if line[0:1] == "'":
                    self.levelname = line[1:-2]
                else:
                    linecounts = False
                    thismaxx = 0
                    thisminx = None
                    for c in line:
                        if c not in [' ', '\n'] and not linecounts:
                            linecounts = c
                            if c != ';':
                                thisminx = x
                        if c not in [' ', '\n'] and linecounts:
                            thismaxx = x
                        if c == '#':
                            fills.append([x, y, 'stuff', 'wall'])
                        if c in ['@', '+']:
                            fills.append([x, y, 'stuff', 'player'])
                        if c in ['$', '*']:
                            fills.append([x, y, 'stuff', 'block'])
                        if c in ['*', '.', '+']:
                            fills.append([x, y, 'floor', 'target'])
                        if c == ';':
                            line = False
                            break
                        x += 1
                    if thismaxx > maxx:
                        maxx = thismaxx
                    if minx == None or (thisminx != None and thisminx < minx):
                        minx = thisminx
                    if not line:
                        break
                    if linecounts:
                        y += 1
            if line[0:len(str(self.level)) + 2] == '; %d' % self.level:
                line = levels.readline()
                if line[0:1] == "'":
                    self.levelname = line[1:-2]
                lineno += 1
                start = True
            lineno += 1
            line = levels.readline()

        if not fills:
            return False
        if minx > 0:
            maxx -= minx
            for f in fills:
                f[0] -= minx
        maxx += 1
        self.cells = array([[Cell(j, i, None, self.omniscient) for i in range(0, y)] for
                            j in range(0, maxx)])
        for cell in self.cells.flat:
            cell.changed = True
        self.dimx = maxx
        self.dimy = y
        for fill in fills:
            self.cells[fill[0], fill[1]].__dict__.update({fill[2]: fill[3]})
        proom = self.playerroom()
        if proom:
            contigs = self.calculatecontig(proom)
            for cell in self.cells.flat:
                if not cell.stuff and cell not in contigs:
                    cell.stuff = 'space'
        return start
        
    def translatemove(self, input):
        proom = self.playerroom()
        offset = self.ioobj.translate(input)
        if not offset:
            return False
        target = self.adjacentoffset(proom, offset[0], offset[1])
        if target and target.stuff in [None, 'block']:
            self.moveplayer(proom.x + offset[0], proom.y + offset[1])
        if not target:
            self.free = True

    def fill(self, fillcell, object):
        if not (0 < fillcell.x < self.dimx - 1):
            return
        if not (0 < fillcell.y < self.dimy - 1):
            return
        if object == 'target':
            if fillcell.stuff in ['wall']:
                fillcell.stuff = None
            fillcell.floor = 'target'
        if object == 'player':
            proom = self.playerroom()
            if proom:
                proom.stuff = None
                proom.changed = True
        if not object or object == 'wall':
            fillcell.floor = None
        if object in [None, 'wall', 'player', 'block']:
            fillcell.stuff = object
        fillcell.changed = True
        for coord in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0),
                      (-1, 1), (0, 1), (1, 1)):
            x = fillcell.x + coord[0]
            y = fillcell.y + coord[1]
            if not (x < 0 or x >= self.dimx or y < 0 or y >= self.dimy):
                self.cells[x, y].changed = True
        

    def calculateroute(self, start, target):
        for cell in self.cells.flat:
            cell.distance = self.dimx * self.dimy
            cell.movechain = []
            cell.visited = False
            cell.current = False

        start.distance = 0
        start.current = True

        def getcurrent():
            return [c for c in self.cells.flat if c.current][0]

        def getshortest():
            unvisited = [c for c in self.cells.flat if
                         not c.visited and not c.stuff]
            if not unvisited:
                return False
            return min(unvisited, key=lambda c: c.distance)

        def upmove(move):
            move.distance = current.distance + 1
            move.movechain = current.movechain + [[move.x, move.y]]

        current = getcurrent()
        while current and current != target:
            moves = [m for m in self.adjacentrooms(current) if
                     not m.visited and m.distance > current.distance]
            map(upmove, moves)
            current.visited = True
            current = getshortest()
            if not current:
                break
#        breakprint(str([(cell.x, cell.y, cell.movechain) for cell in self.cells.flat if cell.movechain]))
        return target.movechain

    def calculatecontig(self, start):
        for cell in self.cells.flat:
            cell.distance = self.dimx * self.dimy
            cell.movechain = []
            cell.visited = False
            cell.current = False

        start.current = True

        def getshortest(contigcells):
            adjcells = set()
            for cell in contigcells:
                adjrooms = self.adjacentfloors(cell)
                for room in adjrooms:
                    if not room.visited:
                        adjcells.add(room)
            if not adjcells:
                return False
            return list(adjcells)[0]

        current = start
        contigcells = []
        while current:
            contigcells.append(current)
            current.visited = True
            current = getshortest(contigcells)
            if not current:
                break

        return contigcells

    def raytrace(self, fromx, fromy, tox, toy):
        denom = float(tox - fromx)
        slope = float(toy - fromy) / denom if denom else None
        retcells = []
        linecells = set()
        if slope:
            def yforx(x):
                return slope * (x - fromx) + fromy
            def xfory(y):
                return ((y - fromy) / slope) + fromx
        elif slope is None:
            def yforx(x):
                return None
            def xfory(y):
                return fromx
        elif slope == 0.0:
            def yforx(x):
                return fromy
            def xfory(y):
                return None
            
        for cell in [c for c in self.cells[..., 0] if
                     max(fromx, tox) >=
                     float(c.x) + 0.5 >= min(fromx, tox)]:
            y = yforx(float(cell.x) + 0.5)
            if y:
                linecells.add(self.cells[cell.x, int(y)])
        for cell in [c for c in self.cells[0, ...] if
                     max(fromy, toy) >=
                     float(c.y) + 0.5 >= min(fromy, toy)]:
            x = xfory(cell.y + 0.5)
            if x:
                linecells.add(self.cells[int(x), cell.y])
        linecells = list(linecells)

        def pdistance(l):
            return distance(fromx, fromy, l.x, l.y)

        if linecells:
            linecells.sort(key=pdistance)
            curcell = linecells.pop(0)
            while curcell:
                retcells.append(curcell)
                curcell = linecells.pop(0) if linecells and curcell.stuff != 'wall' else None

        return retcells

    def tracesides(self):
        proom = self.playerroom()
        sides = [c for c in self.cells.flat if distance(proom.x, proom.y, c.x, c.y) <= self.sightradius]

        sightrooms = set()
        traces = [self.raytrace(proom.x + 0.5, proom.y + 0.5, side.x + 0.5, side.y + 0.5) for side in sides]

        for trace in traces:
            for cell in trace:
                sightrooms.add(cell)
        return sightrooms

    def seerooms(self, rooms):
        if not (self.elephant or self.omniscient):
            for cell in self.cells.flat:
                cell.seen = False
        for room in rooms:
            room.seen = True
