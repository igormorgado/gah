import requests
import json
import pandas as pd

import spacy
import rebel_spacy
import torch

from neo4j import GraphDatabase

from graphs import (
    explode_columns,
    run_query,
    get_all_relationships,
    get_all_nodes,
    cleanup_database,
    create_relationship,
    create_node,
)

from spacy_custom import get_relations
from utils import get_wikipedia_summary
from config import load_config


if torch.cuda.is_available():
    torch_device = "gpu" 
    rebel_device = 0
else:
    torch_device ="cpu"
    rebel_device = -1

config, secrets = load_config()

relext_pipeline = spacy.load('en_core_web_sm', disable=['ner', 'lemmatizer', 'attribute_rules', 'tagger'])

rebel_config_params = {
    'device': rebel_device,
    'model_name': 'Babelscape/rebel-large'
}

rebel_comp = relext_pipeline.add_pipe("rebel", config=rebel_config_params)

entity = "Jon Snow (character)"
summary = get_wikipedia_summary(entity)

# Corefs resolve
coref_pipeline = spacy.load("en_core_web_sm")
# Creates doc._.coref_chains
coref_comp = coref_pipeline.add_pipe('coreferee')

relations = get_relations(summary, coref_pipeline, relext_pipeline)

## Build relations

with open("relationship_import.cypher") as file:
    query = file.read()

driver = GraphDatabase.driver(config.neo4j.uri, auth=(config.neo4j.username, secrets.neo4j_password))

with driver.session() as session:
    summary = cleanup_database(session)
    session.execute_write(run_query, query, parameters={'data': relations})

# Return relationships/nodes as dataframes.
with driver.session() as session:
    rels = session.execute_read(get_all_relationships)
    nodes = session.execute_read(get_all_nodes)

rels_df = explode_columns(pd.DataFrame(rels))
nodes_df = explode_columns(pd.DataFrame(nodes))

print(rels_df.head())
