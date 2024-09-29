import spacy
from coref import resolve_references

## Relation extraction + entity linking
# Maybe in future separate entity linking from Relation Extraction. Entity
# linking is done inside `set_annotation` in `rebel_component`. In the 
# original `set_annotation` (the one with `_org` in name), the entity 
# linking with wikipedia didn't exist. The author of the article, made this
# shitty approach that needs to be replaced for something better. By better
# I mean, the entity linking should be done in a posterior step in pipeline
# when the relations were already created. Or it can be done, after the 
# corefence was solved, since we have already the canonical names for the
# each entity in the text.


def get_relations(text, coref_pipeline, relext_pipeline) -> list:
    # This is so badly written that is taking the pipelines from global
    # variables. This is so ugly that my eyes bleed. I need to fix ASAP.
    # This function depends on spacy coreferee and rebel modules
    # TODO(Igor): Update to use latest native spacy coreference resolution
    # TODO(Igor): Update the triplets extractor to not make entity linking.
    
   
    # Coreference 
    coref_doc = coref_pipeline(text)
    coref_text = resolve_references(coref_doc)

    # Relation extraction + entity linking
    relext_doc = relext_pipeline(coref_text)

    # Build relation dictionary
    params = [rel_dict for value, rel_dict in relext_doc._.rel.items()]
    
    return params


