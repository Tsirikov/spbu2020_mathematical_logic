from rply.token import BaseBox


class Term(BaseBox):
    def __init__(self, name, args=None):
        self.name = name
        self.args = args
        if args is not None:
            for item in args:
                if not isinstance(item, Term):
                    raise ValueError(
                        f'Inappropriate argument for '
                        f'"{self.name}": {item.show()} should be Term, not {item.__class__.__name__}.')

    def __eq__(self, other):
        if self.__class__ == other.__class__ and self.name == other.name:
            eq_args = self.args is None and other.args is None
            if not (self.args is None or other.args is None):
                eq_args = (len(self.args) == len(other.args) and all([i == j for i, j in zip(self.args, other.args)]))
            return eq_args
        return False

    def copy(self):
        if self.args is None:
            return self.__class__(self.name)
        else:
            return self.__class__(self.name, self.args.copy())

    def show(self):
        if self.args is None:
            return f'{self.name}'
        else:
            return f'{self.name}({", ".join(map(lambda x: x.show(), self.args))})'


class Atom(BaseBox):
    def __init__(self, name, args):
        self.name = name
        self.args = args
        for item in args:
            if not isinstance(item, Term):
                raise ValueError(
                    f'Inappropriate argument for '
                    f'"{self.name}": {item.show()} should be Term, not {item.__class__.__name__}.')

    def __eq__(self, other):
        if self.__class__ == other.__class__ and self.name == other.name:
            return len(self.args) == len(other.args) and all([i == j for i, j in zip(self.args, other.args)])
        return False

    def copy(self):
        return self.__class__(self.name, self.args.copy())

    def show(self):
        if self.args is None:
            return f'{self.name}'
        else:
            return f'{self.name}({", ".join(map(lambda x: x.show(), self.args))})'


class UnaryOp:
    def __init__(self, argument):
        if not isinstance(argument, Term):
            self.argument = argument
        else:
            raise ValueError(
                f'In {self.__class__.__name__}, {argument.show()} should be Expr, not {argument.__class__.__name__}.')

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.argument == other.argument

    def copy(self):
        return self.__class__(self.argument.copy())

    def show(self):
        name = self.__class__.__name__
        if name == 'Negation':
            output = '~'
        else:
            output = name
        return f'{output}{self.argument.show()}'


class BinaryOp(BaseBox):
    def __init__(self, left, right):
        if not (isinstance(left, Term) or isinstance(right, Term)):
            self.left = left
            self.right = right
        else:
            if isinstance(left, Term):
                raise ValueError(
                    f'In {self.__class__.__name__}, {left.show()} should be Expr, not {left.__class__.__name__}.')
            if isinstance(right, Term):
                raise ValueError(
                    f'In {self.__class__.__name__}, {right.show()} should be Expr, not {left.__class__.__name__}.')

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.left == other.left and self.right == other.right

    def copy(self):
        return self.__class__(self.left.copy(), self.right.copy())

    def show(self):
        name = self.__class__.__name__
        if name == 'Disjunction':
            output = r' \/ '
        elif name == 'Conjunction':
            output = r' /\ '
        elif name == 'Implication':
            output = r' -> '
        elif name == 'Forall':
            output = r' + '
        elif name == 'Exists':
            output = r' ! '
        else:
            output = name
        return f'({self.left.show()}{output}{self.right.show()})'


class Negation(UnaryOp):
    def introduce_to_antecedent(self):
        return [(self, [], [self.argument])]

    def introduce_to_succedent(self):
        return [(self, [self.argument], [])]


class Implication(BinaryOp):
    def introduce_to_antecedent(self):
        return [(self, [], [self.left]), (self, [self.right], [])]

    def introduce_to_succedent(self):
        return [(self, [self.left], [self.right])]


class Disjunction(BinaryOp):
    def introduce_to_antecedent(self):
        return [(self, [self.left], []), (self, [self.right], [])]

    def introduce_to_succedent(self):
        return [(self, [], [self.left, self.right])]


