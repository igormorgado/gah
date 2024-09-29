import torch
import mediawiki
from mediawiki import MediaWiki


def get_tensor_memory_usage(tensor: torch.Tensor):
    element_size = tensor.element_size()
    num_elements = tensor.numel()
    memory_bytes = element_size * num_elements
    gb = 1024 ** 3
    memory_gb = memory_bytes / gb
    return memory_gb


def get_wikipedia_summary(page) -> str | None:
    summary = None
    try:
        wikipedia = MediaWiki()
        page = wikipedia.page(page)
        summary = page.summary
    except mediawiki.PageError as e:
        print(f"Couldn't parse text for {page} due to {e}")
    except mediawiki.DisambiguationError as e:
        print(f"Page ambiguity: {e}")

    return summary