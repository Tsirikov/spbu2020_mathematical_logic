from rply import ParserGenerator
from ast import *

pg = ParserGenerator(
    # A list of all token names, accepted by the parser.
    ['VAR', 'OPEN_PAREN', 'CLOSE_PAREN',
     'SEMI_COLON', 'CONJ', 'DISJ', 'NEG', 'EXIST', 'ALL', 'SUBSTITUTION', 'IMP'
     ],
    # A list of precedence rules with ascending precedence, to
    # disambiguate ambiguous production rules.
    precedence=[
        ('right', ['IMP']),
        ('left', ['DISJ']),
        ('left', ['CONJ']),
        ('left', ['NEG', 'EXIST', 'ALL', 'SUBSTITUTION'])
    ]
)


@pg.production('expression : VAR')
def expression_variable(p):
    # p is a list of the pieces matched by the right hand side of the
    # rule
    return Var(p[0].getstr())


@pg.production('expression : OPEN_PAREN expression CLOSE_PAREN')
def expression_parens(p):
    return p[1]


@pg.production('expression : NEG expression')
def expression_un_op(p):
    op = p[0]
    value = p[1]
    if op.gettokentype() == 'NEG':
        return Negation(value)
    else:
        raise AssertionError('Oops, this should not be possible!')


@pg.production('expression : ALL expression expression')
@pg.production('expression : EXIST expression expression')
def expression_fst_bin_op(p):
    left = p[1]
    right = p[2]
    if p[0].gettokentype() == 'ALL':
        return Forall(left, right)
    elif p[0].gettokentype() == 'EXIST':
        return Exists(left, right)


@pg.production('expression : expression IMP expression')
@pg.production('expression : expression DISJ expression')
@pg.production('expression : expression CONJ expression')
def expression_bin_op(p):
    left = p[0]
    right = p[2]
    if p[1].gettokentype() == 'IMP':
        return Imp(left, right)
    elif p[1].gettokentype() == 'DISJ':
        return Disj(left, right)
    elif p[1].gettokentype() == 'CONJ':
        return Conj(left, right)
    elif p[1].gettokentype() == 'ALL':
        return Forall(left, right)
    else:
        raise AssertionError('Oops, this should not be possible!')


parser = pg.build()