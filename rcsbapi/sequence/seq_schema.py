"""Fetching and Parsing API's GraphQL schema."""

from __future__ import annotations
import logging
import json
from typing import Any
from pathlib import Path
import requests
from graphql import build_client_schema
import rustworkx as rx

from rcsbapi.const import seq_const
from rcsbapi.config import config

use_networkx: bool = False
# Below section and parts of code involving networkx are commented out
# May implement graph construction through networkx at a later point
# try:
#     import rustworkx as rx

#     logging.info("Using  rustworkx")
# except ImportError:
#     use_networkx = True

logger = logging.getLogger(__name__)


class FieldNode:
    """
    Node representing GraphQL field.

        name (str): field name
        description (str): field description
        redundant (bool): whether field name is redundant in schema
        kind (str): "LIST", "SCALAR, or "OBJECT"
        of_kind (str): If "LIST", whether list of "SCALAR" or "OBJECT"
        type (str): GraphQL schema type (ex: CoreEntry)
        index (int): graph index
    """

    def __init__(self, kind: str, node_type: str, name: str, description: str, args: list[dict[str, str | None]]) -> None:
        """
        Initialize FieldNodes.

        Args:
            kind (str): GraphQL kind, can be "OBJECT", "SCALAR", "LIST"
            node_type (str): If applicable, the GraphQL type returned by the field
            name (str): Name of field
            description (str): Description of field
        """
        self.name: str = name
        self.description: str = description
        self.redundant: bool = False
        self.kind: str = kind
        self.of_kind: str = ""
        self.type: str = node_type
        self.args: list[dict[str, str | None]] = args
        self.index: None | int = None

    def __str__(self) -> str:
        """FieldNode as a string."""
        return f"Field Object name: {self.name}, Kind: {self.kind}, Type: {self.type}, Index if set: {self.index}, Description: {self.description}"

    def set_index(self, index: int) -> None:
        """
        Set index that is associated with the FieldNode.

        Args:
            index (int): index of node in schema_graph
        """
        self.index = index

    def set_of_kind(self, of_kind: str) -> None:
        """
        Only applicable if kind is LIST. Describes the GraphQL kind of the list (OBJECT, SCALAR).

        Args:
            of_kind (str): GraphQL kind of the list returned by a node (a LIST can be "of_kind" OBJECT)
        """
        self.of_kind = of_kind


class TypeNode:
    """Class for nodes representing GraphQL Types in the schema graph."""

    def __init__(self, name: str) -> None:
        """
        Initialize TypeNodes.

        Args:
            name (str): name of GraphQL type (ex: CoreEntry)
        """
        self.name = name
        self.index: None | int = None
        self.field_list: list[FieldNode] = []

    def set_index(self, index: int) -> None:
        """
        Set index that is associated with the TypeNode.

        Args:
            index (int): index of node in schema_graph
        """
        self.index = index

    def set_field_list(self, field_list: list[FieldNode]) -> None:
        """List of FieldNodes associated with the GraphQL type.

        Args:
            field_list (Union[None, list[FieldNode]]): list of FieldNodes
        """
        self.field_list = field_list


