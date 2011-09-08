#! /usr/bin/env python
from optparse import OptionParser
from time import sleep, time
import os
import pickle

from grid import Grid, DIMX, DIMY
#from cursesio import CursesIO
from pygameio import PygameIO

def main(ioobj, options):
    start = 0
    secs = 0
    ioobj.initsoko()
    grid = Grid(DIMX, DIMY, True, ioobj)
    loadoptions = False
    restart = False
    if not options.levelset:
        try:
            options.levelset = max([(f, os.path.getmtime(os.path.expanduser("~") +
                                                         '/' + f)) for
                                    f in os.listdir(os.path.expanduser("~")) if
                                    f[:8] == '.sokoban'],
                                   key=lambda f: f[1])[0][9:]
            if '.' in options.levelset:
                options.levelset = options.levelset.split('.')[0]
        except Exception:
            options.levelset = 'm1'
    if options.level:
        grid.level = int(options.level)
        grid.levelset = options.levelset
        loadoptions = True
    elif os.path.exists(os.path.expanduser("~") + '/.sokoban.' + options.levelset):
        grid = pickle.load(open(os.path.expanduser("~") + '/.sokoban.' + options.levelset))
        if 'secs' in grid.__dict__:
            secs = grid.secs
        for c in grid.cells.flat:
            c.changed = True
        grid.ioobj = ioobj
    else:
        grid.level = 1
        grid.levelset = options.levelset
        loadoptions = True

    while grid.level:
        if loadoptions:
            loaded = grid.loadlevel()
            if not loaded:
                return
        loadoptions = True
        grid.initlevel()
        ioobj.pbar()
        ioobj.pbottom()
        grid.ptitle()
        ioobj.phelpbutton()
        if not start:
            start = time()
        if not secs:
            secs = 0
        ioobj.pstats(grid, start, secs, True)
        while not grid.free:
            grid.pgrid()
            move = ioobj.getmove(cb=ioobj.pstats, cbargs=(grid, start, secs))
            control = ioobj.translatecontrol(move)
            if type(control) is list:
                if control[0] == 'routeto':
                    proom = grid.playerroom()
                    offx = control[1][0] - proom.x
                    offy = control[1][1] - proom.y
                    if abs(offx) + abs(offy) == 1:
                        target = grid.cells[control[1][0], control[1][1]]
                        if target and target.stuff in [None, 'block']:
                            grid.moveplayer(proom.x + offx, proom.y + offy)
                    else:
                        route = grid.calculateroute(proom, grid.cells[control[1][0], control[1][1]])
                        if route:
                            move = route.pop(0)
                            while move:
                                grid.pgrid()
                                ioobj.refresh()
                                sleep(0.01)
                                grid.moveplayer(move[0], move[1])
                                if route:
                                    move = route.pop(0)
                                else:
                                    break                    
            if control == 'routeto':
                proom = grid.playerroom()
                coords = ioobj.selecttile(proom)
                route = grid.calculateroute(proom, grid.cells[coords[0], coords[1]])
                if route:
                    move = route.pop(0)
                    while move:
                        grid.pgrid()
                        ioobj.refresh()
                        sleep(0.01)
                        grid.moveplayer(move[0], move[1])
                        if route:
                            move = route.pop(0)
                        else:
                            break

            if control == 'help':
                ioobj.clear()
                help = open('help')
                quit = ioobj.printhelp(grid, start, secs)
                if quit:
                    grid.ioobj = None
                    pickle.dump(grid, open(os.path.expanduser("~") + '/.sokoban.' + options.levelset, 'w'))
                    return
                ioobj.anykey()
                for cell in grid.cells.flat:
                    cell.changed = True
                grid.ptitle()
            if control == 'reset':
                break
            if control == 'quit':
                grid.ioobj = None
                grid.secs = ioobj.lastsecs
                pickle.dump(grid, open(os.path.expanduser("~") + '/.sokoban.' + options.levelset, 'w'))
                return
            if control == 'undo':
                grid.undomove()
            if control == 'redo':
                grid.redomove()
            if type(control) is str and len(control) > 4 and control[:4] == 'save':
                tempio = grid.ioobj
                grid.secs = ioobj.lastsecs
                grid.ioobj = None
                pickle.dump(grid, open(os.path.expanduser("~") + '/.sokoban.' + options.levelset + '.' + str(grid.level) + '.' + control[4:], 'w'))
                grid.ioobj = tempio
            if type(control) is str and len(control) > 4 and control[:4] == 'load':
                if os.path.exists(os.path.expanduser("~") + '/.sokoban.' + options.levelset + '.' + str(grid.level) + '.' + control[4:]):
                    tempio = grid.ioobj
                    grid = pickle.load(open(os.path.expanduser("~") + '/.sokoban.' + options.levelset + '.' + str(grid.level) + '.' + control[4:]))
                    if 'secs' in grid.__dict__:
                        secs = max(grid.secs, secs)
                    for c in grid.cells.flat:
                        c.changed = True
                    grid.ioobj = tempio
            if not control:
                grid.translatemove(move)
            grid.victory()
            restart = True
        if grid.free:
            grid.level += 1
            secs = 0
            start = None
        grid.movehistory = []
        grid.moveindex = -1
        grid.free = False
            

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option('-l', '--level', default=None,
                      help='Level')
    parser.add_option('-s', '--levelset', default=None,
                      help='Level set')
    options, args = parser.parse_args()
#    ioobj = CursesIO()
    ioobj = PygameIO()
    try:
        main(ioobj, options)
    finally:
        ioobj.endio()
