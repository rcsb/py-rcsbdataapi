"""RCSB PDB Sequence Coordinates API."""
from rcsbapi.sequence.seq_schema import SeqSchema

SEQ_SCHEMA = SeqSchema()

from rcsbapi.sequence.seq_query import Alignments, GroupAlignments, Annotations, GroupAnnotations, GroupAnnotationsSummary, AnnotationFilterInput  # noqa: E402

__all__ = [
    "AnnotationFilterInput",
    "SeqSchema",
    "alignments",
    "annotations",
    "group_alignments",
    "group_annotations",
    "group_annotations_summary",
]
