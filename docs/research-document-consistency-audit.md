# 研究文書の整合性監査

監査日：2026-09-30。当時のaudited base snapshotはGitHub main `130ff0c54ddd77129bd9645d56ca33de505481ec`（PR #7 merge）、研究branch snapshotは`6d27edc4535f22d195b229da7010f982563eaf80`でした。当時のtree差分は空で内容が一致し、ローカル`main`参照`5078c65`とは区別しました。以下は当時の文書監査記録であり、永続的な最新HEAD表記ではありません。mainのcheckoutや既存未追跡資料の移動はしていません。

2026-10-02追記：現行framing・Related Work・Human Review設計の改訂とsnapshot表記の監査は[Deep Research統合監査](deep-research-integration-audit.md)に記録します。以下の歴史的stale項目・当時の監査結果は削除しません。

## 範囲と判断方針

調査開始時のGit管理Markdown 98件を対象に、`pending`、`No real-model`、`current/latest`、`未実施/未実行`等を横断検索しました。root README、Runtimeのarchitecture/information-flow/security/ADR、研究案内、Protocol 3.0/3.1/3.2、Windows完了報告、paper、Study 2の計画・結果・レビューを重点確認しました。リポジトリのコード・tests・script・freezeの配置、ContextBuilder/router/隔離テスト、保存済み両研究の集計・完了監査・レビュー準備監査も読み取り確認しました。全コードの新たな安全性監査や全ログの再解析ではありません。新しい生成・採点・統計計算・人手判定は行っていません。

以下の`E/`は`experiments/epistemic-diversity/`、`S/`は`experiments/synthesis-evidence-preservation/`です。引用や節名は探索時の手掛かりで、ファイル全文の文脈を優先します。

- 現在地の入口は[research-status-ja.md](research-status-ja.md)とし、旧案内を実行承認と扱いません。
- 事前計画、freezeに含まれる資料、当時の結果・失敗・検証記録は保持します。後の成功で古い失敗を消しません。
- 歴史的abstract/outlineは上書きせず、新しい`paper/current-*`で分離します。
- 「現在の案内として更新が必要」と「元ファイル本文を変更すべき」は別です。保全対象は、本監査と現在地文書による外側の注記・誘導で扱います。

## 現在の案内としてstaleな項目

