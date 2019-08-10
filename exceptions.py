class ParseError(ValueError):
    """The roll expression was malformed as to prevent parsing into an expression tree."""
    pass


class EvaluationError(RuntimeError):
    """The roll could not be evaluated."""
    pass


class ArgumentValueError(EvaluationError):
    """The value of an expression cannot be used."""
    pass


class ArgumentTypeError(EvaluationError):
    """An expression in the roll is of the wrong type."""
    pass


class InputTypeError(EvaluationError):
    """You passed the wrong thing into the entry point function."""
    pass