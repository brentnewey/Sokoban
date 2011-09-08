import time
from math import floor

import pygame
from pygame import display
from pygame.transform import rotate, scale
import numpy

from inputbox import InputBox, defaultbox

class PygameIO:
    def __init__(self, lights=False):
        pygame.init()

        di = display.Info()
        self.desksize = (di.current_w, di.current_h)

        surfaces = ('floor', 'wall', 'playerfloor', 'target', 'blocktarget',
                    'wallquarter', 'cornerquarter', 'jutquarter',
                    'emptyquarter', 'playertarget', 'blockfloor')

        sdict = dict((s + 'surface',
                      pygame.image.load('surfaces/%s.png' % s)) for s in
                     surfaces)

        self.__dict__.update(sdict)

        self.qs = {'000': (self.jutquartersurface, 0),
                   '001': (self.wallquartersurface, 90),
                   '010': (self.jutquartersurface, 0),
                   '100': (self.wallquartersurface, 0),
                   '011': (self.wallquartersurface, 90),
                   '101': (self.cornerquartersurface, 0),
                   '110': (self.wallquartersurface, 0),
                   '111': (self.emptyquartersurface, 0)}

        self.qfs = (((-1, 0), (-1, -1), (0, -1), 0, (0, 0)),
                    ((0, -1), (1, -1), (1, 0), 3, (0.5, 0)),
                    ((1, 0), (1, 1), (0, 1), 2, (0.5, 0.5)),
                    ((0, 1), (-1, 1), (-1, 0), 1, (0, 0.5)))

        self.sets([48, 48])
        self.tilex = 48
        self.tiley = 48
        self.renderx = 0
        self.rendery = 0
        self.rs = [0, 0]
        self.scalefactor = 1
        self.initdelay = 0.2
        self.delay = 0.05
        self.levelnamerect = None
        self.controlrects = []
        self.lastmoves = -1
        self.lastsecs = -1
        self.mstart = None

    def sets(self, size):
        self.ts = size
        self.hts = map(lambda c: c / 2, size)

    def cellc(self, cell):
        return (cell.x * self.ts[0], cell.y * self.ts[1])

    def blit(self, surface, coord, offset=True):
        if offset:
            coord = (coord[0] + self.os[0], coord[1] + self.os[1])
        rrect = surface.get_rect()
        ssize = map(lambda d: int(d * self.scalefactor), (rrect.w, rrect.h))
        surface = scale(surface, ssize)
        self.screen.blit(surface, coord)
        rrect.left, rrect.top = coord
        return rrect

    def blitall(self, scoords, offset=True):
        uprects = [self.blit(s[0], s[1], offset) for s in scoords]
        if uprects:
            pygame.display.update(uprects)
        return uprects

    def blitone(self, scoord, offset=True):
        uprect = self.blit(scoord[0], scoord[1], offset)
        pygame.display.update(uprect)
        return uprect

    def ptile(self, stuff):
        if stuff in ('player', 'block'):
            stuff = stuff + 'floor'
        surface = (self.__dict__[stuff + 'surface'] if
                   stuff else self.floorsurface)

        self.blitone((surface, self.hts), False)

    def pbar(self):
        barrect = ((0, self.os[1] - 2), ((self.rs[0] + 1) * self.ts[0], 2))
        pygame.draw.rect(self.screen, (255, 255, 255), barrect)
        pygame.display.update(barrect)

    def pbottom(self):
        barrect = ((0, self.os[1] + ((self.rs[1] + 1) * self.ts[1])), ((self.rs[0] + 1) * self.ts[0], 2))
        pygame.draw.rect(self.screen, (255, 255, 255), barrect)
        pygame.display.update(barrect)

    def pstats(self, grid, start, secs, force=False):
        end = time.time()
        moves = len(grid.movehistory)
        secs += int(end - start)
        if moves != self.lastmoves or force:
            barrect = ((0, self.os[1] + ((self.rs[1] + 1) * self.ts[1]) + 2), (98, self.ps[1] - 2))
            pygame.draw.rect(self.screen, (0, 0, 0), barrect)
            pygame.display.update(barrect)
            self.blitone((self.font.render('Moves: % 6d' % len(grid.movehistory), 1,
                                           (255, 255, 255)), (2, 4 + self.os[1] + ((self.rs[1] + 1) * self.ts[1]))), offset=False)
            self.lastmoves = moves
        if secs != self.lastsecs or force:
            psecs = secs % 60
            pmins = (secs / 60) % 60
            phours = (secs / 3600)
            barrect = ((98, self.os[1] + ((self.rs[1] + 1) * self.ts[1]) + 2), (((self.rs[0] + 1) * self.ts[0]) - 98, self.ps[1] - 2))
            pygame.draw.rect(self.screen, (0, 0, 0), barrect)
            pygame.display.update(barrect)
            self.blitone((self.font.render('Time: %02d:%02d:%02d' % (phours, pmins, psecs), 1,
                                           (255, 255, 255)), (98, 4 + self.os[1] + ((self.rs[1] + 1) * self.ts[1]))), offset=False)
            self.lastsecs = secs

    def plevel(self, level, name):
        fr = self.font.render('Level %d' % level, 1, (255, 255, 255))
        levelsize = self.blitone((fr, (96, 24)), offset=False)
        lname = name if name else '<Click to add name>'
        lr = self.font.render(lname, 1, (255, 255, 255))
        lnrect = self.blitone((lr, (96, 28 + levelsize.h)), offset=False)
        self.controlrects.append((lnrect, 'changename'))

    def phelpbutton(self):
        hbleft = (self.rs[0] + 1) * self.ts[0] - 39
        hb = ((hbleft, 2), (36, 20))
        self.controlrects.append((pygame.Rect(hb[0], hb[1]), 'help'))
        defaultbox(self.screen, hb, 'Help')

    def applyqf(self, cell, qf, adj):
        q = ''.join(['1' if adj(cell, *o) else '0' for o in qf[:3]])
        surface = rotate(self.qs[q][0], self.qs[q][1] + qf[3] * 90)
        return (surface, (self.ts[0] * (cell.x + qf[4][0]),
                          self.ts[1] * (cell.y + qf[4][1])))

    def pgrid(self, cells, adj, elephant, changed):
        surfaces = []
        for cell in changed:
            if cell.stuff == 'player' and cell.floor == 'target':
                self.blitone((self.targetsurface, self.cellc(cell)))
                ps = self.playerfloorsurface
                ps.set_alpha(150)
                self.blitone((ps, self.cellc(cell)))
                ps.set_alpha(255)
            elif cell.stuff in ('wall', 'space'):
                surfaces += [self.applyqf(cell, qf, adj) for qf in self.qfs]
            else:
                lookup = ((cell.stuff if cell.stuff else '') +
                          (cell.floor if cell.floor else 'floor'))
                surfaces.append((self.__dict__[lookup + 'surface'],
                                 self.cellc(cell)))

        self.blitall(surfaces)

    def doevent(self, event):
        if (event.type in (pygame.QUIT, pygame.MOUSEBUTTONDOWN) or
            (event.type == pygame.KEYDOWN and
             (event.key in self.moves or event.key in self.controls or
              event.key in self.shiftcontrols)) or
            (event.type == pygame.MOUSEBUTTONUP and event.button in (4, 5)) or
            (event.type == pygame.MOUSEMOTION and
             pygame.mouse.get_pressed()[0])):
            return event

    def getmove(self, cb=None, cbargs=None):
        while True:
            end = time.time()
            if cb and cbargs:
                cb(*cbargs)
            time.sleep(0.01)
            if (pygame.mouse.get_pressed()[2] and self.mstart and
                time.time() > self.mstart + 0.250):
                pygame.event.clear()
                time.sleep(0.05)
                return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3,
                                          pos=pygame.mouse.get_pos())
            if pygame.event.peek([pygame.MOUSEBUTTONUP, pygame.KEYUP]):
                event = pygame.event.get([pygame.MOUSEBUTTONUP,
                                          pygame.KEYUP])[0]
            else:
                events = pygame.event.get()
                event = events[0] if events else None

            if event:
                revent = self.doevent(event)
                if revent:
                    if (revent.type == pygame.MOUSEBUTTONDOWN and
                        revent.button == 3):
                        self.mstart = time.time()
                    return revent

    def initsoko(self):
        self.moves = {273: [0, -1], 274: [0, 1], 276: [-1, 0], 275: [1, 0],
                      104: [-1, 0], 106: [0, 1], 107: [0, -1], 108: [1, 0],
                      121: [-1, -1], 117: [1, -1], 98: [-1, 1], 110: [1, 1]}
        self.controls = {114: 'reset', 113: 'quit', 122: 'undo',
                         120: 'redo', 48: 'load0', 49: 'load1', 50: 'load2', 51: 'load3', 52: 'load4', 53: 'load5', 54: 'load6', 55: 'load7', 56: 'load8', 57: 'load9'}
        self.shiftcontrols = {48: 'save0', 49: 'save1', 50: 'save2', 51: 'save3', 52: 'save4', 53: 'save5', 54: 'save6', 55: 'save7', 56: 'save8', 57: 'save9', 47: 'help'}
        self.os = (0, 26)
        self.ps = (0, 26)
        pygame.display.set_caption('Sokoban')
        self.fontsize = 18
        self.font = pygame.font.Font(None, self.fontsize)
        pygame.key.set_repeat(250, 50)

    def initmaze(self, cells):
        self.moves = {273: [0, -1], 274: [0, 1], 276: [-1, 0], 275: [1, 0],
                      104: [-1, 0], 106: [0, 1], 107: [0, -1], 108: [1, 0],
                      121: [-1, -1], 117: [1, -1], 98: [-1, 1], 110: [1, 1]}
        self.controls = {}
        self.os = (0, 0)
        pygame.display.set_caption('Maze')
        self.fontsize = 18
        self.font = pygame.font.Font(None, self.fontsize)

        self.sets([48, 48])
        self.rs = [len(cells[..., 0]) - 1, len(cells[0, ...]) - 1]
        xside, yside = self.ts

        if self.rs[1] * self.ts[1] > self.desksize[1] - 100:
            print self.desksize[1], self.rs[1]
            yside = floor((float(self.desksize[1]) - 200.0) / float(self.rs[1]))

        if self.rs[0] * self.ts[0] > self.desksize[0] - 100:
            xside = floor((float(self.desksize[0]) - 200.0) / float(self.rs[0]))

        print xside, yside

        squareside = min(xside, yside)

        if squareside % 2:
            squareside += 1
        self.scalefactor = float(squareside) / float(self.ts[0])
        self.sets([squareside, squareside])
        self.initdisplay()

    def initdisplay(self):
        dispsize = ((self.rs[0] + 1) * self.ts[0] + self.os[0] + self.ps[0],
                    (self.rs[1] + 1) * self.ts[1] + self.os[1] + self.ps[1])
        self.window = pygame.display.set_mode(dispsize)
        self.screen = pygame.display.get_surface()

    def initlevel(self, cells):
        stuffcells = [c for c in cells.flat if
                      c.stuff and not c.stuff == 'space']
        furthestx = max(stuffcells, key=lambda c: c.x).x
        furthesty = max(stuffcells, key=lambda c: c.y).y

        self.rs = [furthestx, furthesty]
        self.sets([48, 48])

        xside, yside = self.ts

        if self.rs[1] * self.ts[1] > self.desksize[1] - 100:
            yside = (self.desksize[1] - 100) / self.rs[1]

        if self.rs[0] * self.ts[0] > self.desksize[0] - 100:
            xside = (self.desksize[0] - 100) / self.rs[0]

        squareside = min(xside, yside)

        if squareside % 2:
            squareside += 1
        self.scalefactor = float(squareside) / float(self.ts[0])
        self.sets([squareside, squareside])

        self.initdisplay()

    def initedit(self, cells):
        self.moves = {}
        self.controls = {115: 'save', 120: 'expandx', 121: 'expandy',
                         110: 'nextlevel', 112: 'previouslevel'}
        self.shiftcontrols = {120: 'expandxback', 121: 'expandyback'}
        self.sets([48, 48])
        self.rs = [len(cells[..., 0]) - 1, len(cells[0, ...]) - 1]
        self.os = (0, 96)
        self.ps = (0, 0)
        self.initdisplay()
        self.fontsize = 18
        self.font = pygame.font.Font(None, self.fontsize)
        display.set_caption('Sokoban Editor')

    def ptitle(self, level, levelname):
        lnstr = (' - %s' % levelname) if levelname else ''
        self.blitone((self.font.render('Level %d%s' % (level, lnstr), 1,
                                       (255, 255, 255)), (2, 2)), offset=False)

    def translate(self, input):
        if type(input) is list or input.type != pygame.KEYDOWN or input.key not in self.moves:
            return False
        return self.moves[input.key]

    def click2cell(self, pos):
        return [(pos[c] - self.os[c]) / self.ts[c] for c in (0, 1)]

    def changename(self, name):
        if not name:
            name = ''
        inbox = InputBox(self.screen)
        cnresult = inbox.ask("Level Name", text=name)
        if not cnresult:
            return
        if type(cnresult) is not str:
            if cnresult.type == pygame.QUIT:
                return ('control', 'quit')
        return cnresult

    def translatecontrol(self, input):
        if input.type == pygame.MOUSEBUTTONDOWN:
            for r in self.controlrects:
                if (r[0].left <= input.pos[0] <= r[0].right and
                    r[0].top <= input.pos[1] <= r[0].bottom):
                    return r[1]

            if input.button == 1:
                if ((self.os[0] < input.pos[0] <
                     self.os[0] + (self.rs[0] + 1) * self.ts[0])
                    and (self.os[1] < input.pos[1] <
                         self.os[1] + (self.rs[1] + 1) * self.ts[1])):
                    return ['routeto', self.click2cell(input.pos)]
                else:
                    return False
            elif input.button == 3:
                return 'undo'
            else:
                return 'notamove'
        if input.type == pygame.MOUSEBUTTONUP:
            return 'notamove'
        if input.type == pygame.MOUSEMOTION:
            if ((self.os[0] < input.pos[0] <
                 self.os[0] + (self.rs[0] + 1) * self.ts[0])
                and (self.os[1] < input.pos[1] <
                     self.os[1] + (self.rs[1] + 1) * self.ts[1])):
                return ['routeto', self.click2cell(input.pos)]
            else:
                return False
        if input.type == pygame.QUIT:
            return 'quit'
        if input.key not in self.controls and input.key not in self.shiftcontrols:
            return False
        if input.type == pygame.KEYDOWN:
            if input.mod & 3 and input.key in self.shiftcontrols:
                return self.shiftcontrols[input.key]
            elif not input.mod & 3 and input.key in self.controls:
                return self.controls[input.key]
            else:
                return False

    def translateeditcontrol(self, input):
        if input.type == pygame.QUIT:
            return 'quit'
        if input.type == pygame.MOUSEBUTTONDOWN:
            for r in self.controlrects:
                if (r[0].left <= input.pos[0] <= r[0].right and
                    r[0].top <= input.pos[1] <= r[0].bottom):
                    return r[1]
            if input.button == 1 and input.pos[1] > self.os[1]:
                return ['fill', self.click2cell(input.pos)]
            else:
                return False
        if input.type == pygame.MOUSEBUTTONUP:
            if input.button == 4:
                return 'stuffup'
            if input.button == 5:
                return 'stuffdown'
            else:
                return False
        if input.type == pygame.MOUSEMOTION:
            if input.pos[1] > self.os[1]:
                return ['fill', self.click2cell(input.pos)]
            else:
                return False
        if input.key not in self.controls and input.key not in self.shiftcontrols:
            return False
        if input.type == pygame.KEYDOWN:
            if input.mod & 3:
                return self.shiftcontrols[input.key]
            else:
                return self.controls[input.key]

    def endio(self):
        return

    def selecttile(self, proom):
        # stub
        return

    def refresh(self):
        # stub
        return

    def clear(self):
        # stub
        return

    def printhelp(self, grid, start, secs):
        helpfile = open('pygamehelp')
        inbox = InputBox(self.screen, boxw=260, boxh=220, cb=self.pstats, cbargs=(grid, start, secs))
        val = inbox.show(helpfile.read())
        if val:
            if val.type == pygame.QUIT:
                return 'quit'
            

    def anykey(self):
        # stub
        return
