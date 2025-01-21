"""
Constants for rcsb-api (immutable and cannot be overridden)

These constants define fixed values used throughout the rcsb-api package,
including API endpoints, search services, and schema URLs. The values are
immutable and protected from modification during runtime.
"""

from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import List


@dataclass(frozen=True)
class Const:
    # Search API constants
    STRUCTURE_INDEX: int = 0
    CHEMICAL_INDEX: int = 0
    SEARCH_API_REQUEST_SCHEMA_URL: str = "https://search.rcsb.org/schema/search/request/json-schema-rcsb_search_query.json"
    SEARCH_OPENAPI_SCHEMA_URL: str = "https://search.rcsb.org/openapi.json"
    STRUCTURE_ATTRIBUTE_SEARCH_SERVICE: str = "text"
    CHEMICAL_ATTRIBUTE_SEARCH_SERVICE: str = "text_chem"
    FULL_TEXT_SEARCH_SERVICE: str = "full_text"
    SEQUENCE_SEARCH_SERVICE: str = "sequence"
    SEQMOTIF_SEARCH_SERVICE: str = "seqmotif"
    STRUCT_SIM_SEARCH_SERVICE: str = "structure"
    STRUCTMOTIF_SEARCH_SERVICE: str = "strucmotif"
    CHEM_SIM_SEARCH_SERVICE: str = "chemical"
    SEQUENCE_SEARCH_MIN_NUM_OF_RESIDUES: int = 25
    SEQMOTIF_SEARCH_MIN_CHARACTERS: int = 2
    STRUCT_MOTIF_MIN_RESIDUES: int = 2
    STRUCT_MOTIF_MAX_RESIDUES: int = 10
    RCSB_SEARCH_API_QUERY_URL: str = "https://search.rcsb.org/rcsbsearch/v2/query"
    UPLOAD_URL: str = "https://user-upload.rcsb.org/v1/putMultipart"
    RETURN_UP_URL: str = "https://user-upload.rcsb.org/v1/download/"

    SEARCH_API_SCHEMA_DIR: str = "search/resources"
    SEARCH_API_STRUCTURE_ATTRIBUTE_SCHEMA_URL: str = "http://search.rcsb.org/rcsbsearch/v2/metadata/schema"
    SEARCH_API_STRUCTURE_ATTRIBUTE_SCHEMA_FILENAME: str = "structure_schema.json"
    SEARCH_API_CHEMICAL_ATTRIBUTE_SCHEMA_URL: str = "https://search.rcsb.org/rcsbsearch/v2/metadata/chemical/schema"
    SEARCH_API_CHEMICAL_ATTRIBUTE_SCHEMA_FILENAME: str = "chemical_schema.json"

    # Data API constants
    DATA_API_ENDPOINT: str = "https://data.rcsb.org/graphql"
    DATA_API_SCHEMA_DIR: str = "data/resources"
    DATA_API_SCHEMA_FILENAME: str = "data_api_schema.json"
    DATA_API_SCHEMA_BASE_URL: str = "https://data.rcsb.org/rest/v1/schema/"
    DATA_API_SCHEMA_ENDPOINT_TO_FILE: MappingProxyType[str, str] = MappingProxyType({
        "entry": "entry.json",
        "polymer_entity": "polymer_entity.json",
        "branched_entity": "branched_entity.json",
        "nonpolymer_entity": "nonpolymer_entity.json",
        "polymer_entity_instance": "polymer_entity_instance.json",
        "branched_entity_instance": "branched_entity_instance.json",
        "nonpolymer_entity_instance": "nonpolymer_entity_instance.json",
        "assembly": "assembly.json",
        "chem_comp": "chem_comp.json",
        "pubmed": "pubmed.json",
        "uniprot": "uniprot.json",
        "drugbank": "drugbank.json",
    })

    SINGULAR_TO_PLURAL: MappingProxyType[str, str] = MappingProxyType({
        "entry": "entries",
        "polymer_entity": "polymer_entities",
        "branched_entity": "branched_entities",
        "nonpolymer_entity": "nonpolymer_entities",
        "polymer_entity_instance": "polymer_entity_instances",
        "nonpolymer_entity_instance": "nonpolymer_entity_instances",
        "branched_entity_instance": "branched_entity_instances",
        "assembly": "assemblies",
        "interface": "interfaces",
        "uniprot": "",
        "pubmed": "",
        "chem_comp": "chem_comps",
        "entry_group": "entry_groups",
        "polymer_entity_group": "polymer_entity_groups",
        "group_provenance": ""
    })
    #
    ID_TO_SEPARATOR: MappingProxyType[str, str] = MappingProxyType({
        "entity_id": "_",
        "asym_id": ".",
        "assembly_id": "-",
        "interface_id": "."
    })

    # Regex strings for IDs
    DATA_API_INPUT_TYPE_TO_REGEX: MappingProxyType[str, List[str]] = MappingProxyType({
        "entry": [r"^(MA|AF|ma|af)_[A-Z0-9]*$", r"^[A-Za-z0-9]{4}$"],
        "entity": [r"^(MA|AF|ma|af)_[A-Z0-9]*_[0-9]+$", r"^[A-Z0-9]{4}_[0-9]+$"],
        "instance": [r"^(MA|AF|ma|af)_[A-Z0-9]*\.[A-Za-z]$", r"^[A-Z0-9]{4}\.[A-Za-z]$"],
        "assembly": [r"^(MA|AF|ma|af)_[A-Z0-9]*-[0-9]+$", r"^[A-Z0-9]{4}-[0-9]+$"],
        "interface": [r"^(MA|AF|ma|af)_[A-Z0-9]*-[0-9]+\.[0-9]+$", r"^[A-Z0-9]{4}-[0-9]+\.[0-9]+$"],
        # Regex for uniprot: https://www.uniprot.org/help/accession_numbers
        "uniprot": [r"[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}"]
    })


@dataclass(frozen=True)
class SeqConst:
    API_ENDPOINT: str = "https://sequence-coordinates.rcsb.org"


seq_const = SeqConst()
const = Const()
