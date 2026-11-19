# BLM-Traffic-simulator-in-PyGame
A simulator to play with the BLM traffic model from 1992.  A cellular automata that runs little cars 

A Pygame version of the 1992 Biham, Middleton & Levine traffic model (BML Traffic)
  https://en.wikipedia.org/wiki/Biham%E2%80%93Middleton%E2%80%93Levine_traffic_model

  Red cars move only East (right), blue cars move only North (up). The streets wrap around.
  Every "flip" all the red cars get a turn, every "flop" all the blue cars get a turn.
  A car only moves if the space ahead is empty when it gets its turn.
  East cars are checked right to left and North cars top to bottom, so a line of cars
  can all move together once the one in front has moved and made a clear space.

  Keys:  + / -   add / remove 10 cars        r  random board      c  clear
         RETURN  run / stop                  SPACE  one step (one flip or flop)
         ESC     quit
  Mouse: left click puts a red car, right click puts a blue car, hold SHIFT to erase
  Slider: speed (steps per second)

  Andy Richter  Original code Nov, 2026
  Free to use change or whatever
