import pyxel
import random

TETROMINOES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1],
          [1, 1]],
    'T': [[0, 1, 0],
          [1, 1, 1]],
    'S': [[0, 1, 1],
          [1, 1, 0]],
    'Z': [[1, 1, 0],
          [0, 1, 1]],
    'J': [[1, 0, 0],
          [1, 1, 1]],
    'L': [[0, 0, 1],
          [1, 1, 1]]
}

TETROMINOES_COLORS = {
    'S': 3,
    'J': 5,
    'Z': 8,
    'T': 2,
    'O': 10,
    'I': 12,
    'L': 9
}
class Tetrimino:
	def __init__(self, shape, width, color):
		self.shape = shape
		self.color = color
		self.x = width // 2
		self.y = 0
