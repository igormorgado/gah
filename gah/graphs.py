import re
from collections.abc import Iterable, Mapping
from typing import Any

import json
import pandas as pd
import uuid
from neo4j._sync.work import Session
from neo4j._sync.work.transaction import Transaction, ManagedTransaction



def explode_iter_column(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Explode a column of lists into multiple columns.

    Parameters
    ==========
    df (pandas.DataFrame): Input dataframe
    column_name (str): Name of the column to explode

    Returns
    =======
    pandas.DataFrame: Dataframe with exploded columns
    """
    # Get all unique values from the specified column
    all_values = sorted(set([value for values in df[column_name] for value in values]))

    # Create new columns for each unique value
    new_columns = []
    for value in all_values:
        new_column_name = column_name + "__" + value
        new_columns.append(new_column_name)
        df[new_column_name] = df[column_name].apply(lambda x: int(value in x))

    # Convert to numeric.
    for col in new_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype(bool)

    # Drop the original column
    df = df.drop(column_name, axis=1)

    return df


def explode_map_column(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Explode a column of dictionary into multiple columns.

    Parameters
    ==========
    df (pandas.DataFrame): Input dataframe
    column_name (str): Name of the column to explode

    Returns
    =======
    pandas.DataFrame: Dataframe with exploded columns
    """
    # Extract the dictionary keys to use as new column names
    new_columns = list(df[column_name].iloc[0].keys())

    # Create new columns from the dictionary values
    for col in new_columns:
        df["props__" + col] = df[column_name].apply(lambda x: x.get(col))

    # Drop the original dictionary column
    df = df.drop(columns=[column_name])

    return df


def explode_columns(
    df: pd.DataFrame,
    columns: list[str] | str = ['properties', 'props', 'labels'],
    on_errors: str = "ignore"
) -> pd.DataFrame | None:
    """Explode a column in multiple columns.
    
    Here we naivily assume that the whole column will treated as a single
    type. If this is not the case, things will probabliy break. Caller 
    must make proper checks and cleaning before passing to this functions.

    We will not add checks for every row of every column in each call.
    This MUST be done by the caller and provide a dataframe that is 
    sanitized. It's recommended, if unsure, pass call the method 
    `.convert_dtypes()` to sanitize th DataFrame.

    on_errors values can be
       "ignore": Ignore errors, keep going.
       "raise:  Raise an exception. Can be handled elsewere.
       "stop": Stop processing
    """
    
    # Column parameter must be always a list
    if isinstance(columns, str):
        columns = [columns]

    #if df is None:
    #    return None
        
    new_df = df.copy()
    for column in columns:
        # Check if column exist in DataFrame
        if column not in new_df.columns:
            if on_errors == "ignore":
                continue
            elif on_errors == "raise":
                raise KeyError(f"Column '{column}' not found in the dataframe")
            elif on_errors == "stop":
                break

        # Column MUST be object dtype.
        if not pd.api.types.is_object_dtype(df[column]):
            if on_errors == "ignore":
                continue
            elif on_errors == "raise":
                raise TypeError(f"Column '{column}'. Not `object` dtype, it is `{str(df[column].dtype)}`.")  
            elif on_errors == "stop":
                break
        
        # Naive assumption. All types in column are the same.
        sample = new_df[column].iloc[0]
        if isinstance(sample, Mapping):
            new_df = explode_map_column(new_df, column)
        elif isinstance(sample, Iterable):
            new_df = explode_iter_column(new_df, column)
        else:
            if on_errors == "ignore":
                continue
            elif on_errors == "raise":
                raise NotImplementedError(f"Column {column} of type {type(sample)} not supported")
            elif on_errors == "stop":
                break

    return new_df


def run_query(
        txn: Session | Transaction | ManagedTransaction,
        query: str,
        parameters: dict | None = None
) -> pd.DataFrame | None:
    """Run a neo4j query over a transaction or session and return a dataframe"""

    result = txn.run(query=query, **parameters)
    columns = result.keys()
    records = [record.values() for record in result]
    if records:
        df = pd.DataFrame(records, columns=columns)
    else:
        df = None

    return df


def query_to_list(
    session: Session | Transaction | ManagedTransaction,
    query: str,
    parameters: dict | None = None
) -> tuple[list[str], list[Any]]:
    results = session.run(query=query, parameters=parameters)
    columns = list(results.keys())
    data = [record.values() for record in results]
    return columns, data


def query_to_records(
    session: Session | Transaction | ManagedTransaction,
    query: str,
    parameters: dict | None = None
) -> tuple[list[str], list[Any]]:
    results = session.run(query=query, parameters=parameters)
    columns = results.keys()
    data = [record for record in results]
    return columns, data


def query_to_df(
    session: Session | Transaction | ManagedTransaction,
    query: str,
    parameters: dict | None = None
) -> pd.DataFrame:
    results = session.run(query=query, parameters=parameters)
    columns = results.keys()
    data = [[record[col] for col in columns] for record in results]
    df = pd.DataFrame(data, columns=columns)
    return df


def query_to_json(
    session: Session | Transaction | ManagedTransaction,
    query: str,
    parameters: dict | None = None
) -> dict:
    results = session.run(query, parameters)
    data = [record.data() for record in results]
    return json.dumps(data)


def extract_relationship_json(relationship: dict) -> dict:
    return {
        "element_id": relationship.element_id,
        "type": relationship.type,
        "start_node_element_id": relationship.start_node.element_id,
        "end_node_element_id": relationship.end_node.element_id,
        "properties": dict(relationship)
    }


def extract_node_json(node: dict) -> dict:
    return {
        "element_id": node.element_id,
        "labels": list(node.labels),
        "properties": dict(node)
    }


def get_all_relationships(
    txn: Session | Transaction | ManagedTransaction,
) -> list[dict]:
    query = "MATCH ()-[relationship]->() RETURN relationship"
    result = txn.run(query=query, parameters=parameters)
    relationships = [
        extract_relationship_json(record["relationship"])
        for record in result
    ]
    return relationships


def get_all_nodes(
    txn: Session | Transaction | ManagedTransaction,
) -> list[dict]:
    query = "MATCH (node) RETURN node"
    result = txn.run(query=query)
    nodes = [
        extract_node_json(record["node"])
        for record in result
    ]
    return nodes


def cleanup_database(
    txn: Session | Transaction | ManagedTransaction,
) -> dict:
    """This query deletes all nodes and relationships in the database"""
    query = "MATCH (n) DETACH DELETE n"
    result = txn.run(query=query)
    summary = result.consume()
    return summary


def sanitize_label(label: str) -> str:
    """
    Sanitize the label to prevent Cypher injection.
    Allows only alphanumeric characters and underscores.
    """
    if re.match(r'^\w+$', label):
        return label
    else:
        raise ValueError(f"Invalid label: {label}")


def create_relationship(txn, relationship):
    type_str = f": {relationship['type']}" if "type" in relationship else ""
    query = (
        "MATCH (source), (target) "
        "WHERE source.uuid = $source AND target.uuid = $target "   # ADD UUID MATCH HERE
        f"CREATE (source)-[r{type_str}]->(target) "
        "SET r += $rel_types "
        "RETURN type(r)"
    )
    # Include all attributes except 'source', 'target', and 'type'
    keys_to_exclude = ['source', 'target', 'type']
    rel_types = {k: v for k, v in relationship.items() if k not in keys_to_exclude}

    txn.run(
        query,
        source=relationship["source"],
        target=relationship["target"],
        rel_types=rel_types,
    )


def create_node(txn, node):
    if isinstance(node.get("labels"), str):
        node["labels"] = [node["labels"]]
    # Handle multiple labels
    sanitized_labels = [sanitize_label(label) for label in node.get("labels")]
    labels_str = ':' + ':'.join(sanitized_labels)

    keys_to_exclude = ["labels"]
    node_types = {k: v for k, v in node.items() if k not in keys_to_exclude}

    if "uuid" not in props:
        props["uuid"] = uuid.uuid4()

    query = (
        f"CREATE (n{labels_str} $node_types)"
    )

    txn.run(query, node_types=node_types)
