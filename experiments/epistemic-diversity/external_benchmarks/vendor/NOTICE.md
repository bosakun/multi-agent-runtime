# Pinned official HotpotQA evaluator

Upstream: https://github.com/hotpotqa/hotpot
Commit: `3635853403a8735609ee997664e1528f4480762a`
Source: `hotpot_evaluate_v1.py`, unchanged bytes.
SHA256: `d35fc91a6db21d791dbdda11daf3856e9359f5701d54e3eefba20d88fecc02c0`

Copyright 2018 Zhilin Yang, Peng Qi, Saizheng Zhang. Apache-2.0; see LICENSE.txt.
The wrapper removes only `import ujson as json` from the in-memory AST and
supplies Python stdlib json. The original vendor file and all scoring logic
remain unchanged. No training dependencies, ujson install, or lockfile edits.

The separately downloaded HotpotQA dataset is CC BY-SA 4.0, not Apache-2.0.
Source sentence text/order and reference answers/supporting facts are preserved.
Public/gold separation and access partitioning are our research adaptation,
not a new official dataset or leaderboard result. Dataset attribution:
Yang, Qi, Zhang, Bengio, Cohen, Salakhutdinov, Manning (EMNLP 2018),
https://aclanthology.org/D18-1259/ and https://hotpotqa.github.io/.
