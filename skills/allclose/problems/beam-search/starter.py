import numpy as np


def beam_search(log_probs, start, eos, beam_size, max_len):
    """Beam search over a bigram table log_probs[last, next]. Returns (tokens: list[int], score: float)."""
    raise NotImplementedError
