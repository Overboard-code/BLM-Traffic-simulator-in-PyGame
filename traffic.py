#!/usr/bin/python3
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import pygame_widgets as pw
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider
import sys
import numpy as np

#
#  A Pygame version of the 1992 Biham, Middleton & Levine traffic model (BML Traffic)
#  https://en.wikipedia.org/wiki/Biham%E2%80%93Middleton%E2%80%93Levine_traffic_model
#
#  Red cars move only East (right), blue cars move only North (up). The streets wrap around.
#  Every "flip" all the red cars get a turn, every "flop" all the blue cars get a turn.
#  A car only moves if the space ahead is empty when it gets its turn.
#  East cars are checked right to left and North cars top to bottom, so a line of cars
#  can all move together once the one in front has moved and made a clear space.
#
#  Keys:  + / -   add / remove 10 cars        r  random board      c  clear
#         RETURN  run / stop                  SPACE  one step (one flip or flop)
#         ESC     quit
#  Mouse: left click puts a red car, right click puts a blue car, hold SHIFT to erase
#  Slider: speed (steps per second)
#
#  Andy Richter  Original code Nov, 2026
#  Free to use change or whatever
#

# ---------- CONSTANTS ----------
bkgnd_color = 'grey88'      # also used for empty cells
grid_color = 'grey80'
bar_color = 'grey70'
East = 'red'
North = 'darkblue'
top_color = 'darkgreen'
text_color = 'snow'
shadows = 'grey23'
hover_color = 'grey46'
click_color = 'grey66'

EMPTY, EAST_CAR, NORTH_CAR = 0, 1, 2
cell_colors = {EAST_CAR: pygame.Color(East), NORTH_CAR: pygame.Color(North)}

Grid = True                 # True to draw a grid behind the cars
cellSize = 5
thesize = 140               # number of columns
barHeight = 8 * cellSize    # strip along the bottom for buttons and slider
thehigh = thesize - barHeight // cellSize   # number of rows of road
windowsize = thesize * cellSize
buttonSlots = 8
slotSize = windowsize / buttonSlots
startDensity = 0.15     # fraction of cells that get a car at start and on Random
initFPS = 30                    # slider start, steps per second
minF = 2
maxF = 300