| file | stale statement | historical recordとして残すべきか | 更新すべきか | 推奨対応／今回の対応 |
| --- | --- | --- | --- | --- |
| `E/README.md` | `Benchmark 2.0.0 / protocol 2.3`、`Current operational status`、`No protocol-2.3 real run has been executed`、`still-pending empirical research` | はい。自作benchmarkと停止履歴の案内。内部にも実行済み19 callsと未実行が混在 | 現在案内としては必要。本文の一律置換は不可 | 旧READMEはそのまま保持。現在地・HotpotQA完了報告を入口にし、旧synthetic cohortへ限定して読む |
| `E/STATUS.md` | `Latest: Protocol 2.4 ... stopped`、`Current ... Pilot remains stopped`、`No real-model results exist at this stage` | はい。時系列の当時状態 | 最新状態への誘導が必要 | 後のWindows/HotpotQA/Study 2を本監査で追補。元節の「Latest」は当時の見出しと解釈し、本文を成功に改変しない |
| `E/READY_FOR_REAL_PILOT.md` | `Comparative real-model results pending`、`Current seal ... protocol-2.3`、launch approval pending | はい。旧synthetic Pilot手順 | 現行手順としての利用停止が必要 | 旧binding/campaignを実行・再開しない。現在地文書を優先し、旧文書のコマンドは履歴として保持 |
| `E/ACTIVE_BENCHMARK.md` | `Protocol 3.0 ... current plan`、6問・C0/C2/C3のPilot-only案内 | はい。3.0/3.1/3.2のfreezeに含まれる | 別の現在案内が必要。封印本文は変更しない | 3.0=Pilot、3.1=30問計画、3.2=復旧完了という時系列を新文書に明記 |
| `E/ACTIVE_EXPERIMENT.md` | `complete planned experiment`、`hotpot_full.py completes ... 456 calls` | はい。3.1/3.2のfreezeに含まれる | 完了・復旧への外側の誘導が必要 | 3.1計画時点の文書として保持。実績は150セル/510正常/511予約で、3.2復旧報告が最終状態 |
| `E/docs/research-plan.md` | `current protocol pilot-2.2 / benchmark 2.0.0` | はい。複数freezeの事前計画資料 | 現行計画を別文書で示す | 旧synthetic計画を保持。HotpotQA 3.1/3.2とStudy 2 PLANへのリンクを新現在地に置く |
| `E/docs/methodology.md` | `Current execution protocol is pilot-2.3`、`All current numerical files are mock validation only` | はい。複数freezeに含まれる | 現行Methodsは別に必要 | 設定・指標・oracle routingは旧syntheticに限定。新outlineにHotpotQA/固定WorkerのMethodsを作成 |
| `E/docs/experiment-freeze.md` | `current seal ... protocol-2.3` | はい。封印仕様の履歴 | 外側でどの研究のsealか区別する | 旧sealの参照・hashは維持。Study 1の3.0/3.1/3.2とStudy 2 v1を現在地で示す |
| `E/docs/findings.md` | `No real-model results exist`、`LLM comparison pending` | はい。明示的なoffline v1 findings | 現行findingsと混同しない誘導が必要 | Mock測定は変更せず、実測結果は両Windows結果報告とcurrent abstractで記す |
| `E/docs/summary_ja.md` | `現在は ... protocol 2.1`、`実モデルは未実行`、`最新の手順は実行準備` | はい。2026-09-28の旧要約 | 現在要約を別に作る | 本文保持、今回のresearch-status-jaを現行要約とする |
| `E/docs/limitations.md` | `Current v2 scope`、古いtimeout・benchmark・未検証範囲 | はい。freeze内の旧制約 | 現在の制約を別途追加する | 古い設定を修正せず、新現在地・brief・outlineにHotpotQA/Study 2の制約を記す |
| `E/docs/validation.md` | `Current: protocol 2.2`と`Current: protocol 2.1` | はい。各検証の当時状態 | 最新検証との混同防止が必要 | 旧件数を増やさず、Study 1 Windows検証とStudy 2のarchival除外を新文書で区別 |
| `E/paper/abstract.md` | `Real-model experiments remain pending because credentials were unavailable`、24 synthetic tasks・250 mocks | はい。歴史的protocol abstract | 新要旨が必要。上書き禁止 | `current-abstract-ja.md`と`current-abstract-en.md`を新規作成 |
| `E/paper/outline.md` | `Current Methods ... protocol 2.1`、`Real-model results pending`、全real cells未充填 | はい。旧執筆scaffold | 新構成が必要。上書き禁止 | 一論文化の方針未確定として`current-outline.md`を新規作成 |
| `E/docs/related-work.md` | publishable contribution unknown `until real runs and stronger benchmark validation exist` | はい。2026-09-28のfocused survey | 現在の新規性・投稿判断を別に扱う | 実行は済んだがpublishabilityは未確定。旧調査を網羅的最新版に見せず、教員への相談事項にする |
| `docs/articles/multi-agent-runtime-hotpotqa-windows-ja.md` | 固定Worker介入は「提案であり、まだ実行していません」 | はい。冒頭で2026-09-29までの未公開草稿と明記 | 現在読む際に日付境界の注記が必要 | 記事本文はそのまま。翌日のStudy 2が提案を実装・実行済みで、結果は非支持だったことを新現在地で接続 |
| `S/docs/offline-validation.md` | `source freeze・backend binding・実生成 ... 未完了` | はい。実生成0の準備段階・Mock失敗記録 | 現在の状態は別文書で示す | 記録を保持し、Study 2結果報告へ誘導。独立人手レビュー未完了だけは今も正しい |
| `S/REVIEW-HANDOFF.md` | 手順5「新比較の実生成が終了したら」 | はい。生成後資料も同書に既に掲載 | 必須ではないが手順の時点を説明する | 実生成・資料準備済み、これから行うのは独立判定と処理。票を埋めたり担当者を仮定しない |
| `S/study.json` | `status: planned_not_implemented` | はい。v1 freezeに含まれる計画snapshot | status fieldを変更せず実績を分ける | README/結果/監査の実績を使う。同snapshotのstatusを研究現在地として解釈しない |
| root `README.md` | 研究紹介の出発点が30 synthetic tasksで、詳細リンク先旧READMEはstale | はい。旧研究の存在は正しい | 最小限の入口追加で十分 | 両研究の完了・人手pendingは既に正しい。research-status-jaへのリンクだけを追加 |

