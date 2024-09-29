import torch
import numpy as np


def is_normalized(array):
    return np.isclose(np.linalg.norm(array), 1.0)


def normalize_rows(array):
    return array / np.linalg.norm(array, axis=-1, keepdims=True)


def torch_normalize_rows(tensor):
    return torch.nn.functional.normalize(tensor, p=2, dim=-1)


def get_avg_embedding(embedding):
    embedding = np.atleast_2d(embedding)
    embedding = embedding.mean(axis=0)
    return embedding


def get_llama_embedding(
        word,
        model,
        tokenizer,
        add_special_tokens=False,
        normalized=False,
        aggregation="none"
):
    inputs = tokenizer.encode(
        word,
        return_tensors="pt",
        padding=True,
        truncation=True,
        add_special_tokens=add_special_tokens
    ).to(model.device)

    embed_layer = model.get_input_embeddings()
    with torch.no_grad():
        embedding = embed_layer(inputs)

    embedding = embedding.squeeze().cpu().numpy() 
    tokens = inputs.squeeze().cpu().numpy()
    
    # Normalize the vectors
    if normalized:
        embedding = normalize_rows(embedding)

    # Aggregate embeddings
    if aggregation == "mean":
        embedding = np.atleast_2d(embedding)
        embedding = embedding.mean(axis=0)
        embedding = embedding.squeeze()
    elif aggregation == "sum":
        embedding = np.atleast_2d(embedding)
        embedding = embedding.sum(axis=0)
        embedding = embedding.squeeze()
    elif aggregation == "none":
        pass
    else:
        raise ValueError(f"Invalid aggregation method {aggregation}")

    return embedding, tokens


def get_word2vec_embedding(word, model):
    try:
        return model[word]
    except KeyError:
        return None
