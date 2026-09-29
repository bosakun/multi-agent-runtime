# HotpotQA Windows本実験・最小復旧の完了報告

2026-09-29。ユーザーが選択したHotpotQA distractor devの30問×C0〜C4、
単一反復・150ケースの実行、公式集計、完了監査を完了した。
7405問の公式dev全体を完了したという意味ではない。

## 実行と保全

Protocol 3.0の18正常ケースと、途中停止したProtocol 3.1の71正常ケースを再利用した。
失敗C1内の正常worker_1/worker_2も出力・artifact・message・AgentRunを改変せず再利用し、
新規worker_0とsynthesizerの2生成、未着手60ケースの204生成を実行した。
新規campaignは61ケース・206予約で正常終了（14:02:40 UTC / 23:02:40 JST）。

| 項目 | 確認値 |
|---|---:|
| 完了したQA/条件セル | 150（30問×5条件、重複なし） |
| 正常native生成 | 510 |
| 予約台帳合計 | 511＝54＋251＋206 |
| 保存した元の送信前失敗予約 | 1 |
| 新規生成 | 206（上限206、追加retry/resumeなし） |
| 再利用した正常ケース / 個別worker | 89 / 2 |
| 新規canonical journal / native observation | 208 / 208（再利用コピー2件を含む） |
| 新規append-only journal snapshot | 824 |
| アクセス監査違反 | 0 |
| 既存ファイルの変更・削除 | 0 / 0（1729ファイル照合） |

元のPermissionError、partialレコード、ゼロ評価、予算消費は原campaignに残した。
失敗予約を払い戻していない。新規campaignとsource freezeでのみ復旧した。
保存修正は新規package `hotpot_recovery/` にあり、journal/progressを追記専用、
terminal結果とcanonical journalとnative observationをexclusive single-writeにした。
既存のfrozen package、データ、freeze、台帳、結果は変更していない。
元のエラーは送信直前のjournal保存/replace異常と判断するが、具体的なlock所有者や
Windows共有違反のOS subcodeは記録がなく確定していない。

## 公式スコア（0〜1）

全30問は累積探索的な集計。6問のPilotが事前に実施済みなので、推論はfresh24だけに限定した。

| 条件 | アクセスと役割 | 全30 Answer F1 | 全30 Support F1 | 全30 Joint F1 | fresh24 Answer F1 |
|---|---|---:|---:|---:|---:|
| C0 | 単一neutral・全文 | 0.718 | 0.680 | 0.505 | 0.674 |
| C1 | 3 neutral・全文＋合成 | 0.734 | 0.790 | 0.611 | 0.695 |
| C2 | 3 diverse roles・全文＋合成 | 0.758 | 0.805 | 0.634 | 0.724 |
| C3 | 3 neutral・文書分割＋合成 | 0.599 | 0.593 | 0.380 | 0.567 |
| C4 | C2の役割・C3の分割＋合成 | 0.565 | 0.560 | 0.374 | 0.567 |

事前指定の主比較P1（fresh24のC3−C2 Answer F1）は−0.15643。
条件付きbootstrap CI95は[−0.29848, −0.03985]、seed付きsign-flip p=0.03010。
この選択標本ではC3優位を示さず、C2の方が高かった。24問のうち非ゼロの差は6問、
すべてC3側が低く、残る18問は同点だった。副比較P2〜P5はHolm補正後いずれもp>0.05。
記述的interaction (C4−C3)−(C2−C1)は−0.02984で、追加有意性検定にはしていない。

元の失敗C1はF1=0、復旧後はF1=1であり、fresh24のC1平均を1/24だけ上げた。
元のpartialレコードを解析に明示し、復旧を隠していない。主比較C3−C2はこのC1復旧に影響されない。

「ローカルモデルが課題を全く解けず、差が出ない」という床効果だけでは説明できない。
例えば全30問のC2はAnswer EM 14/30、Answer F1 0.758である。
C3のworker段階gold-support引用recallは0.847だが、final支持証拠recallは0.592だった。
情報圧縮・合成時の証拠保持は次の検討候補だが、これは記述統計に基づく仮説であり、
意味内容の独立人手検証や因果証明ではない。C2−C3は役割とアクセスの両方が異なる。

## Windowsで確認できた事実

[Windowsガイド](../../../docs/windows-nvidia-ollama.md)を参照し、host-onlyガイド自体の
停止境界と、後から明示承認された研究計画3.0/3.1/最小復旧3.2を区別した。
CodexのChatGPT認証は変更していない。`OPENAI_API_KEY=ollama`をCodex認証に設定せず、
native `/api/chat` を使用した。環境変更は実行用child shell内だけである。

