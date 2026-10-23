import numpy as np


def beam_search(log_probs, start, eos, beam_size, max_len):
    v = log_probs.shape[1]
    beams, finished = [((), 0.0)], []
    for _ in range(max_len):
        cands = []
        for seq, score in beams:
            last = seq[-1] if seq else start
            for tok in range(v):
                cands.append((seq + (tok,), score + float(log_probs[last, tok])))
        cands.sort(key=lambda c: -c[1])
        beams = []
        for seq, score in cands[:beam_size]:
            (finished if seq[-1] == eos else beams).append((seq, score))
        if not beams:
            break
    seq, score = max(finished + beams, key=lambda c: c[1])
    return list(seq), score
