##
# File:    test_data_query.py
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

# import importlib
# import platform
# import resource
import time
import unittest
import requests

from rcsbapi.search import search_attributes as attrs
from rcsbapi.data import DataSchema, DataQuery
from rcsbapi.config import config
from rcsbapi.const import const

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.__startTime = time.time()
        logger.info("Starting %s at %s", self.id().split(".")[-1], time.strftime("%Y %m %d %H:%M:%S", time.localtime()))

    def tearDown(self) -> None:
        endTime = time.time()
        logger.info("Completed %s at %s (%.4f seconds)", self.id().split(".")[-1], time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - self.__startTime)

    def testGetEditorLink(self):
        # query_str = '{ entries(entry_ids: ["4HHB", "1IYE"]) {\n  exptl {\n     method_details\n     method\n     details\n     crystals_number\n  }\n}}'
        query_obj = DataQuery(input_type="entries", input_ids={"entry_ids": ["4HHB", "1IYE"]}, return_data_list=["exptl"])
        url = query_obj.get_editor_link()
        response_json = requests.get(url, timeout=10)
        self.assertEqual(response_json.status_code, 200)

    def testExec(self):
        with self.subTest("1. Batching into requests with fewer Ids"):
            input_ids = []
            for _ in range(165):
                input_ids.append("4HHB")
            query_obj = DataQuery(input_type="entries", input_ids={"entry_ids": input_ids}, return_data_list=["exptl"])
            query_obj.exec()
            # assert that the batch and merge functions are called
            # assert len of results is same as num of input ids

    def testLowercaseIds(self):
        with self.subTest(msg="1. List of IDs"):
            try:
                query_obj = DataQuery(input_type="entries", input_ids=["4hhb"], return_data_list=["exptl.method"])
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="2. Dictionary of IDs"):
            try:
                query_obj = DataQuery(input_type="entries", input_ids={"entry_ids": ["4hhb", "1iye"]}, return_data_list=["exptl"])
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="2. IDs with separators"):
            try:
                query_obj = DataQuery(input_type="interfaces", input_ids=["4hhb-1.1"], return_data_list=["rcsb_interface_info.interface_area"])
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="3. Pubmed IDs"):
            try:
                query_obj = DataQuery(input_type="pubmed", input_ids=["6726807"], return_data_list=["rcsb_pubmed_doi"])
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="3. UniProt IDs"):
            try:
                query_obj = DataQuery(input_type="uniprot", input_ids=["p68871"], return_data_list=["rcsb_id"])
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

    def testParseGQLError(self):
        pass

    def testBatchIDs(self):
        input_ids = []
        for _ in range(165):
            input_ids.append("4HHB")
        query_obj = DataQuery(input_type="entries", input_ids={"entry_ids": input_ids}, return_data_list=["exptl"])
        batch_size = 50
        batched_ids = query_obj._batch_ids(batch_size)
        total_ids = 0
        for batch in batched_ids:
            len_id_batch = len(batch)
            self.assertLessEqual(len_id_batch, batch_size)
            total_ids += len_id_batch
        self.assertEqual(len(query_obj.get_input_ids()), total_ids)

    def testMergeResponse(self):
        # assert that the lengths are combined and all ids are present?
        pass

    def testDocs(self):
        with self.subTest(msg="1. Initialize Schema"):
            schema = DataSchema()

        with self.subTest(msg="2. README 1"):
            try:
                query_obj = DataQuery(input_type="entries", input_ids=["4HHB"], return_data_list=["exptl.method"])
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="3. README 2"):
            try:
                query_obj = DataQuery(
                    input_type="polymer_entities",
                    input_ids=["2CPK_1", "3WHM_1", "2D5Z_1"],
                    return_data_list=[
                        "polymer_entities.rcsb_id",
                        "rcsb_entity_source_organism.ncbi_taxonomy_id",
                        "rcsb_entity_source_organism.ncbi_scientific_name",
                        "cluster_id",
                        "identity",
                    ],
                )
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="4. Quickstart 1"):
            try:
                query_obj = DataQuery(input_type="entries", input_ids=["4HHB"], return_data_list=["exptl.method"])
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="5. Quickstart 2, autocompletion"):
            try:
                query_obj = DataQuery(input_type="entries", input_ids=["4HHB"], return_data_list=["exptl"])
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="4. Helpful methods, get_editor_link()"):
            query = DataQuery(input_type="entries", input_ids=["4HHB"], return_data_list=["exptl"])
            response = requests.get(query.get_editor_link(), timeout=5)
            self.assertEqual(response.status_code, 200)

        with self.subTest(msg="5. Helpful methods, find_paths()"):
            try:
                schema.find_paths(input_type="entries", return_data_name="id")
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="6. Helpful methods, get_input_id_dict"):
            test_dict = schema.get_input_id_dict("polymer_entity_instance")
            polymer_instance_keys = ["entry_id", "asym_id"]
            for key in polymer_instance_keys:
                self.assertIn(key, test_dict.keys())
            for value in test_dict.values():
                self.assertIsNotNone(value)

        with self.subTest(msg="7. Troubleshooting, Not a unique field"):
            with self.assertRaises(ValueError):
                query = DataQuery(input_type="entries", input_ids=["4HHB"], return_data_list=["id"])
                try:
                    query = DataQuery(input_type="entries", input_ids=["4HHB"], return_data_list=["entry.id"])
                except Exception as error:
                    self.fail(f"Failed unexpectedly: {error}")

    def testAddExamples(self):
        with self.subTest(msg="1. Entries"):
            try:
                query = DataQuery(input_type="entries", input_ids=["1STP", "2JEF", "1CDG"], return_data_list=["entries.rcsb_id", "struct.title", "exptl.method"])
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="2. Primary Citation"):
            try:
                query = DataQuery(
                    input_type="entries",
                    input_ids=["1STP", "2JEF", "1CDG"],
                    return_data_list=[
                        "entries.rcsb_id",
                        "rcsb_accession_info.initial_release_date",
                        "audit_author.name",
                        "rcsb_primary_citation.pdbx_database_id_PubMed",
                        "rcsb_primary_citation.pdbx_database_id_DOI",
                    ],
                )
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="3. Polymer Entities"):
            try:
                query = DataQuery(
                    input_type="polymer_entities",
                    input_ids=["2CPK_1", "3WHM_1", "2D5Z_1"],
                    return_data_list=[
                        "polymer_entities.rcsb_id",
                        "rcsb_entity_source_organism.ncbi_taxonomy_id",
                        "rcsb_entity_source_organism.ncbi_scientific_name",
                        "cluster_id",
                        "identity",
                    ],
                )
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="4. Polymer Instances"):
            try:
                query = DataQuery(
                    input_type="polymer_entity_instances",
                    input_ids=["4HHB.A", "12CA.A", "3PQR.A"],
                    return_data_list=[
                        "polymer_entity_instances.rcsb_id",
                        "rcsb_polymer_instance_annotation.annotation_id",
                        "rcsb_polymer_instance_annotation.name",
                        "rcsb_polymer_instance_annotation.type",
                    ],
                )
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="5. Carbohydrates"):
            try:
                query = DataQuery(
                    input_type="branched_entities",
                    input_ids=["5FMB_2", "6L63_3"],
                    return_data_list=["pdbx_entity_branch.type", "pdbx_entity_branch_descriptor.type", "pdbx_entity_branch_descriptor.descriptor"],
                )
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="6. Sequence Positional Features"):
            try:
                query = DataQuery(
                    input_type="polymer_entity_instances",
                    input_ids={"instance_ids": ["1NDO.A"]},
                    return_data_list=[
                        "polymer_entity_instances.rcsb_id",
                        "rcsb_polymer_instance_feature.type",
                        "rcsb_polymer_instance_feature.feature_positions.beg_seq_id",
                        "rcsb_polymer_instance_feature.feature_positions.end_seq_id",
                    ],
                )
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="7. Reference Sequence Identifiers"):
            try:
                query = DataQuery(
                    input_type="entries",
                    input_ids=["7NHM", "5L2G"],
                    return_data_list=[
                        "entries.rcsb_id",
                        "polymer_entities.rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                        "polymer_entities.rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_name",
                    ],
                )
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="8. Chemical Components"):
            try:
                query = DataQuery(
                    input_type="chem_comps",
                    input_ids=["NAG", "EBW"],
                    return_data_list=[
                        "chem_comps.rcsb_id",
                        "chem_comp.type",
                        "chem_comp.formula_weight",
                        "chem_comp.name",
                        "chem_comp.formula",
                        "rcsb_chem_comp_info.initial_release_date",
                    ],
                )
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

        with self.subTest(msg="9. Computed Structure Models"):
            try:
                query = DataQuery(input_type="entries", input_ids=["AF_AFP68871F1"], return_data_list=["ma_qa_metric_global.type", "ma_qa_metric_global.value"])
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

    def testQuickstartNotebook(self):
        with self.subTest(msg="1. Initialize Schema"):
            schema = DataSchema()
        with self.subTest(msg="2. GraphQL example query"):
            query = """
            {
            entry(entry_id: "4HHB") {
                rcsb_entry_info {
                nonpolymer_bound_components
                }
            }
            }
            """
            response_json = requests.post(headers={"Content-Type": "application/graphql"}, data=query, url=const.DATA_API_ENDPOINT, timeout=config.DATA_API_TIMEOUT).json()
            self.assertNotIn("errors", response_json.keys())
        with self.subTest(msg="4. Making Queries"):
            try:
                query = DataQuery(input_type="entries", input_ids=["4HHB"], return_data_list=["nonpolymer_bound_components"])
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="5. input_ids, mult args"):
            try:
                query = DataQuery(input_type="polymer_entity_instances", input_ids=["4HHB.A"], return_data_list=["nonpolymer_bound_components"])
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="6. input_ids, list as entry input_ids"):
            try:
                query = DataQuery(input_type="entries", input_ids=["4HHB"], return_data_list=["nonpolymer_bound_components"])
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="7. input_ids, list as polymer instance input_ids"):
            try:
                query = DataQuery(input_type="polymer_entity_instances", input_ids=["4HHB.A"], return_data_list=["nonpolymer_bound_components"])
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="8. return_data_list, Not a unique field error"):
            with self.assertRaises(ValueError):
                query = DataQuery(input_type="polymer_entity_instances", input_ids=["4HHB.A"], return_data_list=["polymer_composition"])
                query.exec()
        with self.subTest(msg="9. return_data_list, find_paths() methods"):
            try:
                schema = DataSchema()
                schema.find_paths("polymer_entity_instances", "polymer_composition")
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="10. return_data_list, corrected query with non-redundant field"):
            try:
                query = DataQuery(input_type="entries", input_ids=["4HHB"], return_data_list=["rcsb_entry_info.polymer_composition"])
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="11. find_field_names()"):
            try:
                schema.find_field_names("polymer_composition")
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
            try:
                schema.find_field_names("comp")
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="12. More complex queries, multiple ids"):
            try:
                query = DataQuery(input_type="entries", input_ids=["4HHB", "12CA", "3PQR"], return_data_list=["nonpolymer_bound_components"])
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="13. More complex queries, multiple return data"):
            try:
                query = DataQuery(
                    input_type="entries", input_ids=["4HHB"], return_data_list=["citation.title", "nonpolymer_bound_components", "rcsb_entry_info.polymer_composition"]
                )
                query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

    def testSearchDataNotebook(self):
        with self.subTest(msg="1. Construct search API query and request"):
            # search API query and request
            try:
                q1 = attrs.rcsb_entity_source_organism.taxonomy_lineage.name == "COVID-19 virus"
                q2 = attrs.rcsb_nonpolymer_entity_annotation.type == "SUBJECT_OF_INVESTIGATION"
                q3 = attrs.rcsb_polymer_entity_feature_summary.type == "modified_monomer"
                query = q1 & q2 & q3
                result_list = query()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
            self.assertGreaterEqual(len(list(result_list)), 10)
        with self.subTest(msg="2. Construct data API query and parse result"):
            try:
                data_query = DataQuery(
                    input_type="entries",
                    # input ids removed because "rcsb_nonpolymer_instance_validation_score" is None: "6W61", "7ARF", "7JPZ", "7JQ3"
                    input_ids=["7AWU", "7C8B", "7JP0", "7JQ0", "7JQ1", "7JQ2"],
                    return_data_list=[
                        "entries.rcsb_id",
                        "rcsb_nonpolymer_entity_instance_container_identifiers.comp_id",
                        "is_subject_of_investigation",
                        "citation.title",
                        "citation.pdbx_database_id_DOI",
                    ],
                )
                data_query.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
            try:
                json = data_query.get_response()["data"]["entries"]
                json[0]["rcsb_id"]
                json[0]["nonpolymer_entities"]
                json[0]["nonpolymer_entities"][0]["nonpolymer_entity_instances"]
                json[0]["nonpolymer_entities"][0]["nonpolymer_entity_instances"][0]["rcsb_nonpolymer_instance_validation_score"][0]["is_subject_of_investigation"]
                json[0]["nonpolymer_entities"][0]["nonpolymer_entity_instances"][0]["rcsb_nonpolymer_entity_instance_container_identifiers"]["comp_id"]
                json[0]["citation"][0]["title"]
                json[0]["citation"][0]["pdbx_database_id_DOI"]
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")


def buildQuery():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(QueryTests("testGetEditorLink"))
    suiteSelect.addTest(QueryTests("testExec"))
    suiteSelect.addTest(QueryTests("testLowercaseIds"))
    suiteSelect.addTest(QueryTests("testBatchIDs"))
    suiteSelect.addTest(QueryTests("testDocs"))
    suiteSelect.addTest(QueryTests("testAddExamples"))
    suiteSelect.addTest(QueryTests("testQuickstartNotebook"))
    suiteSelect.addTest(QueryTests("testSearchDataNotebook"))
    return suiteSelect


if __name__ == "__main__":
    mySuite = buildQuery()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
