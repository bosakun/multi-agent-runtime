# Protocol 3.2 — HotpotQA最小運用復旧

ユーザーは「最小復旧を承認します」と明示した。30問×C0〜C4・150ケースの
元の研究範囲は変更しない。Protocol 3.0/3.1のfreeze、campaign、予約台帳、
正常出力と失敗履歴は不変。旧campaignをresumeしない。

旧台帳は54+251=305予約、native応答は304。正常89ケースを再利用する。
途中停止C1（5adc0c2b55429947ff1738db）のworker_1/worker_2の正常出力・
artifact・message・AgentRunをそのまま新規runへ取り込み、worker_0とsynthesizer
だけを新規生成する（2回）。未着手60ケースを元と同じ順序・設定で生成する（204回）。
新規台帳のhard ceilingは206、累積予約上限は511、正常native応答予定は510。
元の送信前PermissionError予約を払い戻さず、失敗した原レコードも残す。
復旧による追加のretry、repair、resumeは許可しない。異常時は再びfail-stop。

HotpotQA distractor devの同じ公的長さ選択30問、同じ原文、ゴールド分離、
役割、全文/文書分割アクセス、公式scorer、seedを使う。モデルdigest・Ollama version・
temperature0・think=false・context8192・output4096・input4096・concurrency1を維持。
取り込むartifactのpayloadとメタデータは不変。synthesizerへのartifact/message順は
元のworker_0,worker_1,worker_2順を維持し、新しいrun IDと新規workerのメタデータだけが
必然的に異なる。正常worker2件を再生成しない。source DBはread-onlyで読む。

Windows保存修正は別packageに実装する。各journal checkpointと各progress checkpointは
独立した新規ファイルにexclusive writeし、既存targetへのreplaceを行わない。
canonical journal、native observation、terminal resultsはそれぞれ一度だけexclusive write。
旧journal/observationの再利用コピーも原ファイルSHAで照合する。新規runtime DBは
SQLiteのtransaction/optimistic concurrencyをそのまま利用する。

Mockは実prefixと2件の保存出力を再利用し、新規206呼び出しのみMockで処理する
運用検証であり、モデル性能の測定ではない。Mock結果はこの用途を明記する。
単体テスト、206回Mock、累積150ケース集計・監査の合格後に新規source freezeと
campaignをbindし、host preflight合格後に実生成を開始する。

解析は元Protocol 3.1のP1=C3-C2 answer F1をfresh24だけで評価する。
P2〜P5のsecondary Holm family4、seed20260928、5000 bootstrap/20000 sign flipsを
維持する。全30問は累積探索的。復旧ケースを新しい統計的反復に数えない。
運用障害のある元C1をゼロとした感度比較も記述的に別記し、復旧結果への置換を隠さない。
最終成果物は150ケース、510正常生成、511予約/1送信前失敗の照合、公式10予測export、
fresh24推論、CSV/保存出力レビュー/6図、3 runtime DB/連続event監査、原1729ファイル
保存監査、GPU実機観測。長さ選択dev小標本・単一モデル・単一反復の限界を明記する。
