"""Buggy variants the tests must catch."""


def _train(text, num_merges, tie="first", direction="ltr", min_count=2, encode=True):
    ids = list(text.encode("utf-8")) if encode else [ord(c) for c in text]
    merges = []
    for i in range(num_merges):
        counts = {}
        for pair in zip(ids, ids[1:]):
            counts[pair] = counts.get(pair, 0) + 1
        if not counts:
            break
        top = max(counts.values())
        best = max(counts, key=counts.get) if tie == "first" else min(p for p, c in counts.items() if c == top)
        if counts[best] < min_count:
            break
        seq = ids if direction == "ltr" else ids[::-1]
        key = best if direction == "ltr" else best[::-1]
        out, j = [], 0
        while j < len(seq):
            if j < len(seq) - 1 and (seq[j], seq[j + 1]) == key:
                out.append(256 + i)
                j += 2
            else:
                out.append(seq[j])
                j += 1
        ids = out if direction == "ltr" else out[::-1]
        merges.append(best)
    return merges


def ties_smallest_pair(text, num_merges):
    return _train(text, num_merges, tie="min")


def merges_right_to_left(text, num_merges):
    return _train(text, num_merges, direction="rtl")


def never_stops_early(text, num_merges):
    return _train(text, num_merges, min_count=1)


def unicode_code_points(text, num_merges):
    return _train(text, num_merges, encode=False)
