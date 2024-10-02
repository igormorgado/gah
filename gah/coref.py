import spacy

def join_with_and(items):
    if len(items) == 0:
        return ""
    elif len(items) == 1:
        return str(items[0])
    elif len(items) == 2:
        return f"{items[0]} and {items[1]}"
    else:
        return ", ".join(items[:-1]) + f", and {items[-1]}"


def find_coref(
    token: spacy.tokens.token.Token | None,
    doc: spacy.tokens.doc.Doc
) -> spacy.tokens.span.Span | None:
    """Find the first match a token in of doc entities

    `doc.ents` consists of a list of `spans` of entities in the given document.
    Each `span` is a pointer, with `start` and `end` attributes that indicates 
    the positions of a given span in the `doc` object. Each `doc` is composed
    of a sequence of `tokens`.
    """
    corefs = doc._.coref_chains.resolve(token)
    entities = []
    if corefs:
        for coref in corefs:
            for ent in doc.ents:
                if coref in ent:
                    entities.append(ent)
    return entities


def build_coref(doc: spacy.tokens.doc.Doc) -> list:
    resolved_text = []
    for token in doc:
        coref = find_coref(token, doc)
        if coref:
            resolved_text.append(coref)
        else:
            resolved_text.append(token)    

    return resolved_text


def resolve_references_coreferee(doc) -> str:
    resolved_tokens = []
    for token in doc:
        coref = find_coref(token, doc)
        if coref:
            resolved_tokens.append(coref)
        else:
            resolved_tokens.append(token)      

    sentence = ""
    for entry in resolved_tokens:
        if isinstance(entry, list):
            joined_entry = join_with_and(entry)
            last_entry = entry[-1]
            last_token = last_entry[-1]
            whitespace = doc[last_token.i+1].whitespace_
            sentence += joined_entry + whitespace
        elif isinstance(entry, spacy.tokens.token.Token):
            sentence += entry.text + entry.whitespace_

    return sentence


def resolve_references(doc: spacy.tokens.doc.Doc) -> str:
    """Function for resolving references with the coref output
    doc (Doc): The doc object processed by coref pipeline
    RETURNS (str): The doc string with resolved references
    """
    # Saves token_id: reference_text
    token_mention_mapper = {}
    output_string = ""
    clusters = [val for key, val in doc.spans.items() if key.startswith("coref_cluster")]

    for cluster in clusters:
        # Saves first span of every cluster
        first_mention = cluster[0]
        # Iterate though every other span in the cluster
        for mentions in list(cluster)[1:]:
            token_mention_mapper[mentions[0].idx] = first_mention.text
            for token in mentions[1:]:
                # Set empty string for every other token
                token_mention_mapper[token.idx] = ""

    # Iterate through every token in doc
    for token in doc:
        
        if token.idx in token_mention_mapper:
            # Check if token exists in token_mention_mapper
            output_string += token_mention_mapper[token.idx] + token.whitespace_
        else:
            # Add original text
            output_string += token.text + token.whitespace_

    return output_string