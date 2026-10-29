from board import Direction, Rotation, Action, Shape
from random import Random
import time


class Player:
    count = 0
    rotationCount = 0
    direction = Direction.Left
    rotationLimit = 3
    best_rotate = 0
    best_count = 0
    best_score = -float("inf")
    best_direction = Direction.Left
    move = False
    emergency = False
    xHoleCoordinate = -1

    def print_board(self, board):
        print("--------")
        for y in range(24):
            s = ""
            for x in range(10):
                if (x,y) in board:
                    s += "#"
                else:
                    s += "."
            print(s, y)
    def set_limits(self, board):
        if board.falling.shape == Shape.I:
            self.rotationLimit = 1
        elif board.falling.shape == Shape.O:
            self.rotationLimit = 0
        elif board.falling.shape == Shape.S or board.falling.shape == Shape.Z:
            self.rotationLimit = 1
        else:
            self.rotationLimit = 3

    def reset_variables(self, board):
        switchCondition = False
        switchBackCondition = False
        if board.falling is not None:
            switchCondition = board.falling.left == 0
            switchBackCondition = board.falling.right == 9
        else:
            switchCondition = self.count > 5
            switchBackCondition = self.count > 5
        if self.direction == Direction.Left and switchCondition:
            self.direction = Direction.Right
            self.count = 1
        elif self.direction == Direction.Right and switchBackCondition:
            self.direction = Direction.Left
            self.count = 0
            self.rotationCount += 1
            if self.rotationCount > self.rotationLimit:
                self.rotationCount = 0
                self.move = True

    def move_in_sandbox(self, board):
        for i in range(self.rotationCount):
            if board.falling is None:
                return
            board.rotate(Rotation.Clockwise)
        for i in range(self.count):
            if board.falling is None:
                return
            board.move(self.direction)

    def how_many_holes(self, board):
        holes = 0
        for x in range(10):
            for y in range(24):
                if (x,y) not in board.cells and any((x,yy) in board.cells for yy in range(y-1,-1,-1)):
                    holes += 1
        return holes
    
    def score(self, board, sandbox):
        sandbox2 = sandbox.clone()
        if sandbox2.falling is None:
            return 0
        sandbox2.move(Direction.Drop)
        score = sandbox2.score
        result = set(sandbox2.cells) - set(board.cells)
        if result is not None and len(result) > 0:
            score -= (23 - min(y for (_, y) in result)) ** 2
            score -= ((23 - max(y for (_, y) in result)) ** 2) / 5
        score -= self.how_many_holes(sandbox2) * 50
        topLevel = -1
        values = []
        for x in range(10):
            for y in range(24):
                if (x,y) in sandbox2.cells:
                    values.append(y)
                    break
        diff = 10 - len(values)
        if diff > 0:
            for i in range(diff):
                values.append(24)
        mean = sum(values) / 10
        sumOfDiffs = 0
        for v in values:
            sumOfDiffs += (v - mean) ** 2
        variance = sumOfDiffs / 10
        score -= variance * 20
        return score
    
    def check_score(self, current_score):
        if current_score > self.best_score:
            self.best_score = current_score
            self.best_rotate = self.rotationCount
            self.best_count = self.count
            self.best_direction = self.direction
    
    def choose_action(self, board):
        if board.falling.shape == Shape.B:
            result = self.xHoleCoordinate - 5
            if result < 0:
                for i in range(abs(result)):
                    yield Direction.Left
            elif result > 0:
                for i in range(abs(result)):
                    yield Direction.Right
            yield Direction.Drop
        if self.emergency:
            if board.falling.shape != Shape.I:
                if board.discards_remaining > 0:
                    yield Action.Discard
                else:
                    self.emergency = False
            else:
                self.emergency = False
        sandbox = board.clone()
        self.set_limits(board)
        self.move_in_sandbox(sandbox)
        current_score = self.score(board, sandbox)
        self.check_score(current_score)
        self.count += 1
        self.reset_variables(sandbox)
        if sandbox.falling is not None:
            sandbox.move(Direction.Drop)
        if self.move:
            for i in range(self.best_rotate):
                yield Rotation.Clockwise
            for i in range(self.best_count):
                yield self.best_direction
            self.best_score = -float("inf")
            self.move = False
            bombSandbox = board.clone()
            bombSandbox.move(Direction.Drop)
            for x in range(10):
                topLevel = -1
                for y in range(24):
                    if (x,y) in bombSandbox:
                        if topLevel == -1 and y < 22:
                            topLevel = y
                            if (x, y+1) not in bombSandbox:
                                self.xHoleCoordinate = x
                                yield Action.Bomb
                        if  y == 9:
                            self.emergency = True
            self.print_board(board)
            yield Direction.Drop


SelectedPlayer = Player