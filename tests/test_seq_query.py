##
# File:    testschema.py
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
import unittest
# import rustworkx as rx
# import networkx as nx

from rcsbapi.sequence.seq_query import Alignments, GroupAlignments, Annotations, GroupAnnotations, GroupAnnotationsSummary, AnnotationFilterInput

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SeqTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__startTime = time.time()
        logger.info("Starting %s at %s", self.id().split(".")[-1], time.strftime("%Y %m %d %H:%M:%S", time.localtime()))

    def tearDown(self) -> None:
        endTime = time.time()
        logger.info("Completed %s at %s (%.4f seconds)", self.id().split(".")[-1], time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - self.__startTime)

    def testAnnotations(self) -> None:
        with self.subTest(msg="1. Annotations query with filter"):
            try:
                query_obj = Annotations(
                    reference="NCBI_GENOME",
                    sources=["PDB_INSTANCE"],
                    queryId="NC_000001",
                    filters=[
                        AnnotationFilterInput(
                            field="TYPE",
                            operation="EQUALS",
                            values=["BINDING_SITE"],
                            source="UNIPROT"
                        )
                    ],
                    return_data_list=["features.description"]
                )
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

    def testAlignments(self) -> None:
        with self.subTest(msg="1. Alignments query without filter"):
            try:
                query_obj = Alignments(
                    from_="NCBI_PROTEIN",
                    to="PDB_ENTITY",
                    queryId="XP_642496",
                    return_data_list=["target_id"]
                )
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="2. Alignments query with range"):
            try:
                query_obj = Alignments(
                    from_="NCBI_PROTEIN",
                    to="PDB_ENTITY",
                    queryId="XP_642496",
                    range=[1, 10],
                    return_data_list=["target_id"]
                )
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

    def testGroupAlignments(self) -> None:
        with self.subTest(msg="1. group_alignments query without filter"):
            try:
                query_obj = GroupAlignments(
                    group="MATCHING_UNIPROT_ACCESSION",
                    groupId="P01112",
                    return_data_list=["target_id"],
                )
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="2. group_alignments query with filter"):
            try:
                query_obj = GroupAlignments(
                    group="MATCHING_UNIPROT_ACCESSION",
                    groupId="P01112",
                    return_data_list=["target_id"],
                    filter=["8CNJ_1", "8FG4_1"]
                )
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

    def testGroupAnnotations(self) -> None:
        with self.subTest(msg="1. group_annotations query without filter"):
            try:
                query_obj = GroupAnnotations(
                    group="MATCHING_UNIPROT_ACCESSION",
                    groupId="P01112",
                    sources=["PDB_ENTITY"],
                    return_data_list=["target_id"]
                )
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="2. group_annotations query with filter"):
            try:
                query_obj = GroupAnnotations(
                    group="MATCHING_UNIPROT_ACCESSION",
                    groupId="P01112",
                    sources=["PDB_ENTITY"],
                    filters=[
                        AnnotationFilterInput(
                            field="TYPE",
                            operation="EQUALS",
                            values=["BINDING_SITE"],
                            source="UNIPROT"
                        )
                    ],
                    return_data_list=["target_id"]
                )
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")

    def testGroupAnnotationsSummary(self) -> None:
        with self.subTest(msg="1. group_annotations_summary query without filter"):
            try:
                query_obj = GroupAnnotationsSummary(
                    group="MATCHING_UNIPROT_ACCESSION",
                    groupId="P01112",
                    sources=["PDB_INSTANCE"],
                    return_data_list=["target_id", "features.type"]
                )
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")
        with self.subTest(msg="2. group_annotations_summary query with filter"):
            try:
                query_obj = GroupAnnotationsSummary(
                    group="MATCHING_UNIPROT_ACCESSION",
                    groupId="P01112",
                    sources=["PDB_INSTANCE"],
                    filters=[
                        AnnotationFilterInput(
                            field="TYPE",
                            operation="EQUALS",
                            values=["BINDING_SITE"],
                            source="UNIPROT"
                        )
                    ],
                    return_data_list=["target_id", "features.type"]
                )
                query_obj.exec()
            except Exception as error:
                self.fail(f"Failed unexpectedly: {error}")


def buildQuery() -> unittest.TestSuite:
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(SeqTests("testAnnotations"))
    suiteSelect.addTest(SeqTests("testAlignments"))
    suiteSelect.addTest(SeqTests("testGroupAlignments"))
    suiteSelect.addTest(SeqTests("testGroupAnnotations"))
    suiteSelect.addTest(SeqTests("testGroupAnnotationsSummary"))
    return suiteSelect


if __name__ == "__main__":
    mySuite = buildQuery()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
