##
# File:    test_data_schema.py
# Author:  Ivana Truong
# Date:
# Version:
#
# Update:
#
#
##
"""
Tests for all functions of the schema file. (Work in progress)
"""

__docformat__ = "google en"
__author__ = ""
__email__ = ""
__license__ = ""

import logging

# import platform
# import resource
import time
import json
import os
import unittest
import requests
# import rustworkx as rx
# import networkx as nx

from rcsbapi.data import DATA_SCHEMA
from rcsbapi.config import config
from rcsbapi.const import const

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SchemaTests(unittest.TestCase):
    def test_schema_version(self):
        with self.subTest(msg="1. Compare entry schema"):
            entry_schema_path = os.path.join(os.path.dirname(__file__), "..", "rcsbapi", const.DATA_API_SCHEMA_DIR, const.DATA_API_SCHEMA_ENDPOINT_TO_FILE["entry"])
            with open(entry_schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            local_schema_version = schema_data.get("$comment").split(": ")[1]
            local_major_minor_version = ".".join(local_schema_version.split(".")[:2])

            online_schema_url = "https://data.rcsb.org/rest/v1/schema/entry"
            response = requests.get(online_schema_url, timeout=config.DATA_API_TIMEOUT)
            online_schema_data = response.json()
            online_schema_version = online_schema_data.get("$comment").split(": ")[1]
            online_major_minor_version = ".".join(online_schema_version.split(".")[:2])
            self.assertEqual(local_major_minor_version, online_major_minor_version)

        with self.subTest(msg="2. Compare polymer_entity schema"):
            polymer_entity_schema_path = os.path.join(os.path.dirname(__file__), "..", "rcsbapi", const.DATA_API_SCHEMA_DIR, const.DATA_API_SCHEMA_ENDPOINT_TO_FILE["polymer_entity"])
            with open(polymer_entity_schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            local_schema_version = schema_data.get("$comment").split(": ")[1]
            local_major_minor_version = ".".join(local_schema_version.split(".")[:2])

            online_schema_url = "https://data.rcsb.org/rest/v1/schema/polymer_entity"
            response = requests.get(online_schema_url, timeout=config.DATA_API_TIMEOUT)
            online_schema_data = response.json()
            online_schema_version = online_schema_data.get("$comment").split(": ")[1]
            online_major_minor_version = ".".join(online_schema_version.split(".")[:2])
            self.assertEqual(local_major_minor_version, online_major_minor_version)

        with self.subTest(msg="3. Compare polymer_entity_instance schema"):
            polymer_entity_schema_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "rcsbapi",
                const.DATA_API_SCHEMA_DIR,
                const.DATA_API_SCHEMA_ENDPOINT_TO_FILE["polymer_entity_instance"]
            )
            with open(polymer_entity_schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            local_schema_version = schema_data.get("$comment").split(": ")[1]
            local_major_minor_version = ".".join(local_schema_version.split(".")[:2])

            online_schema_url = "https://data.rcsb.org/rest/v1/schema/polymer_entity_instance"
            response = requests.get(online_schema_url, timeout=config.DATA_API_TIMEOUT)
            online_schema_data = response.json()
            online_schema_version = online_schema_data.get("$comment").split(": ")[1]
            online_major_minor_version = ".".join(online_schema_version.split(".")[:2])
            self.assertEqual(local_major_minor_version, online_major_minor_version)

    def setUp(self):
        self.__startTime = time.time()
        logger.info("Starting %s at %s", self.id().split(".")[-1], time.strftime("%Y %m %d %H:%M:%S", time.localtime()))

    def tearDown(self) -> None:
        endTime = time.time()
        logger.info("Completed %s at %s (%.4f seconds)", self.id().split(".")[-1], time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - self.__startTime)

    def testFetch(self):
        fetched_schema = DATA_SCHEMA._fetch_schema()
        self.assertNotIn("errors", fetched_schema.keys())

    def testConstructRootDict(self):
        with self.subTest(msg="1. root dict for singular type (interface)"):
            interface_dict = DATA_SCHEMA._root_dict["interface"]
            self.assertEqual(len(interface_dict), 3)
            arg_names = []
            for arg_dict in interface_dict:
                arg_names.append(arg_dict["name"])
            self.assertIn("assembly_id", arg_names)
            self.assertIn("interface_id", arg_names)
            self.assertIn("entry_id", arg_names)
        with self.subTest(msg="2. root dict for plural type (entries)"):
            entries_dict = DATA_SCHEMA._root_dict["entries"]
            self.assertEqual(len(entries_dict), 1)
            self.assertEqual(entries_dict[0]["name"], "entry_ids")
            self.assertEqual(entries_dict[0]["kind"], "LIST")
        with self.subTest(msg="3. root dict has the same number of types as schema"):
            schema_list = DATA_SCHEMA._root_introspection["data"]["__schema"]["queryType"]["fields"]
            self.assertEqual(len(schema_list), len(list(DATA_SCHEMA._root_dict.keys())))

    def testConstructTypeDict(self):
        type_fields_dict = {}
        entry_dict = {}
        type_fields_dict = DATA_SCHEMA._construct_type_dict()
        entry_dict_from_func = type_fields_dict["CoreEntry"]
        type_dict_list = DATA_SCHEMA.schema["data"]["__schema"]["types"]
        entry_found = False
        i = 0
        while entry_found is False and i < len(type_dict_list):
            type_dict = type_dict_list[i]
            name = str(type_dict["name"])
            if name == "CoreEntry":
                fields = type_dict["fields"]
                field_dict = {}
                for field in fields:
                    field_dict[str(field["name"])] = dict(field["type"])
                entry_dict = field_dict
                entry_found = True
            i += 1
        self.assertEqual(entry_dict_from_func, entry_dict)
        self.assertEqual(len(type_dict_list), len(DATA_SCHEMA._type_fields_dict.keys()))

    # def testRecurseBuildSchema(self):  # doesn't work right now
    #     original_networkx_flag = schema._use_networkx
    #     schema._use_networkx = False
    #     importlib.reload(schema)
    #     DATA_SCHEMA = DataSchema(config.API_ENDPOINT)
    #     DATA_SCHEMA.recurse_build_schema(DATA_SCHEMA._schema_graph, 'Query')
    #     self.assertIsInstance(DATA_SCHEMA._schema_graph, rx.PyDiGraph)
    #     schema._use_networkx = True
    #     importlib.reload(schema)
    #     DATA_SCHEMA = DataSchema(config.API_ENDPOINT)
    #     DATA_SCHEMA.recurse_build_schema(DATA_SCHEMA._schema_graph, 'Query')
    #     self.assertIsInstance(DATA_SCHEMA._schema_graph, nx.classes.digraph.DiGraph)
    #     # reset to original
    #     schema._use_networkx = original_networkx_flag
    #     importlib.reload(schema)
    #     DATA_SCHEMA = DataSchema(config.API_ENDPOINT)

    def testConstructQuery(self):
        with self.subTest(msg="1. return data not specific enough"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA.construct_query(input_ids=["4HHB"], input_type="entry", return_data_list=["id"])
        with self.subTest(msg="1. multiple ids, but entered singular input_type"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA.construct_query(input_ids=["4HHB", "1IYE"], input_type="entry", return_data_list=["id"])

    def testConstructQueryRustworkX(self):
        with self.subTest(msg="1.  singular input_type (entry)"):
            query = DATA_SCHEMA._construct_query_rustworkx(input_ids={"entry_id": "4HHB"}, input_type="entry", return_data_list=["exptl"])
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="2. plural input_type (entries)"):
            query = DATA_SCHEMA._construct_query_rustworkx(input_ids={"entry_ids": ["4HHB", "1IYE"]}, input_type="entries", return_data_list=["exptl"])
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="3. two arguments (polymer_entity_instance)"):
            query = DATA_SCHEMA._construct_query_rustworkx(input_ids={"asym_id": "A", "entry_id": "4HHB"}, input_type="polymer_entity_instance", return_data_list=["exptl"])
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="4. three arguments (interface)"):
            query = DATA_SCHEMA._construct_query_rustworkx(
                input_ids={"assembly_id": "1", "interface_id": "1", "entry_id": "4HHB"}, input_type="interface", return_data_list=["interface.rcsb_id"]
            )
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="5. request multiple return fields"):
            query = DATA_SCHEMA._construct_query_rustworkx(input_ids={"entry_id": "4HHB"}, input_type="entry", return_data_list=["exptl", "rcsb_polymer_instance_annotation"])
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="6. request scalar field"):
            query = DATA_SCHEMA._construct_query_rustworkx(input_ids={"entry_id": "4HHB"}, input_type="entry", return_data_list=["entry.rcsb_id"])
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="12. two arguments (polymer_entity_instances)"):
            query = DATA_SCHEMA._construct_query_rustworkx(
                input_ids={"instance_ids": ["4HHB.A", "4HHB.C"]}, input_type="polymer_entity_instances", return_data_list=["rcsb_polymer_instance_annotation"]
            )
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="20. nested query"):
            query = DATA_SCHEMA._construct_query_rustworkx(input_type="interfaces", return_data_list=["rcsb_interface_partner"], input_ids=["MA_MACOFFESLACC100000G1I2-1.1", "7XIW-1.2"])
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="20. requesting scalars under same field"):
            query = DATA_SCHEMA._construct_query_rustworkx(input_type="entry", return_data_list=["exptl.method", "exptl.details"], input_ids=["4HHB"])
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        # Test error handling
        with self.subTest(msg="7. too many input ids passed in"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA._construct_query_rustworkx(input_ids={"entry_id": ["4HHB", "1IYE"]}, input_type="entry", return_data_list=["exptl"])
        with self.subTest(msg="8. too few inputs keys provided"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA._construct_query_rustworkx(input_ids={"entry_id": "4HHB"}, input_type="polymer_entity_instance", return_data_list=["exptl"])
        with self.subTest(msg="9. incorrect input keys provided"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA._construct_query_rustworkx(input_ids={"assembly_id": "1"}, input_type="polymer_entity_instance", return_data_list=["exptl"])
        with self.subTest(msg="10. no path exists"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA._construct_query_rustworkx(input_ids={"assembly_id": "1", "interface_id": "1", "entry_id": "4HHB"}, input_type="interface", return_data_list=["exptl"])
        # with self.subTest(msg="11. field doesn't exist"):
        #     with self.assertRaises(ValueError):
        #         DATA_SCHEMA._construct_query_rustworkx(input_ids={"assembly_id": "1", "interface_id": "1", "entry_id": "4HHB"}, input_type="interface", return_data_list=["aaa"])

    def regexChecks(self):
        with self.subTest(msg="1. regex for _entity_instances"):
            query = DATA_SCHEMA._construct_query_rustworkx(
                input_type="polymer_entity_instances", return_data_list=["rcsb_polymer_instance_annotation"], input_ids=["4HHB.A", "AF_AFA0A009IHW8F1.B"]
            )
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="2. regex for _entities"):
            query = DATA_SCHEMA._construct_query_rustworkx(
                input_type="polymer_entities", return_data_list=["rcsb_polymer_entity_feature"], input_ids=["AF_AFA0A009IHW8F1_1", "4HHB_1"]
            )
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="3. regex for entries"):
            query = DATA_SCHEMA._construct_query_rustworkx(input_type="entries", return_data_list=["exptl"], input_ids=["7XIW", "4HHB"])
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="4. regex for assemblies"):
            query = DATA_SCHEMA._construct_query_rustworkx(
                input_type="assemblies",
                return_data_list=["rcsb_struct_symmetry_lineage"],
                input_ids=["4HHB-1", "MA_MACOFFESLACC100000G1I2-2"]
            )
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="5. regex for interfaces"):
            query = DATA_SCHEMA._construct_query_rustworkx(
                input_type="interfaces", return_data_list=["rcsb_interface_container_identifiers.assembly_id"], input_ids=["MA_MACOFFESLACC100000G1I2-1.1", "7XIW-1.2"]
            )
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="6. regex with a singular type"):
            query = DATA_SCHEMA._construct_query_rustworkx(input_type="entry", return_data_list=["exptl"], input_ids=["4HHB"])
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="7. wrong format for CSM entry id"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA._construct_query_rustworkx(input_type="entry", return_data_list=["exptl.method", "exptl.details"], input_ids=["MA_MACOFFESLACC100000G1I2-1.1"])
        with self.subTest(msg="8. id_list provided with incorrect input_type"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA._construct_query_rustworkx(input_type="assemblies", return_data_list=["exptl"], input_ids=["4HHB", "1IYE"])

    def testAllRoots(self):  # incomplete
        with self.subTest(msg="1. uniprot"):
            try:
                DATA_SCHEMA._construct_query_rustworkx(
                    input_type="uniprot", input_ids={"uniprot_id": "P01308"}, return_data_list=["uniprot.rcsb_id", "reference_sequence_identifiers.database_accession"]
                )
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

    def testDotNotation(self):
        with self.subTest(msg="1. dot notation on deeply nested path"):
            try:
                DATA_SCHEMA._construct_query_rustworkx(
                    input_ids={"entry_id": "4HHB"},
                    input_type="entry",
                    return_data_list=[
                        "entry.assemblies.polymer_entity_instances.polymer_entity.polymer_entity_groups.group_provenance.rcsb_group_provenance_container_identifiers.group_provenance_id"
                    ],
                )
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="2. query that loops back to input type"):
            try:
                DATA_SCHEMA._construct_query_rustworkx(
                    input_ids={"entry_id": "4HHB"},
                    input_type="entry",
                    return_data_list=["polymer_entities.entry.assemblies.polymer_entity_instances.polymer_entity.polymer_entity_instances.polymer_entity.entry.rcsb_id"],
                )
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="3. request same field at many levels"):
            try:
                DATA_SCHEMA._construct_query_rustworkx(
                    input_ids={"entry_id": "4HHB"},
                    input_type="entry",
                    return_data_list=[
                        "entry.rcsb_id",
                        "entry.assemblies.rcsb_id",
                        "entry.assemblies.polymer_entity_instances.rcsb_id",
                        "entry.assemblies.polymer_entity_instances.polymer_entity.rcsb_id",
                        "entry.assemblies.polymer_entity_instances.polymer_entity.polymer_entity_groups.rcsb_id",
                        "entry.assemblies.polymer_entity_instances.polymer_entity.polymer_entity_groups.group_provenance.rcsb_id",
                    ],
                )
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="4. throw error when multiple paths are available"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA._construct_query_rustworkx(input_ids=["4HHB"], input_type="entry", return_data_list=["chem_comp.id"])

    def testDescription(self):
        with self.subTest(msg="1. check nonpolymer_comp description"):
            nonpolymer_comp_idx = DATA_SCHEMA._field_to_idx_dict["nonpolymer_comp"][0]
            description = DATA_SCHEMA._schema_graph[nonpolymer_comp_idx].description
            logger.info("Description for 'nonpolymer_comp': %s", DATA_SCHEMA._schema_graph[nonpolymer_comp_idx].description)
            self.assertEqual(description, "Get a non-polymer chemical components described in this molecular entity.")

    def testFindFieldNames(self):
        with self.subTest(msg="1. search for rcsb"):
            result = DATA_SCHEMA.find_field_names("rcsb")
            self.assertIn("rcsb_id", result)
        with self.subTest(msg="1. search for nonexistent field"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA.find_field_names("foo")
        with self.subTest(msg="2. search for field list"):
            with self.assertRaises(ValueError):
                DATA_SCHEMA.find_field_names(["rcsb", "exptl"])  # type: ignore

    def testWeigh(self):
        with self.subTest(msg="1. Remove assembly paths that have a parallel/equivalent path"):
            # 481 is the node index of an assemblies node
            paths = [
                [1, 481, 3],
                [1, 2, 3],
                [1, 2, 3, 4],
            ]

            weigh_paths = DATA_SCHEMA._weigh_assemblies(paths, [481])
            self.assertEqual(len(weigh_paths), 2)

        with self.subTest(msg="2. Do not remove paths without an equivalent path"):
            # 481 is the node index of an assemblies node
            paths = [
                [1, 481, 3, 4, 5],
                [1, 2, 3, 4, 5, 6],
                [1, 481],
            ]

            weigh_paths = DATA_SCHEMA._weigh_assemblies(paths, [481])
            self.assertEqual(len(weigh_paths), 3)


def buildSchema():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(SchemaTests("test_schema_version"))
    suiteSelect.addTest(SchemaTests("testFetch"))
    suiteSelect.addTest(SchemaTests("testConstructRootDict"))
    # suiteSelect.addTest(SchemaTests("testRecurseBuildSchema"))
    suiteSelect.addTest(SchemaTests("regexChecks"))
    suiteSelect.addTest(SchemaTests("testConstructQuery"))
    suiteSelect.addTest(SchemaTests("testAllRoots"))
    suiteSelect.addTest(SchemaTests("testDotNotation"))
    suiteSelect.addTest(SchemaTests("testConstructQueryRustworkX"))
    suiteSelect.addTest(SchemaTests("testDescription"))
    suiteSelect.addTest(SchemaTests("testFindFieldNames"))
    suiteSelect.addTest(SchemaTests("testWeigh"))
    return suiteSelect


if __name__ == "__main__":
    mySuite = buildSchema()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
