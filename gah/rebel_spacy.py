from spacy import Language, util
from spacy.tokens import Doc, Span
from transformers import pipeline
from typing import List
import re
import hashlib
import requests


def get_wiki_id(item):
    try:
        url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={item}&language=en&format=json"
        data = requests.get(url).json()
        # Return the first id (Could upgrade this in the future)
        return data['search'][0]['id']
    except (KeyError, IndexError):
        print(f"Missing key for {item}.")
        return 'id-less'


def extract_triplets(text: str) -> List[dict]:
    """
    parses the text to triplets
    1. Split the text into tokens
    2. If the token is <triplet>, <subj>, or <obj>, then set the current variable to the appropriate value
    3. If the token is not one of the above, then append it to the appropriate variable
    4. If the current variable is <subj>, then append the triplet to the list of triplets

    :param text: str - the text to be parsed
    :type text: str
    :return: A list of dictionaries.
    """

    triplets = []
    relation, subject, relation, object_ = "", "", "", ""
    current = "x"
    
    text = text.strip()
    cleaned_tokens = text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split()
    for token in cleaned_tokens:
        if (token == "<triplet>"):
            current = "t"
            if (relation != ""):
                triplets.append(
                        {
                            "head": subject.strip(),
                            "type": relation.strip(),
                            "tail": object_.strip()
                            }
                        )
                relation = ""
            subject = ""
        elif (token == "<subj>"):
            current = "s"
            if (relation != ""):
                triplets.append(
                    {
                        "head": subject.strip(),
                        "type": relation.strip(),
                        "tail": object_.strip()
                        }
                    )
            object_ = ""
        elif (token == "<obj>"):
            current = "o"
            relation = ""
        else:
            if (current == "t"):
                subject += " " + token
            elif (current == "s"):
                object_ += " " + token
            elif (current == "o"):
                relation += " " + token
    if ((subject != "") and (relation != "") and (object_ != "")):
        triplets.append(
                {
                    "head": subject.strip(),
                    "type": relation.strip(),
                    "tail": object_.strip()
                    }
                )
    return triplets


@Language.factory(
        "rebel",
        requires=["doc.sents"],
        assigns=["doc._.rel"],
        default_config={
            "model_name": "Babelscape/rebel-large",
            "device": 0,
            },
        )
