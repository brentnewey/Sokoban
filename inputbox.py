""" inputbox.by by Brent Newey

Create a box on the screen that accepts keyboard input, and returns
the typed string.

"""
from string import maketrans
from time import sleep
from sys import argv, exit

from pygame import font, event, draw, display, KEYDOWN, KEYUP, QUIT, MOUSEBUTTONDOWN
import pygame.key
from pygame.locals import K_BACKSPACE, K_RETURN, K_ESCAPE, K_END

BOXW = 200
BOXH = 20
BORDERW = 2
BOXC = (0, 0, 0)
BORDERC = (255, 255, 255)
TEXTC = (255, 255, 255)
FONTFILE = None
FONTSIZE = 18
FONTSPACE = 2

def blitfont(screen, text, xy, fontobj, textc):
    return screen.blit(fontobj.render(text, 1, textc), xy)

def textbox(screen, orect, irect, fontupleft, fontobj, text,
            borderc=BORDERC, boxc=BOXC, textc=TEXTC):
    draw.rect(screen, borderc, orect)
    draw.rect(screen, boxc, irect)
    tw = 0

    if text:
        textlines = text.split('\n')
        th = 0
        for t in textlines:
            tupleft = (fontupleft[0], fontupleft[1] + th)
            fontrect = blitfont(screen, t, tupleft, fontobj, textc)
            tw = max(tw, fontrect.w)
            th += fontrect.h + 2

    display.update(orect)
    return tw

def defaultbox(screen, orect, text):

    irect = (tuple(i + BORDERW for i in orect[0]),
             tuple(b - 2 * BORDERW for b in orect[1]))
    fontupleft = tuple(i + 2 for i in irect[0])
    font.init()
    fontobj = font.Font(FONTFILE, FONTSIZE)
    textbox(screen, orect, irect, fontupleft, fontobj, text,
            borderc=BORDERC, boxc=BOXC, textc=TEXTC)

class InputBox():
    "InputBox class - __init__ handles all custom variables."

    def __init__(self, screen, boxw=BOXW, boxh=BOXH, borderw=BORDERW,
                 boxc=BOXC, borderc=BORDERC, textc=TEXTC, fontfile=FONTFILE,
                 fontsize=FONTSIZE, fontspace=FONTSPACE, transtable=None,
                 cb=None, cbargs=None):
        self.__dict__.update(locals())
        self.inupleft = ((screen.get_width() - boxw) / 2,
                         (screen.get_height() - boxh) / 2)
        self.outupleft = tuple(i - borderw for i in self.inupleft)
        self.fontupleft = tuple(i + boxh / 10 for i in self.inupleft)
        self.irect = (self.inupleft, (boxw, boxh))
        self.orect = (self.outupleft,
                      tuple(b + 2 * borderw for b in (boxw, boxh)))

        font.init()
        self.fontobj = font.Font(fontfile, fontsize)
        pygame.key.set_repeat(250, 50)

    def blitfont(self, text, xy):
        "Blit text at the given xy coordinates."
        return blitfont(self.screen, text, xy, self.fontobj, self.textc)

    def box(self, text):
        "Print a box in the middle of the screen."
        return textbox(self.screen, self.orect, self.irect, self.fontupleft,
                       self.fontobj, text, self.borderc, self.boxc, self.textc)

    def message(self, qw, text):
        "Display entered text."
        frect = ((self.irect[0][0] + qw, self.irect[0][1]),
                 (self.irect[1][0] - qw, self.irect[1][1]))
        draw.rect(self.screen, self.boxc, frect)
        if text:
            self.blitfont(text, (self.fontupleft[0] + qw, self.fontupleft[1])) 
        display.update(self.irect)

    def ask(self, question, text=''):
        "ask(question, text) -> answer"
        qw = self.box('%s: ' % question)
        lasttext = None
        while 1:
            if self.cb and self.cbargs:
                self.cb(*self.cbargs)
            sleep(0.01)
            if lasttext != text:
                self.message(qw, text)
                lasttext = text
            events = event.get((KEYDOWN, QUIT))
            if not events:
                continue
            if QUIT in [e.type for e in events]:
                return e
            elif events[0].key == K_BACKSPACE:
                text = text[:-1]
            elif events[0].key in (K_ESCAPE, K_END):
                return None
            elif events[0].key == K_RETURN:
                return text
            elif 31 < events[0].key < 127:
                key = events[0].unicode.encode('ascii')
                text += (key.translate(self.transtable) if
                         self.transtable else key)

    def show(self, text):
        self.box(text)
        while 1:
            if self.cb and self.cbargs:
                self.cb(*self.cbargs)
            sleep(0.01)
            events = event.get((KEYDOWN, MOUSEBUTTONDOWN, QUIT))
            if not events:
                event.clear()
                continue
            if QUIT in [e.type for e in events]:
                return e
            else:
                sleep(0.1)
                return

if __name__ == '__main__':
    screen = display.set_mode((320,240))
    if len(argv) > 1 and argv[1] == 'show':
        InputBox(screen, boxw=170).show('You are the Messiah of Earth')
    if len(argv) > 1 and argv[1] == 'multiline':
        inbox = InputBox(screen, boxw=120, boxh=35)
        inbox.show('You are the\nMessiah of Earth')
    if len(argv) > 1 and argv[1] == 'box':
        defaultbox(screen, ((5, 5), (40, 20)), 'Help')
        sleep(5)
    if len(argv) == 1:
        intext = InputBox(screen).ask('Yo dawg')
        if type(intext) is str:
            print "'%s' was entered" % intext