# ---------- GLOBAL STATE ----------
board = np.zeros((thesize, thehigh), dtype=int)   # board[x, y]; y = 0 is the top row
carsPerKey = max(1, board.size // 300)  # how many cars + and - add or remove (.33% of the board)
eastsTurn = True    # True = next step is a flip (East), False = a flop (North)
run = False
stepOnce = False
idleSteps = 0       # consecutive steps where nothing moved (gridlock detector)
FPS = initFPS

# ---------- PYGAME SETUP ----------
pygame.init()
surface = pygame.display.set_mode((windowsize, windowsize))
clock = pygame.time.Clock()
gui_font = pygame.font.Font(None, 22)
pygame.key.set_repeat(400, 60)      # hold + or - to keep adding or removing

# Pre-draw the background (grid + button strip) once
background = pygame.Surface((windowsize, windowsize))
background.fill(pygame.Color(bkgnd_color))
if Grid:
    for i in range(0, thesize + 1):
        pygame.draw.line(background, pygame.Color(grid_color), (i * cellSize, 0), (i * cellSize, thehigh * cellSize))
    for j in range(0, thehigh + 1):
        pygame.draw.line(background, pygame.Color(grid_color), (0, j * cellSize), (windowsize, j * cellSize))
background.fill(pygame.Color(bar_color), (0, thehigh * cellSize, windowsize, windowsize - thehigh * cellSize))


# ---------- COMMANDS FOR BUTTONS AND KEYS ----------
def resetCounters():
    global eastsTurn, idleSteps
    eastsTurn = True
    idleSteps = 0

def runStop():          # Key RETURN
    global run, idleSteps
    run = not run
    idleSteps = 0

def setSingle():        # Key SPACE
    global stepOnce, run
    run = False
    stepOnce = True

def newRandom():        # Key 'r'
    board.fill(EMPTY)
    n = int(board.size * startDensity)
    spots = np.random.choice(board.size, n, replace=False)
    kinds = np.array([EAST_CAR, NORTH_CAR] * ((n + 1) // 2))[:n]   # half red, half blue
    board.flat[spots] = kinds
    resetCounters()

def boardClear():       # Key 'c'
    board.fill(EMPTY)
    resetCounters()

def addCars(n=carsPerKey):     # Key '+'   half red, half blue
    global idleSteps
    empty = np.argwhere(board == EMPTY)
    n = min(n, len(empty))
    if n == 0:
        return
    pick = empty[np.random.choice(len(empty), n, replace=False)]
    kinds = np.array([EAST_CAR, NORTH_CAR] * ((n + 1) // 2))[:n]
    board[pick[:, 0], pick[:, 1]] = kinds
    idleSteps = 0

def removeCars(n=carsPerKey):  # Key '-'
    global idleSteps
    cars = np.argwhere(board != EMPTY)
    n = min(n, len(cars))
    if n == 0:
        return
    pick = cars[np.random.choice(len(cars), n, replace=False)]
    board[pick[:, 0], pick[:, 1]] = EMPTY
    idleSteps = 0

def game_quit():        # Key ESCAPE
    pygame.quit()
    sys.exit()

# ---------- THE BML RULES ----------
def moveEast():
    """Flip: every red car moves right one cell if that cell is empty.
    Columns are checked right to left so a space cleared by a car moving off
    can be used by the car behind it in the same flip."""
    moved = 0
    wrapped = None
    for x in range(thesize - 1, -1, -1):
        nxt = (x + 1) % thesize
        movers = (board[x, :] == EAST_CAR) & (board[nxt, :] == EMPTY)
        if x == 0:
            movers &= ~wrapped      # a car that just wrapped around already had its turn
        if x == thesize - 1:
            wrapped = movers.copy()
        board[nxt, movers] = EAST_CAR
        board[x, movers] = EMPTY
        moved += int(movers.sum())
    return moved

def moveSouth():
    """Flop: every blue car moves down one cell if that cell is empty.
    Rows are checked bottom to top, so a space cleared by a car moving off
    can be used by the car above it in the same flop."""
    moved = 0
    wrapped = None
    for y in range(thehigh - 1, -1, -1):
        nxt = (y + 1) % thehigh
        movers = (board[:, y] == NORTH_CAR) & (board[:, nxt] == EMPTY)
        if y == 0:
            movers &= ~wrapped      # a car that just wrapped to the top already had its turn
        if y == thehigh - 1:
            wrapped = movers.copy()
        board[movers, nxt] = NORTH_CAR
        board[movers, y] = EMPTY
        moved += int(movers.sum())
    return moved

def takeStep():
    """One half step: a flip (East) then next time a flop (North)."""
    global eastsTurn, idleSteps, run
    if eastsTurn:
        moved = moveEast()
    else:
        moved = moveSouth()
    eastsTurn = not eastsTurn
    idleSteps = 0 if moved else idleSteps + 1
    if idleSteps >= 2:      # neither color could move: total gridlock
        run = False


# ---------- DRAWING ----------
def drawBoard():
    surface.blit(background, (0, 0))
    for kind, colour in cell_colors.items():
        for x, y in np.argwhere(board == kind):
            surface.fill(colour, (x * cellSize + 1, y * cellSize + 1, cellSize - 1, cellSize - 1))

def updateCaption():
    cars = int(np.count_nonzero(board))
    state = 'GRIDLOCK' if idleSteps >= 2 else ('running' if run else 'stopped')
    nextUp = 'East' if eastsTurn else 'North'
    pygame.display.set_caption(f'BML Traffic  Cars={cars} Speed={int(FPS)}  {state}')

def where():
    x, y = pygame.mouse.get_pos()
    return x // cellSize, y // cellSize


# ---------- WIDGETS ----------
def makeAButton(slot, label, routine):
    return Button(surface, int(slotSize * slot + 4), windowsize - barHeight + 5, int(slotSize) - 8, 30,
                  text=label, onClick=routine,
                  font=gui_font, textColour=text_color, margin=cellSize,
                  inactiveColour=top_color, hoverColour=hover_color, pressedColour=click_color,
                  shadowDistance=3, shadowColour=shadows, radius=8)

rndm_button = makeAButton(0, 'Random', newRandom)
play_button = makeAButton(1, 'Go/Stop', runStop)
step_button = makeAButton(2, 'Once', setSingle)
quit_button = makeAButton(3, 'Quit', game_quit)
clear_button = makeAButton(4, 'Clear', boardClear)

FPS_slider = Slider(surface, int(slotSize * 5 + 14), windowsize - barHeight + 16, int(slotSize * 3 - 28), 8,
                    min=minF, max=maxF, initial=initFPS, handleRadius=8,
                    handleColour=tuple(pygame.Color(top_color))[:3])

newRandom()     # start with some traffic

# ---------- MAIN LOOP ----------
while True:
    drawBoard()

    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            game_quit()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                addCars()
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                removeCars()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE:
                game_quit()
            elif event.key == pygame.K_SPACE:
                setSingle()
            elif event.key == pygame.K_RETURN:
                runStop()
            elif event.key == pygame.K_c:
                boardClear()
            elif event.key == pygame.K_r:
                newRandom()
    pw.update(events)       # draws and handles the buttons and slider

    # Advance the traffic
    if run or stepOnce:
        takeStep()
        stepOnce = False

    # Mouse: left = red car, right = blue car, SHIFT + click = erase
    presses = pygame.mouse.get_pressed()
    if presses[0] or presses[2]:
        cx, cy = where()
        if 0 <= cx < thesize and 0 <= cy < thehigh:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                board[cx, cy] = EMPTY
            else:
                board[cx, cy] = EAST_CAR if presses[0] else NORTH_CAR

    FPS = FPS_slider.getValue()
    updateCaption()
    pygame.display.flip()
    clock.tick(FPS if run else 60)
