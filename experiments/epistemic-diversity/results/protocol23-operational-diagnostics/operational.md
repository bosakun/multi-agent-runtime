# Operational audit — not a C2/C3 performance comparison

Protocol: pilot-2.3; runs: 5; calls: 19; journals: 19.
Stop: `runtime/schema/transport/boundary failure; retain all attempted records`.

Usage is unknown for 1 call(s). Failed usage must not be replaced with zero.

| Call journal | Agent | Latency s | Generated tokens | Limit | Headroom | Error |
|---|---|---:|---:|---:|---:|---|
| call-journal/0001_3c984a7e37f649039285f9caf73d260b_worker_0.json | worker_0 | 55.51 | 654 | 2048 | 1394 | unknown |
| call-journal/0002_3c984a7e37f649039285f9caf73d260b_worker_1.json | worker_1 | 53.69 | 642 | 2048 | 1406 | unknown |
| call-journal/0003_3c984a7e37f649039285f9caf73d260b_worker_2.json | worker_2 | 83.85 | 774 | 2048 | 1274 | unknown |
| call-journal/0004_3c984a7e37f649039285f9caf73d260b_synthesizer.json | synthesizer | 87.43 | 630 | 2048 | 1418 | unknown |
| call-journal/0005_1252c8300fbe433988b56515964140de_worker_0.json | worker_0 | 89.20 | 673 | 2048 | 1375 | unknown |
| call-journal/0006_1252c8300fbe433988b56515964140de_worker_1.json | worker_1 | 89.93 | 721 | 2048 | 1327 | unknown |
| call-journal/0007_1252c8300fbe433988b56515964140de_worker_2.json | worker_2 | 75.64 | 605 | 2048 | 1443 | unknown |
| call-journal/0008_1252c8300fbe433988b56515964140de_synthesizer.json | synthesizer | 278.00 | 2033 | 2048 | 15 | unknown |
| call-journal/0009_e60bba92b3024c7bb4cc5ed9d49758c6_worker_0.json | worker_0 | 144.69 | 1038 | 2048 | 1010 | unknown |
| call-journal/0010_e60bba92b3024c7bb4cc5ed9d49758c6_worker_1.json | worker_1 | 176.42 | 1269 | 2048 | 779 | unknown |
| call-journal/0011_e60bba92b3024c7bb4cc5ed9d49758c6_worker_2.json | worker_2 | 187.35 | 1290 | 2048 | 758 | unknown |
| call-journal/0012_e60bba92b3024c7bb4cc5ed9d49758c6_synthesizer.json | synthesizer | 196.60 | 1159 | 2048 | 889 | unknown |
| call-journal/0013_59971e54891b41ab9e71b95cc593635f_worker_0.json | worker_0 | 137.85 | 958 | 2048 | 1090 | unknown |
| call-journal/0014_59971e54891b41ab9e71b95cc593635f_worker_1.json | worker_1 | 166.04 | 1183 | 2048 | 865 | unknown |
| call-journal/0015_59971e54891b41ab9e71b95cc593635f_worker_2.json | worker_2 | 161.95 | 889 | 2048 | 1159 | unknown |
| call-journal/0016_59971e54891b41ab9e71b95cc593635f_synthesizer.json | synthesizer | 524.37 | 1334 | 2048 | 714 | unknown |
| call-journal/0017_e14b05fe11754953a75d6010dc002060_worker_0.json | worker_0 | 431.34 | unknown | 2048 | unknown | RuntimeFault |
| call-journal/0018_e14b05fe11754953a75d6010dc002060_worker_1.json | worker_1 | 273.41 | 2025 | 2048 | 23 | unknown |
| call-journal/0019_e14b05fe11754953a75d6010dc002060_worker_2.json | worker_2 | 158.52 | 1130 | 2048 | 918 | unknown |

No answer quality, gold data, model text or hidden reasoning is included.
