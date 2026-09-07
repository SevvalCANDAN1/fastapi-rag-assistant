"""Safe calculator tool for the RAG assistant."""
import ast
import operator

from langchain_core.tools import tool


# Allowed AST operators -> their Python implementations.
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_MAX_EXPRESSION_LENGTH = 200
_MAX_AST_DEPTH = 20


def _eval_node(node, depth=0):
    """Recursively evaluate an AST node using only allowed operations."""
    if depth > _MAX_AST_DEPTH:
        raise ValueError("Expression too deeply nested")

    # Top-level expression wrapper.
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, depth + 1)

    # Numeric literal (Python 3.8+ uses Constant).
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    # Legacy numeric literal for older Python versions.
    if isinstance(node, ast.Num):
        return node.n

    # Binary operation: e.g. 2 + 3 * 4
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _eval_node(node.left, depth + 1)
        right = _eval_node(node.right, depth + 1)
        return _ALLOWED_OPS[op_type](left, right)

    # Unary operation: e.g. -5, +3
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        operand = _eval_node(node.operand, depth + 1)
        return _ALLOWED_OPS[op_type](operand)

    # Anything else (Name, Call, Attribute, Import, etc.) is rejected.
    raise ValueError(f"Unsupported expression element: {type(node).__name__}")


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Use this when the user asks for arithmetic, percentages, totals, averages,
    or any numeric calculation. The expression may contain only numbers, +, -,
    *, /, ** and parentheses.

    Examples:
        "2 + 3 * 4" -> "14"
        "(100 - 20) / 5" -> "16.0"
        "2 ** 10" -> "1024"
    """
    if not expression or not isinstance(expression, str):
        return "Error: expression must be a non-empty string"

    if len(expression) > _MAX_EXPRESSION_LENGTH:
        return "Error: expression too long"

    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree)
        return str(result)
    except (SyntaxError, ValueError) as e:
        return f"Error: invalid expression ({e})"
    except ZeroDivisionError:
        return "Error: division by zero"
    except Exception as e:
        return f"Error: could not evaluate expression ({e})"
