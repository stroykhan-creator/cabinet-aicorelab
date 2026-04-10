"""
Безопасный вычислитель выражений (только арифметика и ограниченный набор функций).
"""
import ast, math, operator as op

operators = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Pow: op.pow, ast.USub: op.neg, ast.Mod: op.mod
}

allowed_funcs = {
    'ceil': math.ceil, 'floor': math.floor, 'round': round,
    'min': min, 'max': max, 'abs': abs
}

class EvalError(Exception):
    pass

def _eval(node, variables):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        raise EvalError(f'Unknown variable: {node.id}')
    if isinstance(node, ast.BinOp):
        left = _eval(node.left, variables)
        right = _eval(node.right, variables)
        oper = operators.get(type(node.op))
        if oper is None:
            raise EvalError('Unsupported operator')
        return oper(left, right)
    if isinstance(node, ast.UnaryOp):
        oper = operators.get(type(node.op))
        if oper is None:
            raise EvalError('Unsupported unary operator')
        return oper(_eval(node.operand, variables))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise EvalError('Only simple functions allowed')
        func = allowed_funcs.get(node.func.id)
        if func is None:
            raise EvalError('Function not allowed')
        args = [_eval(a, variables) for a in node.args]
        return func(*args)
    raise EvalError('Unsupported expression')

def safe_eval(expr, variables=None):
    if variables is None:
        variables = {}
    try:
        tree = ast.parse(expr, mode='eval')
        return _eval(tree.body, variables)
    except Exception as e:
        raise EvalError(str(e))
