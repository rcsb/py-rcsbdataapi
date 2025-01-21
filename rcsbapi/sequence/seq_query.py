from typing import Dict, List, Any, Optional
from enum import Enum
from types import MappingProxyType
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
import urllib.parse
import requests

from rcsbapi.const import seq_const
from rcsbapi.config import config
from rcsbapi.sequence import SEQ_SCHEMA


# pylint: disable=useless-parent-delegation
# This should be dynamically populated at some point.
class EnumTypes(Enum):
    SequenceReference = SEQ_SCHEMA.read_enum("SequenceReference")
    FieldName = SEQ_SCHEMA.read_enum("FieldName")
    OperationType = SEQ_SCHEMA.read_enum("OperationType")
    AnnotationReference = SEQ_SCHEMA.read_enum("AnnotationReference")
    GroupReference = SEQ_SCHEMA.read_enum("GroupReference")


@dataclass(frozen=True)
class Query(ABC):
    """Base class for all query types"""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Get dictionary represented query and attributes, skips values of None"""
        request_dict: Dict[str, Any] = {}
        for field in fields(self):
            field_name = field.name
            field_value = getattr(self, field_name)
            field_name = field_name.replace("_", "")
            if field_value:
                # Create an exception for AnnotationFilterInput
                if (
                    isinstance(field_value, list)
                    and all(isinstance(item, AnnotationFilterInput) for item in field_value)
                ):
                    field_value = [filter.to_string() for filter in field_value]
                request_dict[field_name] = field_value
        return request_dict

    def construct_query(self, query_type: str) -> Dict[str, Any]:
        """type check based on the GraphQL schema, then construct the GraphQL query"""
        # Assert attributes exists for mypy.
        # Can't be defined in Query class because
        # attributes without defaults must be defined before those with defaults.
        # Inherited attributes are placed before non-inherited attributes.
        # Possible workaround is making the attributes keyword-only, but I decided against it for now.
        # Issue: https://github.com/python-attrs/attrs/issues/38
        assert hasattr(self, "return_data_list"), \
            f"{self.__class__.__name__} must define 'return_data_list' attribute."
        assert hasattr(self, "suppress_autocomplete_warning"), \
            f"{self.__class__.__name__} must define 'suppress_autocomplete_warning' attribute."

        SEQ_SCHEMA.check_typing(
            query_type=query_type,
            enum_types=EnumTypes,
            args=self.to_dict(),
        )

        query = SEQ_SCHEMA.construct_query(
            query_type=query_type,
            query_args=self.to_dict(),
            return_data_list=self.return_data_list,
            suppress_autocomplete_warning=self.suppress_autocomplete_warning,
        )

        return query

    def exec(self) -> Dict[str, Any]:
        """execute given query and return JSON response"""
        # Assert attribute exists for mypy
        assert hasattr(self, "_query"), \
            f"{self.__class__.__name__} must define '_query' attribute."
        response_json = requests.post(
            json=dict(self._query),
            url=seq_const.API_ENDPOINT + "/graphql",
            timeout=config.DATA_API_TIMEOUT
        ).json()
        self._parse_gql_error(response_json)
        return dict(response_json)

    def get_editor_link(self) -> str:
        """Get link to GraphiQL editor with given query populated"""
        editor_base_link = str(seq_const.API_ENDPOINT) + "/graphiql" + "/index.html?query="
        assert hasattr(self, "_query")  # for mypy
        return editor_base_link + urllib.parse.quote(str(self._query["query"]))

    def _parse_gql_error(self, response_json: Dict[str, Any]) -> None:
        """Look through responses to see if there are errors. If so, throw an HTTP error, """
        if "errors" in response_json.keys():
            error = response_json["errors"][0]
            raise requests.HTTPError(
                f"\n{error["message"]}\n"
                f"  Run <query object name>.get_editor_link() to get a link to GraphiQL editor with query"
            )


@dataclass(frozen=True)
class Alignments(Query):
    """
    Get sequence alignments

        from_ (str): From which query sequence database
        to (str): To which query sequence database
        queryId (str): Database sequence identifier
        return_data_list (List[str]): Requested data fields
        range (Optional, List[]): Optional integer list to filter alignments to a particular region
        suppress_autocomplete_warning (bool, optional): Suppress warning message about field path autocompletion. Defaults to False.
        _query (MappingProxyType): Attribute for storing GraphQL query
    """
    from_: str
    to: str
    queryId: str
    return_data_list: List[str]
    range: Optional[List[int]] = None
    suppress_autocomplete_warning: bool = False
    _query: MappingProxyType[str, Any] = MappingProxyType({})
    """
    `offset` and `first` are field arguments (currently the only ones).
    Making them class attributes (below) would not work if there
    were redundant field arg names. Other options:
    1. Use a string in `return_data_list` and parse later
            return_data_list = ["target_alignments(first:0, offset:5)"]
    2. Create an attribute `field_args` and pass in args as a dict
            field_args = {"target_alignments": {first:0, offset:5}, ...}
    """
    offset: Optional[int] = None
    first: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()

    def __post_init__(self) -> None:
        query = super().construct_query("alignments")
        object.__setattr__(self, "_query", query)


@dataclass(frozen=True)
class Annotations(Query):
    """
    Get sequence annotations

        queryId (str): Database sequence identifier
        sources (List[str]): List defining the annotation collections to be requested
        reference (SequenceReference): Query sequence database
        return_data_list (List[str]): Requested data fields
        filters (list["AnnotationFilterInput"], optional): Optional annotation filter by type or target identifier
        range: (List[int], optional): Optional integer list to filter annotations to a particular region
        suppress_autocomplete_warning (bool, optional): Suppress warning message about field path autocompletion. Defaults to False.
        _query (MappingProxyType): Attribute for storing GraphQL query
    """
    queryId: str
    sources: List[str]
    reference: str
    return_data_list: List[str]
    filters: Optional[list["AnnotationFilterInput"]] = None
    range: Optional[List[int]] = None
    suppress_autocomplete_warning: bool = False
    _query: MappingProxyType[str, Any] = MappingProxyType({})

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()

    def __post_init__(self) -> None:
        query = super().construct_query("annotations")
        object.__setattr__(self, "_query", query)


@dataclass(frozen=True)
class GroupAlignments(Query):
    """
    Get alignments for structures in groups

        queryId (str): Database sequence identifier for group
        return_data_list (list[str]): Requested data fields
        filter (list[str], optional): Optional string list of allowed identifiers for group members
        suppress_autocomplete_warning (bool, optional): Suppress warning message about field path autocompletion. Defaults to False.
        _query (MappingProxyType): Attribute for storing GraphQL query
    """
    group: str
    groupId: str
    return_data_list: list[str]
    filter: Optional[list[str]] = None
    suppress_autocomplete_warning: bool = False
    _query: MappingProxyType[str, Any] = MappingProxyType({})
    offset: Optional[int] = None
    first: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()

    def __post_init__(self) -> None:
        query = super().construct_query("group_alignments")
        object.__setattr__(self, "_query", query)


@dataclass(frozen=True)
class GroupAnnotations(Query):
    """
    Get annotations for structures in groups

        group (GroupReference): Query sequence database
        groupId (str): Database sequence identifier for group
        sources (list[AnnotationReference]): List defining the annotation collections to be requested
        return_data_list (list[str]): Requested data fields
        filters (list[AnnotationFilterInput]): Optional annotation filter by type or target identifier
        suppress_autocomplete_warning (bool, optional): Suppress warning message about field path autocompletion. Defaults to False.
        _query (MappingProxyType): Attribute for storing GraphQL query
    """
    group: str
    groupId: str
    sources: List[str]
    return_data_list: list[str]
    filters: Optional[List["AnnotationFilterInput"]] = None
    suppress_autocomplete_warning: bool = False
    _query: MappingProxyType[str, Any] = MappingProxyType({})

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()

    def __post_init__(self) -> None:
        query = super().construct_query("group_annotations")
        object.__setattr__(self, "_query", query)


@dataclass(frozen=True)
class GroupAnnotationsSummary(Query):
    """
    Get a positional summary of group annotations

        group (GroupReference): Query sequence database
        groupId (str): Database sequence identifier for group
        sources (list[AnnotationReference]): List defining the annotation collections to be requested
        return_data_list (list[str]): Request data fields
        filters (list[AnnotationFilterInput], optional): Optional annotation filter by type or target identifier
        suppress_autocomplete_warning (bool, optional): Suppress warning message about field path autocompletion. Defaults to False.
        _query (MappingProxyType): Attribute for storing GraphQL query
    """
    group: str
    groupId: str
    sources: List[str]
    return_data_list: list[str]
    filters: Optional[List["AnnotationFilterInput"]] = None
    suppress_autocomplete_warning: bool = False
    _query: MappingProxyType[str, Any] = MappingProxyType({})

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()

    def __post_init__(self) -> None:
        query = super().construct_query("group_annotations_summary")
        object.__setattr__(self, "_query", query)


class AnnotationFilterInput:
    """
    filter used to select which annotations will be retrieved
    """

    def __init__(
        self,
        field: str,
        operation: str,
        values: List[str],
        source: Optional[str] = None,
    ):
        """
        Args:
            field (FieldName): Defines the field to be compared
            operation (OperationType): Defines the comparison method
            values (List[str]): List of allowed values
            source (AnnotationReference, optional): Only features with the same annotation collections will be filtered
        """
        self.field = field
        self.operation = operation
        self.values = values
        self.source = source

    def to_string(self) -> str:
        """Generate string to insert in GraphQL query based on GraphQL schema"""

        input_field_specs: list[Any] = []
        for arg_dict in SEQ_SCHEMA._root_dict["annotations"]:
            if arg_dict["name"] == "filters":
                input_field_specs = arg_dict["inputFields"]
        assert len(input_field_specs) > 0, '"filters" key not found in arg_dict'

        args = set()
        for input_field in input_field_specs:
            field_name = input_field["name"]
            if getattr(self, field_name) is None:
                continue
            if (
                (input_field["type"]["ofType"] is not None)
                and (input_field["type"]["ofType"]["kind"] == "LIST")
            ):
                if input_field["type"]["ofType"]["ofType"]["ofType"]["name"] == "String":
                    # If type is string, add list with double quotes around each item
                    args.add(f"{field_name}: {str(getattr(self, field_name)).replace("'", '"')}")
                else:
                    # If type isn't string, remove single quotes
                    args.add(f"{field_name}: {str(getattr(self, field_name)).replace("'", "")}")
            elif (
                (input_field["type"]["kind"] == "ENUM")
                or (input_field["type"]["ofType"]["kind"] == "ENUM")
            ):
                # If type is ENUM, remove single quotes
                args.add(f"{field_name}: {str(getattr(self, field_name)).replace("'", "")}")
            else:
                raise NotImplementedError("Unsupported type in schema dictionary")
        str_filter = str(args).replace("'", "")
        return str_filter
