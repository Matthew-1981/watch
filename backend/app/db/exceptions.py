class ORMError(Exception):
    pass


class OperationError(ORMError):
    pass


class ConstraintError(ORMError):
    pass
