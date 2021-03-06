from parsec import pparse
import ast


def solve(string):
    expr = pparse(string)
    print()
    print(f'Sequent for {expr.show()}:')
    return solve__internal([], [expr], False, 0)


def pprint(depth, a, b):
    print(f"{depth}) {', '.join(map(lambda x: x.show(), a))} |- {', '.join(map(lambda x: x.show(), b))}")


def solve__internal(antecedent_, succedent_, exists_mode, depth):    
    antecedent = [i for i in antecedent_ if not isinstance(i, ast.Substitution)] + [i for i in antecedent_ if isinstance(i, ast.Substitution)]
    succedent = [i for i in succedent_ if not isinstance(i, ast.Substitution)] + [i for i in succedent_ if isinstance(i, ast.Substitution)]
    
    pprint(depth, antecedent, succedent)

    if contraversial(antecedent, succedent):
        return True

    are_valid_branches_left, exists_mode_1 = check_side(antecedent, succedent, False, exists_mode, depth)
    if are_valid_branches_left is not None:
        return are_valid_branches_left

    are_valid_branches_right, exists_mode_2 = check_side(antecedent, succedent, True, exists_mode_1, depth)
    if are_valid_branches_right is not None:
        return are_valid_branches_right

    if exists_mode_2 or all(map(has_next, antecedent + succedent)):
        return False
    else:
        return True


def check_side(antecedent, succedent, reversed, exists_mode, depth):
 
    iterable = succedent if reversed else antecedent
    
    for i in iterable:
        if isinstance(i, ast.Substitution):

            search_area = antecedent + succedent

            for j in enumerate_available_substitutions(i, search_area):

                antecedent_next = antecedent.copy()
                succedent_next = succedent.copy()

                if reversed:
                    succedent_next.remove(i)
                    succedent_next.insert(0, j)
                else:
                    antecedent_next.remove(i)
                    antecedent_next.insert(0, j)

                are_valid_branches = solve__internal(antecedent_next, succedent_next, reversed, depth + 1)

                if reversed:
                    if are_valid_branches:
                        return True, exists_mode
                elif not exists_mode and not are_valid_branches:
                    return False, exists_mode
                elif exists_mode and are_valid_branches:
                    return True, exists_mode

            return not reversed, exists_mode

        elif not isinstance(i, ast.Atom):
            def check(x): return prepare_and_resolve(
                antecedent, succedent, reversed, exists_mode, x, depth)
            func = i.introduce_to_succedent() if reversed else i.introduce_to_antecedent()
            are_valid_branches = all(map(check, func))

            if not exists_mode and not are_valid_branches:
                return False, exists_mode
            elif are_valid_branches:
                return True, exists_mode
    return None, exists_mode


def prepare_and_resolve(antecedent, succedent, reversed, exists_mode, item, depth):
    i, l, r = item

    antecedent_next = antecedent.copy()
    succedent_next = succedent.copy()

    if reversed:
        succedent_next.remove(i)
    else:
        antecedent_next.remove(i)

    antecedent_next1 = l + antecedent_next
    succedent_next1 = r + succedent_next

    return solve__internal(antecedent_next1, succedent_next1, exists_mode, depth + 1)


def enumerate_available_substitutions(mask, array):
    for i in array:
        for var_new in traverse_expression_tree(i):
            if var_new is not None:
                print(f'Substitute {var_new.show()} instead of {mask.left.show()} in {mask.right.show()}:')
                result = ast.substitute(mask.left, var_new, mask.right)
                yield result
    end_phase = mask.copy()
    end_phase.collision()
    print(f'Substitute {end_phase.left.show()} instead of {mask.left.show()} in {mask.right.show()}:')
    yield end_phase.right


def traverse_expression_tree(source):
    if isinstance(source, ast.Term):
        if not contains(source, None):
            yield source
        if source.args is not None:
            for arg in source.args:
                for item in traverse_expression_tree(arg):
                    if not contains(item, None):
                        yield item
    elif isinstance(source, ast.Atom):
        for arg in source.args:
            for item in traverse_expression_tree(arg):
                yield item
    elif issubclass(type(source), ast.UnaryOp):
        for item in traverse_expression_tree(source.argument):
            yield item
    elif aware_recursion(source):
        for item in traverse_expression_tree(source.right):
            # if isinstance(item, ast.Term) and not item == source.left:
            if not contains(item, source.left):
                yield item
    elif issubclass(type(source), ast.BinaryOp):
        for item in traverse_expression_tree(source.left):
            yield item
        for item in traverse_expression_tree(source.right):
            yield item
    yield None


def contains(box, item):
    if isinstance(box, ast.Term):
        if box.args is None:
            return item == box
        else:
            return any(map(lambda x: contains(x, item), box.args))


def aware_recursion(expr):
    return isinstance(expr, ast.Forall) or isinstance(expr, ast.Exists) or isinstance(expr, ast.Substitution)


def has_next(x):
    return isinstance(x, ast.Atom)


def contraversial(antecedent, succedent):
    return any(map(lambda x: x in antecedent, succedent))
