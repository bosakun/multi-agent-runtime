# Windows Codexへの記事執筆引き継ぎ

## 目的と位置づけ

前編は`docs/articles/multi-agent-runtime-development-ja.md`。
2026年9月30日時点、基準commit
`95441daee16dc51821b07cd67bc28773f7185664`の記録に基づく。
Runtime設計、研究基盤、Mac / OllamaでのPilot停止までを扱う。
Windows実機上の速度、GPU利用率、native test結果は記載していない。

後編は、Windows側で実際に確認した事実を基に別記事として作成する。
本引き継ぎは記事作成の依頼であり、新しい実験・Protocol変更・real generation・pushの実行承認ではない。

## Windows側のCodexへ渡せるプロンプト

```text
このRepositoryの開発記事の後編を作成してください。

まず以下を読み、前編と整合する形にしてください。
- docs/articles/multi-agent-runtime-development-ja.md
- docs/articles/windows-continuation-notes.md
- docs/windows-nvidia-ollama.md
- docs/windows-compatibility-audit.md
- experiments/epistemic-diversity/STATUS.md
- experiments/epistemic-diversity/docs/qwen3-14b-protocol24-operational-failure.md

前編は情報境界中心のRuntime設計、Role DiversityとEpistemic Diversityの
比較設計、Mac上のProtocol 2.1〜2.4のoperational failureを扱っています。
Windows側で行った作業・検証の記録を確認し、その先を記事にしてください。

今回は記事の作成です。新しいreal model call、実験、Protocol変更を
記事用のデータ集めとして勝手に行わないでください。
実行済みのログや既存のhardware reportから確認できる事実だけを使い、
不足するデータは未確認と記載してください。

記事では次を区別してください。
1. Host platformの変更と研究Conditionの変更
2. Mock検証とWindows native検証
3. GPU residencyと実際の推論速度
4. Operational completionとtask performance
5. Engineering diagnosticと正式な研究Pilot

Windowsの実機構成、Ollama / driver / model digest、GPU offload、
PowerShell、UTF-8 / LF、file locking、SQLiteの検証について、
実際の記録がある範囲で説明してください。
問題があれば、観測・仮説・対応・確認済み結果を分けて書いてください。

前編の実モデルPilotは未完走です。GPU変更だけでEvidence IDの問題まで
解決したと推測しないでください。後続の結果があれば独立したProtocol /
campaignとして扱い、歴史的な失敗を成功へ書き換えないでください。

新規Markdownをdocs/articles/に作成してください。
既存研究資産、benchmark、gold、prompts、configs、freeze、campaignは変更禁止です。
既存ユーザーファイルを保持し、commit / pushは別途依頼がない限り行わないでください。
```

## 前編との接続点

- 出発点は「同じモデル、同じ情報に異なる役名をつけるだけでよいのか」。
- 人間の会議は比喩。private evidenceの分離は、信条・人格・事前学習知識の分離ではない。
- C2 / C3の優劣は未確定。Benchmark 2.0.0は30 tasks / 10 families。
- 正式Pilotの計画は六task、二条件、一repetition、12 runs / 48 calls。
- 2.1は1 run / 3 callsのtimeout。2.2は4 runs / 16 callsのtimeout。
- 2.3は5 runs / 19 callsのlength termination。
- 軽量synthetic diagnosticの成功では失敗を再現できなかった。
- exact failed inputの診断では2048でfinal contentなし、4096で2430 generated tokensを使いSchema-valid出力。
- 2.4は4 runs / 15 Pilot callsで`unknown_evidence_reference`。診断3 callsを含む共有budget消費は18。
- invalid IDは`none`。fail-closedは正常。repair、retry、dynamic enumは実装したことにしない。
- Windows support追加時の検証はmacOS上。318 passed / 3 skippedにWindows向けMock 66件が含まれる。
- 3,084既存ファイルのSHA256一致はその追加作業の記録。新しいWindows checkoutで実測した値とは区別する。

## 後編に欲しい、実測に基づく項目

- 実機OS / CPU / RAM / GPU / VRAM / driverと取得不能な項目。
- Ollama version、endpoint、model identity / digest / quantization。
- server processへconcurrency環境変数が渡ったことを何で確認したか。
- 起動済みserver検出と、無断killを避けた運用。
- モデルがresidentでない場合とpartial / full offloadの実測値。
- native tests、non-research smokeの実行日時・コマンド・結果。
- file locking、研究budget DBのhandle lifecycleなど残る制約。
- 実際に後続研究の承認と実行があった場合のみ、新Protocolと結果の独立した説明。

速度比較には同一入力、生成量、設定、温度・負荷などの条件確認が必要。
単発latencyやGPU搭載の事実だけで、Macより何倍速いと書かない。
研究性能の結論は、operational gateを満たしたcohortと十分な比較記録がある場合だけ検討する。

## 編集上の注意

前編はZenn向けfront matter付きの未公開原稿。`published: false`。
本人の一人称による著者草稿だが、未記録の感情・会話・体験を創作しない。
公開前に著者が言い回しと公開範囲を確認する。
Repositoryのtrace類にはGit管理外のものがあるため、読者がGitHubから
全実行データを取得できるとは書かない。引用は公開summaryと実データを区別する。