## 歴史的記録として維持する項目・現在も正しいpending

| file | stale statementまたは誤読し得る記述 | historical recordとして残すべきか | 更新すべきか | 推奨対応 |
| --- | --- | --- | --- | --- |
| `E/docs/archive/README-v1.md` | real-model pending、24 authored tasks | はい。archiveで明示 | 不要 | 過去のMock検証として保持、現行結果とpoolしない |
| `E/docs/experiment-log.md` | 各時点の`results pending`、`current freeze` | はい。時系列実施記録 | 過去entryの更新不要 | 新現在地を別文書に置き、過去entryの当時状態を維持 |
| `E/docs/protocol-2.1-amendment.md`、`v2-design-amendment.md` | `No real result has been observed`、credentialsなし | はい。事前条件 | 不要 | 当時の計画として保持。現在のモデル結果なしという意味にはしない |
| `E/docs/protocol-2.2-amendment.md`〜`protocol-2.7-amendment.md` | 各版のcurrent source/設定/承認境界 | はい。封印された改訂履歴 | 不要 | プロトコル別に読む。後の条件を遡及適用しない |
| `E/docs/protocol-3.0-hotpotqa.md` | Main/C1/C4はnot launched | はい。6問Pilotの事前範囲 | 不要 | その後の3.1・3.2を別段階として説明 |
| `E/docs/protocol-3.1-hotpotqa-main.md`、`protocol-3.2-hotpotqa-recovery.md` | 456 planned calls、206新規の予定・gate | はい。freeze済み事前仕様 | 不要 | 実績は結果報告に置く。条件・予算を後付けで変更しない |
| `E/docs/hotpotqa-migration-windows.md` | 「この移行では」実生成・binding・Pilot未開始 | はい。移行時点と範囲を明記 | 不要 | 後の実行成功と区別、当時の未実行を消さない |
| `E/docs/hotpotqa-main-validation.md` | 開始gate、追加132ケース終了まで未完了 | はい。開始時点の記録 | 不要 | 最終状態は3.2結果報告から読む |
| `E/docs/qwen3-14b-hotpotqa-protocol31-operational-failure.md` | 全実験未完了・60未着手・復旧は提案 | はい。実際の停止と元失敗 | 不要 | 原失敗を保持し、3.2の実施と並べて提示 |
| `E/docs/qwen3-14b-*operational-failure.md`各版、診断plan/results/launch、`operational-recovery.md`、`recovery-v2-*` | 停止・未実行の後続・限定診断成功 | はい。各運用事象・承認境界 | 不要 | 古い失敗を成功に変更しない。診断成功を研究成績にpoolしない |
| `E/docs/qwen3-14b-protocol27-windows-outcome.md` | 後続一般化・意味的検証は未実施 | はい。旧synthetic6課題の結果 | 不要 | HotpotQAに読み替えず、別cohortで保持 |
| `E/docs/next-research-plan.md` | 草稿時点の未実施・計画 | はい。supersededと81比較完了の注記あり | 不要 | 後継PLANと結果を優先。fresh24呼称をStudy 2の未観測標本に使わない |
| `S/PLAN.md`、`S/OPERATIONS.md` | 実装・freeze完了を意味しない、今後の実装順序 | はい。v1 freezeに含まれる | 不要 | 仕様と実施状況を分ける。人手完了条件は今も有効 |
| `S/REVIEW.md` | 担当者未確保時pending、独立2名を要する | はい。freeze済み判定計画 | 不要 | 2名の実判定と不一致処理は未実施。空フォームをAIで埋めない |
| `S/README.md`、`S/docs/qwen3-14b-windows-outcome.md` | 81件完了・人手0/2・full research未完了 | はい。現行結果と整合 | 不要 | 現在の根拠として使用。平均差0を同等性に言い換えない |
| `S/docs/regression-scope.md` | 最初のsuite未合格、旧path/CRLF/journal制約、archival除外 | はい。不利な検証結果も必要 | 不要 | 398 passed / 4 skipped / 25 deselectedを無条件全greenとしない |
| `E/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md`、`S/docs/qwen3-14b-windows-outcome.md` | 「commit/pushしていない」等 | はい。各実行報告作成時の作業範囲 | 不要 | 後の6d27edc公開とは別の事実。全文を現在時制で読まない |
| `docs/articles/multi-agent-runtime-development-ja.md`、`windows-continuation-notes.md` | Mac Pilot未完走、比較未確定、後編作成予定 | はい。前編・執筆引き継ぎ | 不要 | 後編とStudy 2への接続を新現在地で補足、Mac失敗を成功に変えない |
| `docs/windows-compatibility-audit.md` | Native Windows/RTX検証pending | はい。host support追加時のMac検証 | 不要 | その作業時点では正しい。後のWindows結果報告と区別 |
| `docs/windows-nvidia-ollama.md` | host-onlyの停止境界・warmup「今回未実行」 | はい。host準備の限定範囲 | 不要 | 後の研究承認を遡及してガイドへ混ぜない。今回はガイドの生成手順も実行しない |
| `docs/validation.md`、`docs/evaluation-results.md`、旧Mock summary・human-review出力 | v1/offline検証、paid API未実行、Mock数値 | はい。範囲・日付・Mockを明示 | 不要 | Runtime検証と研究性能を分ける。「human-review」ファイル生成は独立人手レビュー完了ではない |
| root `README.md`のHTTP adapter offline契約検証・paid-model制約 | `Live paid-model ... require separate experiments` | はい。汎用adapter/有料APIの検証範囲 | 不要 | native Ollama研究と同じprovider契約とは扱わない。研究成果への入口のみ追加 |
| `docs/architecture.md`、`information-flow.md`、`security.md`、`docs/adr/` | 情報隔離・typed publication・trusted host限界 | はい。研究結果のpendingとは別 | 不要 | 実装コードとも整合。引用scopeを真実性保証に拡張しない |
| `E/docs/benchmark-taxonomy.md`、`benchmark-audit.md`、`metric-audit.md`、`qualitative-analysis-template.md` | synthetic仕様・監査・判定テンプレート | はい。旧benchmarkの資料 | 不要 | HotpotQAの指標や実人手判定として流用しない |