class SeqSchema:
    """GraphQL schema defining available fields, types, and how they are connected."""

    def __init__(self) -> None:
        """GraphQL schema defining available fields, types, and how they are connected."""
        self.pdb_url: str = seq_const.API_ENDPOINT + "/graphql"
        self.timeout: int = config.DATA_API_TIMEOUT  # TODO: change?
        self.schema: dict[str, Any] = self.fetch_schema()
        """JSON resulting from full introspection of the GraphQL schema"""

        self._use_networkx: bool = use_networkx
        # if use_networkx:
        #     self._schema_graph = nx.DiGraph()
        #     """NetworkX graph representing the GraphQL schema"""
        # else:
        #     self._schema_graph = rx.PyDiGraph()
        #     """rustworkx graph representing the GraphQL schema"""

        self._type_to_idx_dict: dict[str, int] = {}
        self._field_to_idx_dict: dict[str, list[int]] = {}
        """Dict where keys are field names and values are lists of indices.
        Indices of redundant fields are appended to the list under the field name. (ex: {id: [[43, 116, 317...]})"""
        self._root_introspection = self._request_root_types()
        """Request root types of the GraphQL schema and their required arguments"""
        self._client_schema = build_client_schema(self.schema["data"])
        """GraphQLSchema object from graphql package, used for query validation"""
        self._type_fields_dict: dict[str, dict[Any, Any]] = self._construct_type_dict()
        """Dict where keys are type names and the values are their associated fields"""
        self._field_names_list = self._construct_name_list()
        """list of all field names"""
        self._root_dict: dict[str, list[dict[str, Any]]] = self._construct_root_dict()
        self._schema_graph: rx.PyDiGraph[FieldNode | TypeNode, None | int] = rx.PyDiGraph()
        self._schema_graph = self._recurse_build_schema(self._schema_graph, "Query")
        self._root_to_idx: dict[str, int] = self._make_root_to_idx()
        self._field_names_list = self._construct_name_list()
        """Dict where keys are field names and values are indices. Redundant field names are represented as <parent_field_name>.<field_name> (ex: {entry.id: 1452})"""

    def _request_root_types(self) -> dict[str, Any]:
        """
        Make an introspection query to get information about schema's root types.

        Returns:
            Dict: JSON response of introspection request
        """
        root_query = {
            "query": """query IntrospectionQuery{ __schema{ queryType{ fields{ name args
        { name description type{ kind ofType{ name kind ofType{ inputFields {name type { kind ofType { name kind ofType { ofType { kind name ofType {kind name}} } } } }
        kind name ofType{name kind} } } } } } } } }"""
        }
        response = requests.post(headers={"Content-Type": "application/json"}, json=root_query, url=self.pdb_url, timeout=self.timeout)
        return dict(response.json())

    def _construct_root_dict(self) -> dict[str, list[dict[str, Any]]]:
        """Build a dictionary to organize information about schema root types.

        Returns:
            dict[str, list[Dict]]: Dict where keys are the type names.
            Values are lists of dictionaries with information about arguments.

            ex: {"alignments": [{'name': 'from', 'description': 'Query sequence database'...}, ...], ...}
        """
        response = self._root_introspection
        root_dict: dict[str, list[dict[str, str]]] = {}
        root_fields_list = response["data"]["__schema"]["queryType"]["fields"]
        for name_arg_dict in root_fields_list:
            root_name = name_arg_dict["name"]
            arg_dict_list = name_arg_dict["args"]
            for arg_dict in arg_dict_list:
                arg_name = arg_dict["name"]
                arg_description = arg_dict["description"]
                arg_kind = arg_dict["type"]["kind"]
                arg_of_kind = ""
                arg_of_type = ""
                if arg_kind in {"LIST", "NON_NULL"}:
                    arg_of_kind = arg_dict["type"]["ofType"]["kind"]
                    arg_of_type = self._find_type_name(arg_dict["type"]["ofType"])
                input_fields = ""
                if ("ofType" in arg_dict["type"]["ofType"] and arg_dict["type"]["ofType"]["ofType"] is not None) and (
                    "inputFields" in arg_dict["type"]["ofType"]["ofType"] and arg_dict["type"]["ofType"]["ofType"]["inputFields"] is not None
                ):
                    input_fields = arg_dict["type"]["ofType"]["ofType"]["inputFields"]
                if root_name not in root_dict:
                    root_dict[root_name] = []
                root_dict[root_name].append(
                    {"name": arg_name, "description": arg_description, "kind": arg_kind, "ofKind": arg_of_kind, "ofType": arg_of_type, "inputFields": input_fields}
                )
        return root_dict

    def fetch_schema(self) -> dict[str, Any]:
        """
        Make an introspection query to get full Data API schema. Also found in resources folder as "seq_api_schema.json".

        Returns:
            Dict: JSON response of introspection request
        """
        query = {
            "query": """query IntrospectionQuery { __schema
            { queryType { name } types { kind name description fields(includeDeprecated: true)
            { name description args { name description type { kind name ofType { kind name ofType
            { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType
            { kind name } } } } } } } } defaultValue } type { kind name ofType { kind name ofType { kind name
            ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } } }
            isDeprecated deprecationReason } inputFields { name description type { kind name ofType
            { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType
            { kind name ofType { kind name } } } } } } } } defaultValue } interfaces { kind name ofType
            { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType
            { kind name } } } } } } } } enumValues(includeDeprecated: true) { name description isDeprecated deprecationReason }
            possibleTypes { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType
            { kind name ofType { kind name ofType { kind name } } } } } } } } } directives { name description locations args
            { name description type { kind name ofType { kind name ofType { kind name ofType { kind name ofType
            { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } } } defaultValue } } }}"""
        }
        schema_response = requests.post(headers={"Content-Type": "application/json"}, json=query, url=self.pdb_url, timeout=self.timeout)
        if schema_response.status_code == 200:
            return dict(schema_response.json())
        logger.info("Loading data schema from file")
        current_dir = Path(Path(__file__).resolve()).parent
        json_file_path = Path(current_dir) / "resources" / "seq_api_schema.json"
        with Path.open(json_file_path, encoding="utf-8") as schema_file:
            return dict(json.load(schema_file))

    def _construct_type_dict(self) -> dict[str, dict[str, dict[str, str]]]:
        """Construct dictionary of GraphQL types and their associated fields.

        Args:
            schema (Dict): GraphQL schema

        Returns:
            dict[str, dict[str, dict[str, str]]]: Dict where keys are GraphQL types and values are lists of field names
        """
        all_types_dict: dict[Any, Any] = self.schema["data"]["__schema"]["types"]
        type_fields_dict = {}
        for each_type_dict in all_types_dict:
            type_name = str(each_type_dict["name"])
            fields = each_type_dict["fields"]
            field_dict = {}
            if fields is not None:
                for field in fields:
                    info_dict = field["type"]
                    info_dict["args"] = field["args"]
                    field_dict[str(field["name"])] = info_dict
            type_fields_dict[type_name] = field_dict
        return type_fields_dict

    def _construct_name_list(self) -> list[str]:
        """Construct a list of all field names in the schema. Used to determine whether a field is known or redundant.

        Returns:
            list[str]: list of all fields
        """
        field_names_list = []
        for type_name, field_dict in self._type_fields_dict.items():
            if "__" in type_name:
                continue
            for field_name in field_dict:
                field_names_list.append(field_name)  # noqa: PERF402
        return field_names_list

    def make_type_subgraph(self, type_name: str) -> TypeNode:
        """Make a subgraph of only one type and its associated fields.

        Args:
            type_name (str): name of the type for which to construct subgraph

        Returns:
            TypeNode: returns TypeNode constructed from type_name
        """
        field_name_list = self._type_fields_dict[type_name].keys()
        field_node_list = []
        type_node = self._make_type_node(type_name)
        for field_name in field_name_list:
            parent_type_name = type_name
            field_node = self._make_field_node(parent_type_name, field_name)
            field_node_list.append(field_node)
        type_node.set_field_list(field_node_list)
        return type_node

    def _recurse_build_schema(
        self,
        schema_graph: rx.PyDiGraph[FieldNode | TypeNode, None | int],
        type_name: str
    ) -> rx.PyDiGraph[FieldNode | TypeNode, None | int]:
        """Build the API schema by iterating through the fields of the given type and building subgraphs for each one recursively until a scalar (leaf) is reached.

        Args:
            schema_graph (rx.PyDiGraph): graph object to build into
            type_name (str): name of type whose fields will be iterated through

        Returns:
            rx.PyDiGraph: returns complete schema graph object
        """
        type_node = self.make_type_subgraph(type_name)
        for field_node in type_node.field_list:
            assert isinstance(field_node.index, int)  # noqa: S101 (assert needed for mypy)
            if field_node.kind == "SCALAR" or field_node.of_kind == "SCALAR":
                continue
            type_name = field_node.type
            if type_name in self._type_to_idx_dict:
                type_index = self._type_to_idx_dict[type_name]
                if use_networkx:
                    schema_graph.add_edge(field_node.index, type_index, 1)
                else:
                    schema_graph.add_edge(field_node.index, type_index, 1)
            else:
                self._recurse_build_schema(schema_graph, type_name)
                type_index = self._type_to_idx_dict[type_name]
                # if self._use_networkx:
                #     schema_graph.add_edge(field_node.index, type_index, 1)
                if self._use_networkx is False:
                    schema_graph.add_edge(field_node.index, type_index, 1)
        return schema_graph

    # def _apply_weights(self, root_type_list: list[str], weight: int) -> None:
    #     """applies weight to all edges from a root TypeNode to FieldNodes

    #     Args:
    #         root_type_list (list[str]): list of root fields to apply weights to
    #             ex: "CoreEntry", "CoreAssembly"
    #         weight (int): integer weight to apply to edges from specified type(s)
    #     """
    #     for root_type in root_type_list:
    #         node_idx = self._type_to_idx_dict[root_type]
    #         if use_networkx is False:
    #             assert isinstance(self._schema_graph, rx.PyDiGraph)
    #             out_edge_list = self._schema_graph.incident_edges(node_idx)
    #             for edge_idx in out_edge_list:
    #                 self._schema_graph.update_edge_by_index(edge_idx, weight)
    #         # else:
    #         #     out_edge_list = self._schema_graph.edges(node_idx)
    #         #     nx.set_edge_attributes(
    #         #         self._schema_graph,
    #         #         {edge_tuple: {"weight": weight} for edge_tuple in out_edge_list}
    #         #     )

    def _make_type_node(self, type_name: str) -> TypeNode:
        type_node = TypeNode(type_name)
        # if self._use_networkx:
        #     index = len(self._schema_graph.nodes)
        #     self._schema_graph.add_node(index, type_node=type_node)
        # if self._use_networkx is False:
        index = self._schema_graph.add_node(type_node)
        self._type_to_idx_dict[type_name] = index
        type_node.set_index(index)
        return type_node

    def _make_field_node(self, parent_type: str, field_name: str) -> FieldNode:
        kind = self._type_fields_dict[parent_type][field_name]["kind"]
        field_type_dict: dict[str, Any] = self._type_fields_dict[parent_type][field_name]
        return_type = self._find_type_name(field_type_dict)
        description = self._find_description(parent_type, field_name)
        args = [self._make_args_dict(args) for args in self._type_fields_dict[parent_type][field_name]["args"]]
        field_node = FieldNode(kind, return_type, field_name, description, args)
        if kind in {"LIST", "NON_NULL"}:
            of_kind = self._find_kind(field_type_dict)
            field_node.set_of_kind(of_kind)
        parent_type_index = self._type_to_idx_dict[parent_type]
        # if self._use_networkx:
        #     index = len(self._schema_graph.nodes
        #     self._schema_graph.add_node(index, field_node=field_node)
        #     self._schema_graph.add_edge(parent_type_index, index, weight=1)
        # if self._use_networkx is False:
        if field_node.kind == "SCALAR" or field_node.of_kind == "SCALAR":
            index = self._schema_graph.add_child(parent_type_index, field_node, 1)
        else:
            index = self._schema_graph.add_child(parent_type_index, field_node, 1)
        if self._field_names_list.count(field_name) > 1:
            field_node.redundant = True
        field_node.set_index(index)
        assert isinstance(field_node.index, int)  # noqa: S101 (needed for mypy)
        if field_name not in self._field_to_idx_dict:
            self._field_to_idx_dict[field_name] = [field_node.index]
        else:
            self._field_to_idx_dict[field_name].append(field_node.index)

        return field_node

    def _find_kind(self, field_dict: dict[str, Any]) -> Any | str:  # noqa: ANN401
        if field_dict["name"] is not None:
            return field_dict["kind"]
        return self._find_kind(field_dict["ofType"])

    def _find_type_name(self, field_dict: dict[str, Any]) -> Any | str:  # noqa: ANN401
        if field_dict:
            if field_dict["name"] is not None:
                return field_dict["name"]
            return self._find_type_name(field_dict["ofType"])
        return ""

    def _find_description(self, type_name: str, field_name: str) -> str:
        for type_dict in self.schema["data"]["__schema"]["types"]:
            if type_dict["name"] == type_name:
                for field in type_dict["fields"]:
                    if (field["name"] == field_name) and isinstance(field["description"], str):
                        return field["description"]
        return ""

    def _make_args_dict(self, args: dict[str, Any]) -> dict[str, str | None]:
        name = args["name"]
        ofType = args["type"]["ofType"]
        kind = args["type"]["kind"]
        # ofKind is only needed for Lists.
        # Currently no field args are lists. If that changes, this code may need correcting
        ofKind = None
        if (ofType) and ("kind" in ofType):
            ofKind = args["type"]["ofType"]["kind"]

        return {"name": name, "ofType": ofType, "kind": kind, "ofKind": ofKind}

    def _make_root_to_idx(self) -> dict[str, int]:
        root_to_idx: dict[str, int] = {}
        # Assumes 0 is the index for root Query node.
        # Remains true as long as graph building starts from there
        for root_node in self._schema_graph.successors(0):
            assert isinstance(root_node.index, int)  # for mypy
            root_to_idx[root_node.name] = root_node.index
        return root_to_idx

    def _get_descendant_fields(self, node_idx: int, visited: None | set[int] = None) -> list[int | dict[int, Any]]:
        if visited is None:
            visited = set()

        field_name = self._idx_to_name(node_idx)
        result: list[int | dict[int, Any]] = []
        children_idx = list(self._schema_graph.neighbors(node_idx))

        for idx in children_idx:
            if idx in visited:
                error_msg = f"{field_name} in return_data_list is too general, unable to autocomplete query.\n" "Please request a more specific field."
                raise ValueError(error_msg)

            visited.add(idx)
            child_data = self._schema_graph[idx]
            assert isinstance(child_data.index, int)  # noqa: S101 (needed for mypy)

            if isinstance(child_data, FieldNode):
                child_descendants = self._get_descendant_fields(idx, visited)
                # If further subfields append as dictionary. ex: {field index: [subfield1, subfield2, ...]}
                if child_descendants:
                    result.append({child_data.index: child_descendants})
                # If scalar, append index
                else:
                    result.append(child_data.index)
            elif isinstance(child_data, TypeNode):
                type_descendants = self._get_descendant_fields(idx, visited)
                # If further subfields, append the list of descendants (indices and index dicts)
                if type_descendants:
                    result.extend(type_descendants)
                # Skips appending if no further subfields (ENUMS)
        return result

    def return_fields_to_paths(
        self,
        start_idx: int,
        query_type: str,
        return_data_list: list[str],
    ) -> dict[int, list[int]]:
        return_data_paths: dict[int, list[int]] = {}
        complete_path: int = 0

        for field in return_data_list:
            # Generate list of all possible paths to the final requested field. Try to find matching sequence to user input.
            path_list = field.split(".")
            possible_paths = self.find_paths(query_type, path_list[-1])
            matching_paths: list[str] = []
            for path in possible_paths:
                possible_path_list = path.split(".")
                possible_path_list.insert(0, str(query_type))

                # If there is an exact path match,
                # the path is fully specified and other possible_paths can be removed and loop can stop.
                # Iterate complete path, so warning can be raised if autocompletion is used
                path_list_with_input = [query_type, *path_list]
                if possible_path_list in (path_list, path_list_with_input):
                    matching_paths = [".".join(possible_path_list)]
                    complete_path += 1
                    break
                # Else, check for matching path segments.
                for i in range(len(possible_path_list)):
                    if possible_path_list[i: i + len(path_list)] == path_list:
                        matching_paths.append(".".join(possible_path_list))

            idx_paths: list[list[int]] = []
            if len(matching_paths) > 0:
                for path in matching_paths:
                    idx_paths.extend(self._parse_dot_path(path))

            # remove paths not beginning with input_type
            full_idx_paths: list[list[int]] = list(idx_paths)
            input_type_idx = self._root_to_idx[query_type]
            for idx_path in idx_paths:
                if idx_path[0] != input_type_idx:
                    full_idx_paths.remove(idx_path)
            idx_paths = full_idx_paths

            if len(idx_paths) > 1:
                # Print error message that doesn't include input_type at beginning
                # But keep input_type in matching_paths for query construction reasons
                num_paths_to_print = 10
                path_choice_msg = "  " + "\n  ".join([".".join(path.split(".")[1:]) for path in matching_paths[:10]])
                len_path = min(len(matching_paths), num_paths_to_print)

                if len(matching_paths) > num_paths_to_print:
                    error_msg = (
                        f'Given path "{field}" not specific enough. Use one or more of these paths in return_data_list argument:\n\n'
                        f"{len_path} of {len(matching_paths)} possible paths:\n"
                        f"{path_choice_msg}"
                        f"\n  ...\n\n"
                        f"For all paths run:\n"
                        f"  from rcsbapi.data import Schema\n"
                        f"  schema = Schema()\n"
                        f'  schema.find_paths("{query_type}", "{path_list[-1]}")'
                    )
                    raise ValueError(error_msg)

                error_msg = (
                    f'Given path  "{field}" not specific enough. Use one or more of these paths in return_data_list argument:\n\n'
                    f"{len_path} of {len(matching_paths)} possible paths:\n"
                    f"{path_choice_msg}"
                )
                raise ValueError(error_msg)

            # If path isn't in possible_paths_list, try using the graph to validate the path. Allows for queries with loops and paths that have repeated nodes.
            if len(idx_paths) == 0:
                possible_dot_paths: list[list[int]] = self._parse_dot_path(field)  # Throws an error if path is invalid
                shortest_full_paths: list[list[int]] = self._compare_paths(start_idx, possible_dot_paths)
                if len(shortest_full_paths) > 1:
                    shortest_name_paths = [".".join([self._idx_to_name(idx) for idx in path[1:] if isinstance(self._schema_graph[idx], FieldNode)]) for path in shortest_full_paths]
                    shortest_name_paths.sort()
                    path_choice_msg = ""
                    for name_path in shortest_name_paths:
                        path_choice_msg += "  " + name_path + "\n"
                    error_msg = (
                        "Given path not specific enough. Use one or more of these paths in return_data_list argument:\n\n"
                        f"{path_choice_msg}\n"
                        "Please note that this list may not be complete. "
                        "If looking for a different path, you can search the interactive editor's documentation explorer: https://data.rcsb.org/graphql/index.html"
                    )
                    raise ValueError(error_msg)
                idx_paths = shortest_full_paths
            final_idx: int = idx_paths[0][-1]
            shortest_path: list[int] = idx_paths[0][1:]
            return_data_paths[final_idx] = shortest_path
        return return_data_paths

    def _format_args(self, arg_dict: dict[str, list[Any]] | dict[str, str], input_value: str | list[str] | int) -> str:
        """Add double quotes or omit quotes around a single GraphQL argument.

        Args:
            arg_dict (Dict[str, str]): dictionary with information about the argument
            input_value (str): input value of the argument

        Returns:
            str: returns input value formatted with quotes, no quotes, or as a list
        """
        format_arg = ""
        if arg_dict["kind"] == "LIST" or arg_dict["ofKind"] == "LIST":
            if arg_dict["ofType"] == "String":
                # Add double quotes around each item
                format_arg += f'{arg_dict["name"]}: {str(input_value).replace("'", '"')}'
            else:
                # Remove single quotes if not string
                format_arg += f'{arg_dict["name"]}: {str(input_value).replace("'", "")}'
        elif arg_dict["ofType"] == "String":
            # If arg type is string, add double quotes around value
            format_arg += f'{arg_dict["name"]}: "{input_value}"'
        else:
            assert isinstance(input_value, str) or isinstance(input_value, int)
            format_arg += f"{arg_dict["name"]}: {input_value}"
        return format_arg

    def _find_idx_path(self, dot_path: list[str], idx_list: list[int], node_idx: int) -> list[int]:
        """Function that recursively finds a list of indices that matches a list of field names.

        Args:
            dot_path (list[str]): list of field names to find index matches for
            idx_list (list[int]): list of matching indices, appended to as matches are found during recursion
            node_idx (int): index to be searched for a child node matching the next field name

        Returns:
            list[int]: a list of indices matching the given dot_path. If no path is found, an empty list is returned.
        """
        if len(dot_path) == 0:
            idx_list.append(node_idx)
            return idx_list
        if (getattr(self._schema_graph[node_idx], "kind") == "SCALAR") or (getattr(self._schema_graph[node_idx], "of_kind") == "SCALAR"):
            return self._find_idx_path(dot_path[1:], idx_list, node_idx)
        type_node = next(iter(self._schema_graph.successor_indices(node_idx)))
        field_nodes = self._schema_graph.successor_indices(type_node)
        for field_idx in field_nodes:
            if self._schema_graph[field_idx].name == dot_path[0]:
                idx_list.append(node_idx)
                return self._find_idx_path(dot_path[1:], idx_list, field_idx)
            continue
        return []

    def _parse_dot_path(self, dot_path: str) -> list[list[int]]:
        """Parse dot-separated field names into lists of matching node indices. ex: "prd.chem_comp.id" --> [[57, 81, 116], [610, 81, 116], [858, 81, 116]].

        Args:
            dot_path (str): dot-separated field names given in return_data_list
                ex: "exptl.method" or "prd.chem_comp.id"

        Raises:
            ValueError: thrown if no path matches dot_path

        Returns:
            list[list[int]]: list of paths where each path is a list of FieldNode indices matching the given dot_path
        """
        path_list = dot_path.split(".")
        node_matches: list[int] = self._field_to_idx_dict[path_list[0]]
        idx_path_list: list[list[int]] = []
        for node_idx in node_matches:
            found_path: list[int] = []
            found_path = self._find_idx_path(path_list[1:], found_path, node_idx)
            if len(found_path) == len(path_list):
                idx_path_list.append(found_path)
        if len(idx_path_list) == 0:
            error_msg = f"return_data_list path is not valid: {dot_path}"
            raise ValueError(error_msg)

        return idx_path_list

    def _compare_paths(self, start_node_index: int, dot_paths: list[list[int]]) -> list[list[int]]:
        """Compare length of paths from the starting node to dot notation paths, returning the shortest paths.

        Args:
            start_node_index (int): the index of query's input_type
                ex: input_type entry --> 20
            dot_paths (list[list[int]]):  a list of paths where each path is a list of node indices matching a dot notation string

        Raises:
            ValueError: thrown when there is no path from the input_type node to the return data nodes.

        Returns:
            list[list[int]]: list of shortest paths from the input_type node index to the index of the final field given in dot notation.
                ex: input_type "entry" and "exptl.method" would return a list of shortest path(s) with indices from "entry" to "method".
        """
        all_paths: list[list[int]] = []

        for path in dot_paths:
            first_path_idx = path[0]
            if start_node_index == first_path_idx:
                unique_paths_list: list[list[int]] = [path]
            else:
                paths = rx.digraph_all_shortest_paths(self._schema_graph, start_node_index, first_path_idx, weight_fn=lambda edge: edge)
                unique_paths = {tuple(path) for path in paths}
                unique_paths_list = [list(unique_path) for unique_path in unique_paths]
                if len(unique_paths_list) == 0:
                    unique_paths_list = []
                else:
                    for unique_path in unique_paths_list:
                        unique_path += path[1:]
            all_paths.extend(unique_paths_list)
        if len(all_paths) == 0:
            error_msg = f"Can't access \"{'.'.join(self._idx_path_to_name_path(dot_paths[0]))}\" from given input_type {self._schema_graph[start_node_index].name}"
            raise ValueError(error_msg)
        shortest_path_len = len(min(all_paths, key=len))
        shortest_paths = [path for path in all_paths if len(path) == shortest_path_len]
        return shortest_paths  # noqa: RET504

    def _weigh_assemblies(self, paths: list[list[int]], assembly_node_idxs: list[int]) -> list[list[int]]:
        """Remove paths containing "assemblies" if there are <= length paths available. Mimics weighing assembly edges in the rest of query construction.

        Args:
            paths (list[list[int]]): list of paths where each path is a list of indices from a root node to a requested field.
            assembly_node_idxs (list[int]): list of indices of nodes named "assemblies" (root node excluded)

        Returns:
            list[list[int]]: List with weight applied (no "assemblies" path if there is an equivalent path present)
        """
        remove_paths: set[tuple[int, ...]] = set()

        for path in paths:
            for assemblies_idx in assembly_node_idxs:
                if assemblies_idx in path:
                    for compare_path in paths:
                        if compare_path == path:
                            continue
                        name_compare_path = self._idx_path_to_name_path(compare_path)
                        # If there are shorter or equal length paths without "assemblies", filter out
                        if (len(compare_path) <= len(path)) and ("assemblies" not in name_compare_path) and (compare_path[-1] == path[-1]):
                            remove_paths.add(tuple(path))

        for path in remove_paths:  # type: ignore[assignment]
            paths.remove(list(path))

        return paths

    def _idx_to_name(self, idx: int) -> str:
        """Given an index, return the associated node's name.

        Args:
            idx (int): index of a node

        Returns:
            str: name of node
        """
        return str(self._schema_graph[idx].name)  # casting as string for mypy

    def _idx_path_to_name_path(self, idx_path: list[int]) -> list[str]:
        """Take a path of graph indices and return a path of field names.

        Args:
            idx_path (list[int]): List of node indices (can be both TypeNodes and FieldNodes)

        Returns:
            list[str]: List of field names, removing TypeNodes.
        """
        name_path: list[str] = []
        for idx in idx_path:
            if isinstance(self._schema_graph[idx], FieldNode):
                name_path.append(self._schema_graph[idx].name)  # noqa: PERF401
        return name_path

    def find_paths(self, input_type: str, return_data_name: str, descriptions: bool = False) -> list[str] | dict[str, str]:
        """Find path from input_type to any nodes matching return_data_name.

        Args:
            input_type (str): name of an input_type (ex: entry, polymer_entity_instance)
            return_data_name (str): name of one field, can be a redundant name
            descriptions (bool, optional): whether to include descriptions for the final field of each path. Default is False.

        Returns:
            Union[list[str], Dict]
                list[str]: list of paths to nodes with names that match return_data_name
                Dict: if description is True, a dictionary with paths as keys and descriptions as values is returned.
        """
        paths: list[list[int]] = []
        input_type_idx: int = self._root_to_idx[input_type]
        for possible_idx in self._field_to_idx_dict[return_data_name]:
            paths_to_idx = rx.all_simple_paths(self._schema_graph, input_type_idx, possible_idx)
            paths.extend(paths_to_idx)
        dot_paths: list[str] = []
        description_dict: dict[str, str] = {}
        for path in paths:
            name_path = self._idx_path_to_name_path(path)
            dot_path = ".".join(name_path[1:])
            dot_paths.append(dot_path)
            if descriptions:
                final_field_idx = path[-1]
                description = getattr(self._schema_graph[final_field_idx], "description")
                if description is None:
                    description = ""
                description_dict[dot_path] = description.replace("\n", " ")

        if descriptions:
            return description_dict
        dot_paths.sort()
        return dot_paths

    def read_enum(self, type_name: str) -> list[str]:
        """Parse given type name into a list of enumeration values.

        Args:
            type_name (str): GraphQL type name
        """
        for type_dict in self.schema["data"]["__schema"]["types"]:
            if type_dict["name"] == type_name:
                return [value["name"] for value in type_dict["enumValues"]]
        error_msg = "Not an ENUM value in GraphQL schema"
        raise ValueError(error_msg)

    def check_typing(self, query_type: str, enum_types: "EnumTypes", args: dict[str, Any]) -> None:  # noqa: UP037, F821
        """Check that ENUM types are valid values and that if the schema type.

        Args:
            query_type (str): Name of query field (annotations, alignments, etc)
            enum_types (EnumTypes): Enum class of GraphQL types that are enumerations.
                Values are lists of valid strings corresponding to enumerations
            args (Dict[str, Any]): Dictionary where keys are argument names and
                values are input values
        """
        error_list = []
        arg_dict_list = self._root_dict[query_type]
        for arg_dict in arg_dict_list:
            arg_type = arg_dict["ofType"]
            arg_name = arg_dict["name"]

            if arg_name not in args:
                continue

            if arg_dict["kind"] == "NON_NULL" and arg_dict["ofKind"] == "ENUM" and args[arg_name] not in enum_types[arg_type].value:
                error_list.append(f"Invalid value '{args[arg_name]}' for '{arg_name}': valid values are {enum_types[arg_type].value}")

            # If list. Does not do type-checking for items of list.
            if arg_dict["kind"] == "LIST":
                if not isinstance(args[arg_name], list):
                    error_list.append(f"'{arg_name}' must be a list")
                # No case written for boolean arguments since there are none right now
                if arg_type == "Int":
                    if not all(isinstance(item, int) for item in args[arg_name]):
                        error_list.append(f"'{arg_name}' must be a list of integer(s)")
                elif not all(isinstance(item, str) for item in args[arg_name]):
                    error_list.append(f"'{arg_name}' must be list of string(s)")

            # if list of ENUMs
            if arg_dict["kind"] == "NON_NULL" and arg_dict["ofKind"] == "LIST":
                mismatch_type = [item for item in args[arg_name] if item not in enum_types[arg_type].value]
                if mismatch_type:
                    error_msg = f"Invalid value(s) {mismatch_type} for '{arg_name}': valid values are {enum_types[arg_type].value}"
                    raise ValueError(error_msg)

        if error_list:
            raise ValueError("\n" + "  " + "\n  ".join(error_list))

    def construct_query(
        self, query_type: str, query_args: dict[str, str] | dict[str, list[Any]], return_data_list: list[str], suppress_autocomplete_warning: bool = False
    ) -> dict[str, Any]:
        """
        Construct a GraphQL query - currently only uses rustworkx.

        Args:
            query_type (str): root type ("alignments", "annotations")
            query_args (dict[str, str] | dict[str, list]): dictionary where keys are argument names and
                values are input values
            return_data_list (list[str]): list of fields to request data for
            suppress_autocomplete_warning (bool, optional): Whether to suppress warning for autocompletion of paths.
                Defaults to False.

        Raises:
            ValueError: unknown field in the return_data_list

        Returns:
            dict: GraphQL query in JSON format
        """
        unknown_return_list: list[str] = []
        for field in return_data_list:
            if "." in field:
                separate_fields = field.split(".")
                for sep_field in separate_fields:
                    if sep_field not in self._field_names_list:
                        unknown_return_list.append(sep_field)  # noqa: PERF401
            elif field not in self._field_names_list:
                unknown_return_list.append(field)
        if unknown_return_list:
            error_msg = f"Unknown item in return_data_list: {unknown_return_list}"
            raise ValueError(error_msg)
        # if use_networkx:
        #     query = self._construct_query_networkx(
        #         input_type=input_type,
        #         input_ids=input_ids,
        #         return_data_list=return_data_list,
        #         suppress_autocomplete_warning=suppress_autocomplete_warning
        #     )
        # else:
        # query = self._construct_query_rustworkx(
        #     input_type=input_type,
        #     input_ids=input_ids,
        #     return_data_list=return_data_list,
        #     add_rcsb_id=add_rcsb_id,
        #     suppress_autocomplete_warning=suppress_autocomplete_warning
        # )
        query = self._construct_query_rustworkx(
            query_type=query_type, query_args=query_args, return_data_list=return_data_list, suppress_autocomplete_warning=suppress_autocomplete_warning
        )
        return query  # noqa: RET504

    def _construct_query_rustworkx(
        self,
        query_type: str,
        query_args: dict[str, str] | dict[str, list[Any]],
        return_data_list: list[str],
        suppress_autocomplete_warning: bool = False
    ) -> dict[str, Any]:
        """Construct a GraphQL query as a dict, if using rustworkx.

        Args:
            query_type (str): type of query to make (ex: Alignments, Annotations, etc)
            query_args (dict[str, str] | dict[str, list[Any]]): dict of query_type-specific args
            return_data_list (list[str]): list of fields to request
            suppress_autocomplete_warning (bool, optional): Whether to suppress warning when
                autocompletion of paths is used. Defaults to False.

        Returns:
            dict[str, Any]: GraphQL query as dict.
                Dict is JSON format needed for POST requests (https://sequence-coordinates.rcsb.org/#gql-api)
        """
        # Build first line of query where arguments are given
        arg_list = self._root_dict[query_type]
        arg_value_list = tuple(self._format_args(arg_dict, query_args[arg_dict["name"]]) for arg_dict in arg_list if arg_dict["name"] in query_args)
        first_line = f"{query_type}{str(arg_value_list).replace("'", '')}"

        # Build query body
        start_idx = self._root_to_idx[query_type]
        return_data_path_dict: dict[int, list[int]] = self.return_fields_to_paths(start_idx, query_type, return_data_list)
        # return_data_query_list is a list of queries, each one corresponding to one field in return_data_list
        return_data_query_list = []
        for return_field_idx, path in return_data_path_dict.items():
            # Format the paths with the correct nesting of fields. Still using indices at this point
            return_field_query_dict = self._idxs_to_idx_dict(idx_list=path, autopopulated_fields=self._get_descendant_fields(return_field_idx))
            return_data_query_list.append(return_field_query_dict)

        # Merge all the queries in merge_query_list so there are no redundant paths
        idx_query_body = self._merge_query_list(return_data_query_list)
        name_query_body = self._idx_dict_to_name_dict(idx_query_body, query_args)
        query = self._query_dict_to_graphql_string(first_line, name_query_body)
        return {"query": query}

    def _merge_query_list(self, query_list: list[dict[int, Any] | list[int]]) -> list[dict[int, Any] | list[int]]:
        """Merge a list of query dicts, returning a merged query with unique indices/index dictionaries.

        Args:
            query_list (list[dict[int, Any]  |  int]): list where each item is a query to a field
                specified by return_data_list in construct_query

        Returns:
            list[dict[int, Any] | int]: List of indices and index dicts representing the merged query
        """
        # print(f"query_list: {query_list}")
        if isinstance(query_list[0], list):
            result: list[dict[int, Any] | list[int]] | list[int] = query_list[0]
        result = [query_list[0]]

        for path in query_list[1:]:
            for i, result_path in enumerate(result):
                merged_query = self._merge_queries(result_path, path)
                # TODO: Rather than checking if merged query and having to use two separate functions.
                #  Maybe check if length of merged_query is == len(result_path) + len(path) (with some additional logic obviously)
                path_len = 1
                if isinstance(path, list):
                    path_len = len(path)
                result_path_len = 1
                if isinstance(result_path, list):
                    result_path_len = len(result_path)

                if len(merged_query) < (path_len + result_path_len):
                    result.pop(i)
                    result.extend(merged_query)
                    # print(f"merging: {path} and {result_path}")
                    break
            if len(merged_query) == (path_len + result_path_len):
                result.append(path)
            # print(f"result: {result}")

        # print(f"FINAL: {result}")
        return result

    def _merge_queries(
        self,
        dict_1: dict[int, Any] | list[int | dict[int, Any]] | int,
        dict_2: dict[int, Any] | list[int | dict[int, Any]] | int,
    ) -> list[dict[int, Any] | int] | list[dict[int, Any]] | list[int]:
        """Merge two dictionaries without overwriting values.

        Args:
            dict_1 (dict[int, Any] | list[int  |  dict[int, Any]] | int): _description_
            dict_2 (dict[int, Any] | list[int  |  dict[int, Any]] | int): _description_

        Raises:
            ValueError: _description_

        Returns:
            list[dict[int, Any] | int] | list[dict[int, Any]] | list[int]: _description_
        """
        # Case where both queries are dicts:
        #   If share keys --> merge values
        #   If dicts are equal --> return one dict
        #   Else: return both dicts in list
        if isinstance(dict_1, dict) and isinstance(dict_2, dict):
            for key in dict_1.keys():
                if (key in dict_2):
                    return [{key: self._merge_queries(dict_1[key], dict_2[key])}]
                return [dict_1, dict_2]

        # Cases where one query is a list and one is a dict
        #   If query is already in the other query, return only more general query
        #   Else: return list with both queries
        elif isinstance(dict_1, list) and isinstance(dict_2, dict):
            if dict_2 in dict_1:
                return dict_1
            return dict_1 + [dict_2]
        elif isinstance(dict_1, dict) and isinstance(dict_2, list):
            if dict_1 in dict_2:
                return dict_2
            return [dict_1] + dict_2

        # Case where both queries are lists
        #   Merge lists, checking if items are unique
        elif isinstance(dict_1, list) and isinstance(dict_2, list):
            unique_query_1 = [path for path in dict_1 if path not in dict_2]
            return unique_query_1 + dict_2
        raise ValueError("Invalid dictionary input")

    def _idxs_to_idx_dict(
            self,
            idx_list: list[int],
            autopopulated_fields: list[int | dict[int, Any]],
            partial_query: dict[Any, Any] | None = None,
    ) -> dict[int, Any] | list[int] | list[dict[int, Any] | int]:
        """Construct a query with correct nesting of dicts/lists

        Args:
            idx_list (list[int]): list of indices to a return_date_list field
            autopopulated_fields (list[int  |  dict[int, Any]]): fields underneath return_data_list field (can be empty)
            partial_query (dict[Any, Any] | None, optional): the query as it gets constructed by recursion. Defaults to None.

        Returns:
            dict[int, Any] | list[int] | list[dict[int, Any] | int]: query dict/list with nesting
        """
        if partial_query is None:
            partial_query = {}
        # Base case
        if len(idx_list) == 0:
            assert isinstance(partial_query, dict)  # for mypy
            return partial_query
        # Add autopopulated fields
        if len(idx_list) == 1:
            if not autopopulated_fields:
                return [idx_list[0]]
            return {idx_list[0]: autopopulated_fields}
        # Add level of nesting
        else:
            return {idx_list[0]: self._idxs_to_idx_dict(idx_list[1:], autopopulated_fields=autopopulated_fields)}

    def _idx_dict_to_name_dict(
        self,
        idx_fields: list[dict[int, Any] | int] | dict[int, Any] | int,
        query_args: dict[str, Any]
    ) -> dict[str, Any] | list[str] | str:
        """Convert dictionary of indices to dictionary of field names and add arguments if applicable."""
        query_dict = {}
        if isinstance(idx_fields, dict):
            for field_idx, subfield in idx_fields.items():
                field_name = self._idx_to_name(field_idx)
                args = getattr(self._schema_graph[field_idx], "args")
                if args:
                    field_name = self.add_field_args(field_name, args, query_args)
                query_dict[field_name] = self._idx_dict_to_name_dict(subfield, query_args)
            return query_dict
        elif isinstance(idx_fields, list):
            return [self._idx_dict_to_name_dict(field, query_args) for field in idx_fields]
        elif not idx_fields:
            return ""
        else:
            return self._idx_to_name(idx_fields)

    def add_field_args(self, field_name: str, args: list[dict[str, Any]], query_args: dict[str, Any]) -> str:
        """Add arguments to a field, returning the fieldname and args as a formatted string.

        Args:
            args (list[dict[str, Any]]): args of a field, retrieved from the GraphQL schema/FieldNode object
            query_args (dict[str, Any]): dictionary where keys are argument name and values are user input

        Returns:
            str: field name or field name with corresponding arguments
        """
        # Check FieldNode argument names and see if user has passed in corresponding values 
        formatted_args = []
        for arg in args:
            arg_name = arg["name"]
            if arg_name in query_args:
                formatted_args.append(self._format_args(arg, query_args[arg_name]))

        if formatted_args:
            return f"{field_name}{str(tuple(formatted_args)).replace("'", "")}"
        else:
            return field_name

    def _query_dict_to_graphql_string(self, first_line: str, query_body: dict[str, Any]) -> str:
        """Turn query dictionary into a string in GraphQL syntax"""
        formatted_query_body = (
            # format the dict as a GraphQL query
            # TODO: bit janky, change?
            json.dumps(query_body, indent=2, separators=(" ", "~"))
            .replace('"', "")
            .replace("'", '"')
            .replace("[", "")
            .replace("]", "")
            .replace("{", "")
            .replace("~", "{")
        )
        formatted_query_body = "\n".join(line for line in formatted_query_body.splitlines() if line.strip())
        query = f"query{{{first_line}{{\n{formatted_query_body}}}}}"
        return query

    def get_input_id_dict(self, input_type: str) -> dict[str, str]:
        """Get keys input dictionary for given input_type.

        Args:
            input_type (str): GraphQL input_type (ex: alignments)

        Returns:
            dict[str, str]: dictionary where keys are argument names and values are descriptions
        """
        if input_type not in self._root_dict:
            error_msg = "Not a valid input_type, no available input_id dictionary"
            raise ValueError(error_msg)
        root_dict_entry = self._root_dict[input_type]
        input_dict = {}
        for arg in root_dict_entry:
            name = arg["name"]
            description = arg["description"]
            if (len(root_dict_entry) == 1) and root_dict_entry[0]["name"] == "entry_id":
                description = "ID"
            input_dict[name] = description
        return input_dict

    def find_field_names(self, search_string: str) -> list[str]:
        """Find field names that fully or partially match the search string.

        Args:
            search_string (str): string to search field names for

        Raises:
            ValueError: thrown when a type other than string is passed in for search_string
            ValueError: thrown when no fields match search_string

        Returns:
            list[str]: list of matching field names
        """
        if not isinstance(search_string, str):
            error_msg = f"Please input a string instead of {type(search_string)}"  # type: ignore[unreachable]
            raise TypeError(error_msg)

        field_names = [key for key in self._field_to_idx_dict if search_string.lower() in key.lower()]
        if not field_names:
            error_msg = f"No fields found matching '{search_string}'"
            raise ValueError(error_msg)
        return field_names
