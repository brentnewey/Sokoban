#! /usr/bin/env python
from optparse import OptionParser
from time import sleep

from grid import Grid#, DIMX, DIMY
#from cursesio import CursesIO
from pygameio import PygameIO

def main(ioobj, options):
    grid = Grid(101, 101, True, ioobj)
    grid.sightradius = int(options.sightradius)
    grid.elephant = options.elephant
    grid.omniscient = True
    grid.mazify()
    exit = grid.makeexit()
    player = grid.placeplayer()
    route = grid.calculateroute(player, exit)
    for c in grid.cells.flat:
        c.changed = True
        c.seen = True
    ioobj.initmaze(grid.cells)
    while not grid.free:
        
 #       if not options.omniscient:
#            seenrooms = grid.tracesides()
#            grid.seerooms(seenrooms)
        grid.pgrid()
        if options.solve:
            ioobj.refresh()
            sleep(0.05)
            if route:
                inval = route.pop(0)
            else:
                grid.finalmove()
                break
            grid.moveplayer(inval[0], inval[1])
        else:
            move = ioobj.getmove()
            control = ioobj.translatecontrol(move)
            if control == 'solve':
                options.solve = True
                player = grid.playerroom()
                route = grid.calculateroute(player, exit)
            else:
                grid.translatemove(move)

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option('-s', '--solve', action="store_true", dest="solve",
                      help='Solve the dungeon for me.')
    parser.add_option('-e', '--elephant', action="store_true", dest="elephant",
                      help='Play as an elephant.')
#    parser.add_option('-o', '--omniscient', action="store_true", dest="omniscient",
#                      help='You see everything in the maze.')
    parser.add_option('-r', '--sightradius', default=10,
                      help='Sight Radius')
    options, args = parser.parse_args()

#    ioobj = CursesIO(True)
    ioobj = PygameIO()
    try:
        main(ioobj, options)
    finally:
        ioobj.endio()
    if options.elephant:
        print 'snOOOOOOOOOORT!'
    else:
        print 'Well done!'