## 今回の変更と残る整備

新規作成は、研究現在地、本文書、教員向けbrief、主張対応表、日英current abstract、一論文化のcurrent outlineの7ファイルです。root READMEは現在地への入口だけを追加しました。上表の旧資料の本文・freeze・過去campaignは変更していません。歴史的本文に残る`current/latest/pending`は意図的に保全したもので、本監査の対応表と現在地文書を通して読む必要があります。

将来、旧README/STATUSにも直接注記を付ける場合は、当該ファイルが保存baselineやsealに含まれるか再確認し、保全対象を再封印・書換えしない方針を先に決めます。今回、旧abstractの「Replace」指示は実行せず、ユーザー指定どおり別ファイル化しました。

raw/local/privateの公開可否、資料ライセンス、完全な再解析パッケージ、独立人手レビュー、関連研究の追加調査は未完了です。ローカルJSONへリンクしていることと第三者がGitHubから取得できることは違います。研究相談・査読に必要な共有範囲は人間が判断します。

## 整理後の確認

- 新規7文書のローカルリンク75件は、このPC上で参照先の存在を確認しました。Git管理外のリンクが公開可能になったという意味ではありません。
- 調査開始時のGit管理581ファイルをSHA256で再照合し、変更はroot READMEだけでした。旧abstract/outline、Protocol、freeze、Runtime core等の既存管理ファイルは同一でした。
- Study 2 v1 freezeの`code_hashes`と`source_hashes`計526件を読み取り照合し、欠落・hash不一致は0でした。新しいseal作成や過去sealの更新はしていません。
- `git diff --check`と新文書の行末空白確認に問題はありません。既存未追跡Mockフォルダ3件は保持しました。
- 今回は文書整理のため、モデル生成・Ollama通信・新しい統計・test suiteの再実行・独立人手判定・stage/commit/pushを行っていません。remote main参照を取得するGit fetchのみ行いました。
