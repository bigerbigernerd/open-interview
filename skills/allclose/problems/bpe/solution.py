def bpe_train(text, num_merges):
    ids = list(text.encode("utf-8"))
    merges = []
    for i in range(num_merges):
        counts = {}
        for pair in zip(ids, ids[1:]):  # insertion order = first occurrence
            counts[pair] = counts.get(pair, 0) + 1
        if not counts:
            break
        best = max(counts, key=counts.get)  # ties -> earliest
        if counts[best] < 2:
            break
        new, out, j = 256 + i, [], 0
        while j < len(ids):
            if j < len(ids) - 1 and (ids[j], ids[j + 1]) == best:
                out.append(new)
                j += 2
            else:
                out.append(ids[j])
                j += 1
        ids = out
        merges.append(best)
    return merges