class Conjunction(BinaryOp):
    def introduce_to_antecedent(self):
        return [(self, [self.left, self.right], [])]

    def introduce_to_succedent(self):
        return [(self, [], [self.left]), (self, [], [self.right])]


index = 0


class Forall(BinaryOp):
    def __init__(self, left, right):
        if isinstance(left, Term) and (left.args is None) and not isinstance(right, Term):
            self.left = left
            self.right = right
            self.doubled = False
        else:
            if not (isinstance(left, Term) and (left.args is None)):
                raise ValueError(
                    f'In {self.__class__.__name__}, {left.show()} should be Var, not {left.__class__.__name__}.')
            if isinstance(right, Term):
                raise ValueError(
                    f'In {self.__class__.__name__}, {right.show()} should be Expr, not {right.__class__.__name__}.')

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            if self.left != other.left:
                self.right = substitute(self.left, other.left, self.right)
                self.left = other.left
            return self.right == other.right

        return False

    def introduce_to_antecedent(self):
        global index
        index += 1
        if not self.doubled:
            self.doubled = True
            return [(self, [self, self], [])]
        else:
            return [(self, [Substitution(Term(f'_v{index}'), substitute(self.left, Term(f'_v{index}'), self.right), 'Forall')], [])]

    def introduce_to_succedent(self):
        global index
        index += 1
        return [(self, [], [substitute(self.left, Term(f'_c{index}'), self.right)])]


class Exists(BinaryOp):
    def __init__(self, left, right):
        if isinstance(left, Term) and (left.args is None) and not isinstance(right, Term):
            self.left = left
            self.right = right
            self.doubled = False
        else:
            raise ValueError(
                f'In {self.__class__.__name__}, {left.show()} should be Var and {right.show()} should be Expr.')

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            if self.left != other.left:
                self.right = substitute(self.left, other.left, self.right)
                self.left = other.left
            return self.right == other.right

        return False

    def introduce_to_antecedent(self):
        global index
        index += 1
        return [(self, [substitute(self.left, Term(f'_c{index}'), self.right)], [])]

    def introduce_to_succedent(self):
        global index
        index += 1
        if not self.doubled:
            self.doubled = True
            return [(self, [], [self, self])]
        else:
            return [(self, [], [Substitution(Term(f'_v{index}'), substitute(self.left, Term(f'_v{index}'), self.right), "Exists")])]


class Substitution(BinaryOp):
    def __init__(self, left, right, kind):
        self.left = left
        self.right = right
        self.kind = kind

    def copy(self):
        return Substitution(self.left.copy(), self.right.copy(), self.kind)


    def show(self):
        if self.kind == 'Exists':
            return f'({self.left.show()} ! {self.right.show()})'
        elif self.kind == 'Forall':
            return f'({self.left.show()} + {self.right.show()})'

    def collision(self):
        global index
        index += 1
        if self.left.name.startswith('_v'):
            new_name = f'_v{index}'
        else:
            new_name = f'_c{index}'
        self.right = substitute(self.left, Term(new_name), self.right)
        self.left = Term(new_name)


def substitute(old, new, expr):
    res = expr.copy()
    if expr == old:
        res = new
    elif isinstance(expr, Term) and expr.args is not None:
        for i in range(0, len(expr.args)):
            res.args[i] = substitute(old, new, expr.args[i])
    elif isinstance(expr, Atom):
        for i in range(0, len(expr.args)):
            res.args[i] = substitute(old, new, expr.args[i])
    elif issubclass(type(expr), UnaryOp):
        res.argument = substitute(old, new, res.argument)
    elif isinstance(expr, Forall) or isinstance(expr, Exists) or isinstance(expr, Substitution):
        if expr.left != old:
            res.right = substitute(old, new, res.right)
        else:
            global index
            index += 1
            if expr.left.name.startswith('_v'):
                res.left = Term(f'_v{index}')
            else:
                res.left = Term(f'_c{index}')
            res.right = substitute(expr.left, res.left, res.right)
            res.right = substitute(old, new, res.right)
    elif issubclass(type(expr), BinaryOp):
        res.left = substitute(old, new, res.left)
        res.right = substitute(old, new, res.right)

    return res
