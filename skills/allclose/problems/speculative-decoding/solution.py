import numpy as np


def speculative_accept(draft_tokens, draft_probs, target_probs, u):
    accepted = []
    for i, x in enumerate(draft_tokens):
        p, q = target_probs[i], draft_probs[i]
        if u[i] < min(1.0, p[x] / q[x]):
            accepted.append(int(x))
            continue
        residual = np.maximum(p - q, 0.0)
        return accepted, residual / residual.sum()
    return accepted, target_probs[len(draft_tokens)]