- branch `research/epistemic-diversity`、HEAD `95441daee16dc51821b07cd67bc28773f7185664`。
  tracked/cached diffは空、既存未追跡ファイルは保持。stage/commit/pushなし。
- Windows 10.0.26200、PowerShell 5.1.26100.9549、Python 3.12.11・UTF-8 mode、
  uv 0.11.23、Git 2.51.2.windows.1の利用を確認。
- RTX 4070 SUPER、driver 591.86、VRAM 12282MiB。
- Ollama 0.34.4、Qwen3:14b Q4_K_M、digest
  `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`。
- 実生成中の`/api/ps`＋CLIで100% GPU配置、ロードcontext8192、
  size=size_vram=10321636883bytesを記録。これはcompute使用率とは別の値。
- `nvidia-smi`監視中の一観測ではGPU使用率97%、VRAM11529MiB、68℃、186.26W。
  これは継続平均やハードウェアbenchmarkではない。
- think=false、temperature0、input/output上限4096、concurrency1を維持。
  510件のnative応答はdone=true・finish_reason=stop・thinking_chars=0。
- Windows回帰テスト215合格・2skip、失敗/エラー0、324.12秒。
  skipはPostgreSQL URLと非配布implementation-local baseline。live API E2Eは除外。
  復旧/完了監査の個別テスト11合格、型検査6 source files合格、Ruff合格。
- Mockは実prefixを再利用した運用検証で、追加206回はMock。性能測定と混同していない。

## 完了の証拠と成果物

- [独立完了監査](../../../reports/hotpot-recovery-completion-final-audit.json)：
  150セル、510正常生成、511予約、3 runtime DBの連続event、再利用元の同一性、
  同じpublic選択と原文/gold、公式scorer・10予測export・推論の再計算、
  CSV/レビュー/6図、元の失敗保持、1729ファイル保存に合格。
- [保存監査](../../../reports/hotpot-recovery-preservation-after.json)。
- [WindowsテストXML](../../../reports/hotpot-recovery-windows-tests.xml)。
- [実生成中GPU配置](../../../reports/windows-host/inspect-20260929T134618Z-cf65b0e0a68344fabb1edb98cea43097.json)。
- [公式集計](../runs/hotpotqa-protocol32-qwen3-14b-windows/analysis/analysis.json)、
  [短い集計表](../runs/hotpotqa-protocol32-qwen3-14b-windows/analysis/summary.md)。
- [ケースCSV](../runs/hotpotqa-protocol32-qwen3-14b-windows/analysis/descriptive/cases.csv)、
  [保存出力レビュー](../runs/hotpotqa-protocol32-qwen3-14b-windows/analysis/descriptive/saved-output-review.md)。
  6 SVGは同directory、Answer F1/Support F1/input tokens/call latency/citation overlap/access audit。
  実測C2/C3 EM不一致3件は`discordant-C2-C3.json`。
- [復旧事前計画](protocol-3.2-hotpotqa-recovery.md)、新規freeze
  `freezes/hotpotqa-dev-distractor-protocol-3.2.json`、binding署名
  `a97ad811afde38a8221fb069536f5a9f42387e0033ca930e7ea9a0d3ee7a1c75`。

## 確認できていないこと・解釈の限界

インストール済みCUDA runtimeはunknown/nullで、driver-supported CUDA欄から推定しない。
Ollama processの環境値をAPIから確認できるとは主張しない。
取得不能だったCMU原配布とmirrorのbyte同一性は未確認で、pinned mirrorのchecksum/provenanceを使う。
長さ制限付きdev30問・単一モデル・temperature0単一反復であり、全benchmark/leaderboard、
他モデル、確率的頑健性、汚染なし、認知的独立性を示さない。
質問間のentity依存でiid bootstrap解釈が弱まる可能性がある。
引用の一致は意味内容の正しさを保証せず、分割条件の低引用overlapは機械的なアクセス制約でも生じる。
総入力/computeは条件間で同一ではない。未知の価格はnull、call latencyはend-to-endではない。
出力レビューは自動生成で、独立人手検証は未実施。

次に人間が行う作業は、保存出力と不一致3件のレビュー、および必要ならより大きな
公的ベンチマーク標本の新規事前計画を決めること。既存campaignは再実行しない。
追加モデル生成、別モデル、追加反復、commit/pushは実施していない。
