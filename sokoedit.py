#! /usr/bin/env python
from optparse import OptionParser
from time import sleep
from os.path import exists

from grid import Grid, DIMX, DIMY
from pygameio import PygameIO

def main(ioobj, options):
    grid = Grid(5, 5, True, ioobj)
    grid.level = int(options.level)
    if options.levelset and exists('levels/' + options.levelset):
        grid.levelset = options.levelset
        grid.loadlevel()
        for c in grid.cells.flat:
            if c.stuff == 'space':
                c.stuff = 'wall' 
    else:
        for c in grid.cells.flat:
            c.changed = True
            c.stuff = 'wall'
    ioobj.initedit(grid.cells)
    ioobj.pbar()
    ioobj.plevel(grid.level, grid.levelname)
    editing = True
    stufflist = [None, 'wall', 'player', 'block', 'target']
    cstuff = 0
    while editing:
        ioobj.ptile(stufflist[cstuff])
        grid.pgrid()
        move = ioobj.getmove()
        control = ioobj.translateeditcontrol(move)
        if control:
            if type(control) is list and control[0] == 'fill':
                fillcell = grid.cells[control[1][0], control[1][1]]
                grid.fill(fillcell, stufflist[cstuff])
            elif control == 'stuffup':
                cstuff += 1
                if cstuff == len(stufflist):
                    cstuff = 0
            elif control == 'stuffdown':
                cstuff -= 1
                if cstuff == -1:
                    cstuff = len(stufflist) - 1
            elif control == 'changename':
                cnresult = ioobj.changename(grid.levelname)
                if cnresult == None:
                    for cell in grid.cells.flat:
                        cell.changed = True
                if type(cnresult) is tuple:
                    control = cnresult[1]
                    if control == 'quit':
                        editing = False
                        break
                grid.levelname = cnresult
                ioobj.initedit(grid.cells)
                ioobj.pbar()
                ioobj.plevel(grid.level, grid.levelname)
                for cell in grid.cells.flat:
                    cell.changed = True
            elif control in ['nextlevel', 'previouslevel']:
                if control == 'previouslevel' and grid.level == 1:
                    continue
                oldlevel = grid.level
                grid.save(options.levelset if options.levelset else 'p1')
                grid = Grid(5, 5, True, ioobj)
                if control == 'nextlevel':
                    grid.level = oldlevel + 1
                if control == 'previouslevel':
                    grid.level = oldlevel - 1
                if options.levelset and exists('levels/' + options.levelset):
                    grid.levelset = options.levelset
                    loaded = grid.loadlevel()
                    if loaded:
                        for c in grid.cells.flat:
                            if c.stuff == 'space':
                                c.stuff = 'wall' 
                    else:
                        for c in grid.cells.flat:
                            c.changed = True
                            c.stuff = 'wall'
                else:
                    for c in grid.cells.flat:
                        c.changed = True
                        c.stuff = 'wall'
                ioobj.initedit(grid.cells)
                ioobj.pbar()
                ioobj.plevel(grid.level, grid.levelname)
            elif control in ('expandx', 'expandy', 'expandxback',
                             'expandyback'):
                if control == 'expandx':
                    grid.stackx()
                elif control == 'expandxback':
                    grid.stackx(back=True)
                elif control == 'expandy':
                    grid.stacky()
                elif control == 'expandyback':
                    grid.stacky(back=True)
                ioobj.initedit(grid.cells)
                ioobj.pbar()
                ioobj.plevel(grid.level, grid.levelname)
                for cell in grid.cells.flat:
                    cell.changed = True
            elif control == 'save':
                grid.save(options.levelset if options.levelset else 'p1')
                editing = False
            elif control == 'quit':
                editing = False

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option('-s', '--levelset', default=None,
                      help='Level set')
    parser.add_option('-l', '--level', default=1,
                      help='Level')
    options, args = parser.parse_args()
    ioobj = PygameIO()
    try:
        main(ioobj, options)
    finally:
        ioobj.endio()