class RebelComponent:

    def __init__(
        self,
        nlp,
        name,
        model_name: str,
        device: int,
    ):

        assert model_name is not None, ""

        self.triplet_extractor = pipeline(
            "text2text-generation",
            model=model_name,
            tokenizer=model_name,
            device=device
        )

        # Register custom extension on the Doc
        if (not Doc.has_extension("rel")):
            Doc.set_extension("rel", default={})

    def _generate_triplets(self, sents: List[Span]) -> List[List[dict]]:
        """
        1. We pass the text of the sentence to the triplet extractor.
        2. The triplet extractor returns a list of dictionaries.
        3. We extract the token ids from the dictionaries.
        4. We decode the token ids into text.
        5. We extract the triplets from the text.
        6. We return the triplets.

        The triplet extractor is a model that takes a sentence as input and returns a list of dictionaries.
        Each dictionary contains the token ids of the extracted triplets.

        The token ids are the numbers that represent the words in the sentence.
        For example, the token id of the word "the" is 2.

        The token ids are decoded into text using the tokenizer.
        The tokenizer is a model that takes a list of token ids as input and returns a list of words.

        :param sents: List[Span]
        :type sents: List[Span]
        :return: A list of lists of dicts.
        """
        # Makes the inference with Model
        output_ids = self.triplet_extractor(
            [sent.text for sent in sents],
            return_tensors=True,
            return_text=False
        )
        # Convert token ids to text.
        extracted_texts = self.triplet_extractor.tokenizer.batch_decode(
            [
                out["generated_token_ids"]
                for out in output_ids
            ]
        )
        # Process triplets from generated text and return as dictionary
        extracted_triplets = [extract_triplets(text) for text in extracted_texts]
        
        return extracted_triplets
    
    def set_annotations(self, doc: Doc, triplets: List[dict]):
        for triplet in triplets:
            # Remove self-loops (relationships that start and end at the entity)
            if triplet['head'] == triplet['tail']:
                continue
    
            # Use regex to search for entities
            head_span = re.search(triplet["head"], doc.text)
            tail_span = re.search(triplet["tail"], doc.text)
    
            # Skip the relation if both head and tail entities are not present in the text
            # Sometimes the Rebel model hallucinates some entities
            if not head_span or not tail_span:
                continue

            index_value = "".join(triplet.values())
            index = hashlib.sha1(index_value.encode('utf-8')).hexdigest()
            if index not in doc._.rel:
                # Get wiki ids and store results
                doc._.rel[index] = {
                    "relation": triplet["type"],
                    "head_span": {
                        'text': triplet['head'],
                        'id': get_wiki_id(triplet['head'])
                    },
                    "tail_span": {
                        'text': triplet['tail'],
                        'id': get_wiki_id(triplet['tail'])
                    }
                }

    def set_annotations_org(self, doc: Doc, triplets: List[dict]):
        """
        The function takes a spacy Doc object and a list of triplets (dictionaries) as input.
        For each triplet, it finds the substring in the Doc object that matches the head and tail of the triplet.
        It then creates a spacy span object for each of the head and tail.
        Finally, it creates a dictionary of the relation type, head span and tail span and adds it to the Doc object

        :param doc: the spacy Doc object
        :type doc: Doc
        :param triplets: List[dict]
        :type triplets: List[dict]
        """
        text = doc.text.lower()
        for triplet in triplets:
            if (triplet["head"] == triplet["tail"]):
                continue

            head_match = re.search(
                r'\b' + re.escape(triplet["head"].lower()) + r'\b', text)

            if head_match:
                head_index = head_match.start()
            else:
                head_index = text.find(triplet["head"].lower())
            
            tail_match = re.search(
                r'\b' + re.escape(triplet["tail"].lower()) + r'\b',
                text
            )

            if tail_match:
                tail_index = tail_match.start()
            else:
                tail_index = text.find(triplet["tail"].lower())

            if ((head_index == -1) or (tail_index == -1)):
                continue

            head_span = doc.char_span(
                head_index,
                head_index + len(triplet["head"]),
                alignment_mode = "expand"
            )
            tail_span = doc.char_span(
                tail_index,
                tail_index + len(triplet["tail"]),
                alignment_mode = "expand"
            )

            try:
                offset = (head_span.start, tail_span.start)
            except (AttributeError):
                continue

            if (offset not in doc._.rel):
                doc._.rel[offset] = {
                    "relation": triplet["type"],
                    "head_span": head_span,
                    "tail_span": tail_span,
                }
    
    def __call__(self, doc: Doc) -> Doc:
        """
        The function takes a doc object and returns a doc object

        :param doc: Doc
        :type doc: Doc
        :return: A Doc object with the sentence triplets added as annotations.
        """

        sentence_triplets = self._generate_triplets(doc.sents)
        for sentence_triplet in sentence_triplets:
            self.set_annotations(doc, sentence_triplet)

        return doc

    def pipe(self, stream, batch_size=128):
        """
        It takes a stream of documents, and for each document,
        it generates a list of sentence triplets,
        and then sets the annotations for each sentence in the document

        :param stream: a generator of Doc objects
        :param batch_size: The number of documents to process at a time, defaults to 128 (optional)
        """

        for docs in util.minibatch(stream, size=batch_size):
            sents = []
            for doc in docs:
                sents += doc.sents

            sentence_triplets = self._generate_triplets(sents)
            index = 0

            for doc in docs:
                n_sent = len(list(doc.sents))
                self.set_annotations(doc, sentence_triplets[index: index + n_sent])
                index += n_sent
                yield doc
