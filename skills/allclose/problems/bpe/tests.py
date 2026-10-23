def cases():
    para = ("the quick brown fox jumps over the lazy dog. " * 3 + "大模型的分词器先把文本变成字节，再反复合并最常见的相邻对。" * 4
            + "tokenization is the first step of every language model; tokens are not words. ") * 12
    return [
        dict(name="aaabdaaabac, 3 merges", kwargs=dict(text="aaabdaaabac", num_merges=3), sample=True),
        dict(name="hello hello world", kwargs=dict(text="hello hello hello world", num_merges=6), sample=True),
        dict(name="runs: aaaaaaa (overlaps, left to right)", kwargs=dict(text="aaaaaaab aaab", num_merges=4)),
        dict(name="Chinese (UTF-8 bytes)", kwargs=dict(text="大模型大模型训练训练大模型", num_merges=5)),
        dict(name="stops when nothing repeats", kwargs=dict(text="abcdefg abc", num_merges=10)),
        dict(name="ties broken by first occurrence", kwargs=dict(text="xyab xyab abxy", num_merges=5)),
        dict(name="1-char text", kwargs=dict(text="a", num_merges=3)),
        dict(name="long mixed text, 40 merges", kwargs=dict(text=para, num_merges=40)),
    ]
