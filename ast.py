from rply.token import BaseBox


class Var(BaseBox):
    def __init__(self, value):
        self.value = value
        
    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.value == other.value

    def eval(self):
        return self.value

    def show(self):
        return f'{self.__class__.__name__} {self.value}'


class BinaryOp(BaseBox):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.left == other.left and self.right == other.right 

    def show(self):
        return f'{self.__class__.__name__}({self.left.show()},{self.right.show()})'


class UnaryOp:
    def __init__(self, argument):
        self.argument = argument

    def show(self):
        return f'{self.__class__.__name__}({self.argument.show()})'


class Negation(UnaryOp):
    def eval(self):
        return self.argument.eval()

    def introduce(self):
        return [([], [self.argument])]

    def eliminate(self):
        return [([self.argument], [])]


class Imp(BinaryOp):
    def eval(self):
        return self.left, self.right

    def introduce(self):
        return [([], [self.left]), ([self.right], [])]

    def eliminate(self):
        return [([self.left], [self.right])]


class Disj(BinaryOp):
    def eval(self):
        return self.left.eval(), self.right.eval()

    def introduce(self):
        return [([self.left], []), ([self.right], [])]

    def eliminate(self):
        return [([], [self.left, self.right])]


class Conj(BinaryOp):
    def eval(self):
        return self.left.eval(), self.right.eval()

    def introduce(self):
        return [([self.left, self.right], [])]

    def eliminate(self):
        return [([], [self.left]), ([], [self.right])]


class Forall(BinaryOp):
    def eval(self):
        return self.left.eval(), self.right.eval()


class Exists(BinaryOp):
    def eval(self):
        return self.left.eval(), self.right.eval()
