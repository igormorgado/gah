from typing import Any
from pydantic import BaseModel, Field


def clean_dict(d):
    if not isinstance(d, dict):
        return d
    return {k: clean_dict(v) for k, v in d.items() if v is not None}


class Neo4jNode(BaseModel):
    # Neo4j Features
    element_id: str
    labels: list[str] | None = None
    properties: dict[str, Any] | None = None


class TextualFeatures(BaseModel):
    text: str | None = None
    lemma: str | None = None
    pos: str | None = None
    tag: str | None = None


class Token(Neo4jNode):
    # Textual Feature
    properties: TextualFeatures | None = None
        
    def to_neo4j(self):
        data = self.model_dump()
        del data['elementId']
        data = clean_dict(data)
        return data

    def from_spacy(self):
        """Takes a spacy token and build a Token object"""


class Relationship(BaseModel):
    # Neo4j Features
    type_: str
    #direction: str
    source: str
    target: str
    properties: dict[str, Any] | None = None
    