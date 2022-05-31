from graphql import GraphQLError

class GraphqlException(GraphQLError):

    __slots__ = (
        "message",
        "nodes",
        "stack",
        "original_error",
        "_source",
        "_positions",
        "_locations",
        "path",
        "errors"
    )

    def __init__(
            self,
            message,  # type: str
            errors=None, # type: str
            nodes=None,  # type: Any
            stack=None,  # type: Optional[TracebackType]
            source=None,  # type: Optional[Any]
            positions=None,  # type: Optional[Any]
            locations=None,  # type: Optional[Any]
            path=None,  # type: Union[List[Union[int, str]], List[str], None]
    ):

        # type: (...) -> None
        super(GraphQLError, self).__init__(message, errors)
        self.message = errors
        self.nodes = nodes
        self.stack = stack
        self._source = source
        self._positions = positions
        self._locations = locations
        self.path = path
        return None