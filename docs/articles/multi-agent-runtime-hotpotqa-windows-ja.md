---
title: "情報を分けたら、答えは悪くなった――Windows実機で完走したMulti-Agent実験と、残った問い"
emoji: "🔎"
type: "tech"
topics: ["llm", "multiagent", "python", "ollama", "研究"]
published: false
---

> 本稿は[前編](https://github.com/bosakun/multi-agent-runtime/blob/582d82e2df69111a7f04b9cc4c5aaf3017c2d714/docs/articles/multi-agent-runtime-development-ja.md)の後編です。前編で未完走だったMac上のPilotを成功したことにはせず、その後にWindows / NVIDIA環境で行った検証と、別のHotpotQA実験を扱います。2026年9月29日までに保存された結果に基づく未公開草稿です。

## 前編で止まったのは、研究上の「負け」ではない

前編では、同じモデルに異なる役名を与えることと、エージェントが参照できる情報を実際に分けることを区別した。Runtimeには情報・Tool・公開Artifactの境界を作り、Role DiversityとEpistemic Diversityを比較する研究基盤も用意した。

しかしMac上の`qwen3:14b`による正式Pilotは完走しなかった。timeout、生成長の上限、存在しないEvidence IDの引用という、異なる運用上の失敗で停止した。最後の失敗ではRuntimeが未知のIDを拒否しており、安全境界としては期待どおりに働いた。一方、完走した比較結果はない。ここから「情報分離が有利／不利」とは言えなかった。

次の段階はWindows PCへの移行だった。ただし、Windowsは新しい研究条件ではない。GPUやOSの変更は実行環境の変更であり、C0〜C4という科学的な比較条件そのものとは分けて記録した。過去の失敗campaignも書き換えず、後続は別Protocolとcampaignにした。

## まず、モデルがどこで動いているかを確かめた

Windows実機はRTX 4070 SUPER（VRAM 12282 MiB）、driver 591.86。Ollama 0.34.4上の`qwen3:14b`はQ4_K_Mだった。実生成中にOllama APIとCLIでモデルの100% GPU配置を記録し、APIの`size`と`size_vram`はいずれも10,321,636,883 bytesだった。別の一時点の`nvidia-smi`観測ではGPU使用率97%、VRAM 11529 MiBだった。

ここで「100% GPU」はモデルの配置を表し、常時GPU計算使用率100%という意味ではない。一時点の使用率から平均速度やMacとの速度比も推定できない。driverが表示するCUDA対応値は、インストール済みCUDA runtimeのversionでもない。

PowerShell、Python、uv、Git、Ollamaの利用を確認し、Windows向けのpreflightと、研究ベンチマークを使わないMock smokeを通した。後続のWindows回帰テスト記録は215 passed / 2 skippedで、失敗・エラーは0。これはソフトウェアと実行環境の確認であって、モデルの正答性能の証拠ではない。実モデル実行時は`think=false`、temperature 0、concurrency 1を維持した。

## 自作問題から、HotpotQAへ移した

最初の自作ベンチマークは構造を制御しやすい反面、一般的なQAへの外挿に限界があった。そこで次の比較には、複数文書を横断して答える[HotpotQA](https://hotpotqa.github.io/)のdistractor devを使った。公式の回答と支持文の評価を利用できる。

今回の対象はdev全体7405問ではなく、事前に固定した長さ制限付き30問だけ。各問を五条件で一度ずつ実行した。

| 条件 | Workerの役割 | Workerが見る文書 | 後段 |
| --- | --- | --- | --- |
| C0 | 単一・neutral | 全文 | なし |
| C1 | 三人ともneutral | 全員が全文 | Synthesizer |
| C2 | 三つの異なる役割 | 全員が全文 | Synthesizer |
| C3 | 三人ともneutral | 担当ごとに分割 | Synthesizer |
| C4 | 三つの異なる役割 | 担当ごとに分割 | Synthesizer |

C1〜C4のSynthesizerが受け取るのはWorkerの公開出力で、各Workerのprivateな原文全体ではない。これはRuntimeが意図した情報境界である。ただし、C2とC3を直接比較すると**役割と文書アクセスの両方**が変わる。二条件の差を、そのまま「文書分割だけの因果効果」と呼べない。

## 30問×5条件は完走した。しかし、集計の読み方は二段階になる

最終的に150ケース、正常なモデル生成510件を揃えた。予約台帳は511件で、差の1件は送信前のjournal保存失敗である。失敗した予約を消したり払い戻したりはせず、別campaignで承認済みの最小復旧を行い、元のpartial記録も残した。完了は独立した監査で確認した。

公式評価のAnswer F1は次のとおりだった。1に近いほど回答文字列が正解に近い。

| 条件 | 全30問・探索的 | fresh24・事前指定の主比較に使用 |
| --- | ---: | ---: |
| C0 | 0.718 | 0.674 |
| C1 | 0.734 | 0.695 |
| C2 | **0.758** | **0.724** |
| C3 | 0.599 | 0.567 |
| C4 | 0.565 | 0.567 |

最初の6問ではPilotを先に見ている。そのため、30問すべてを未使用の検証標本のように扱わず、事前指定した推論は残りのfresh24に限定した。主比較C3−C2の平均Answer F1差は**−0.1564**。条件付きbootstrapの95%区間は[−0.2985, −0.0399]、seedを固定したsign-flip検定は`p=0.0301`だった。24問中18問は同点で、差があった6問はすべてC3の方が低い。副比較は多重比較補正後、いずれも`p>0.05`だった。

少なくともこの標本・このモデルでは、「情報を分けたC3の方が良い」という期待は支持されなかった。逆に「Multi-Agent一般に分割は有害」とも言えない。単一モデル、temperature 0の一反復、長さで選んだ小標本であり、問題間で登場人物や文書が重なる可能性もある。区間推定を独立同分布の24試行として強く一般化するのは危うい。またC2はAnswer F1 0.758を得ており、「ローカルモデルが何も解けず、差が見えなかった」という床効果だけではこの結果を説明できない。

## Workerが見た証拠は、どこで失われたのか

この差を見て気になったのは、情報の受け渡しだった。C3でWorkerの引用がgold支持文を含む割合は0.847だったが、最終回答の支持文recallは0.592だった。Worker群が関連文を指していても、最後の回答に十分残っていないように見える。

ただし、**引用IDの一致は、その文の意味を正しく読めた証明ではない。** 保存済み出力のうち、C2が正答しC3がExact Matchで外した3問を読むと、少なくとも二種類の失敗が見える。

- 映画監督の出自を問う問題では、C3の一人のWorkerが「Deeyah KhanはPunjabi/Pashtun系」という正答に必要な事実を公開出力に書いていた。それでもSynthesizerは「Norwegian」と答えた。この例では、事実は受け渡されており、後段の選択・統合に失敗した。
- ブログ執筆者の生年を問う問題では、Workerに渡された原文に「Sean Michael Carroll ... born October 5, 1966」があった。しかしそのWorkerは生年情報がないと述べ、別のWorkerは人物を取り違え、Synthesizerは1936年と答えた。ここでは、原文からWorkerの公開出力を作る段階で重要情報が落ちている。
- BAFTAの司会者の生年月日を問う問題でも、Workerの入力にはGraham Nortonの生年月日があったが、公開出力はそれを取り出せず、別の人物の情報も混じった。最終回答は不確実とされた。

調べた3問では、Workerの公開出力そのものはSynthesizerの入力に保存されていた。したがって「Runtimeの転送中に文字列が欠けた」と断定する根拠はない。一方、Workerが原文を要約・選択する時点の意味的な欠落と、届いた情報をSynthesizerが使い損ねる失敗は、どちらも起こり得る。3問の事例確認は機構の手掛かりであって、30問全体の原因割合を確定する人手評価でも、因果実験でもない。

情報を分割すると引用の重複が減るのは、アクセス権が重ならない設計から機械的にも生じる。重複が少ないことを、独立した発想や高品質な統合の証拠にはしない。

## 次に検証したいのは、分割そのものではなく公開境界だ

現時点で私が立てられる仮説は、「情報分割による性能低下の一部は、Workerの公開Artifactに必要な事実が残らないこと、またはSynthesizerが残った事実を使えないことから生じる」というものだ。これは今回の実験で証明した結論ではない。

切り分けるなら、保存済みC3 Worker出力を固定し、Synthesizerへ渡すものだけを変える追加実験が必要になる。例えば、現行の要約のみ、要約に引用元の短い原文を添える条件、同じtoken量の無関係な文章を添える対照条件を比較する。これなら「追加tokenが効いただけ」と「必要な証拠が復元された」を多少は分けて考えられる。ただしこれは**提案であり、まだ実行していない**。新しい実験には事前計画、予算、freeze、独立campaignが要る。

前編では「誰が何を見られるか」を実装した。後編で分かったのは、境界が守られ、実験が完走しても、**誰が何を相手に伝えられたか**は別の問題だということだった。情報を分けるだけでは、知識を統合できない。次に設計・検証すべき場所は、その公開境界にある。

## Repositoryと根拠資料

本文の集計と環境値は以下の保存記録に基づく。Git管理外の生データ・実行DB・詳細journalは、これらのリンクからすべて取得できるわけではない。元の記録を公開可能な要約と混同しないため、未公開草稿のままにしている。

- [前編と執筆引き継ぎ](https://github.com/bosakun/multi-agent-runtime/tree/582d82e2df69111a7f04b9cc4c5aaf3017c2d714/docs/articles)
- [HotpotQA Windows本実験・完了報告](https://github.com/bosakun/multi-agent-runtime/blob/c86e6fba2350ecfea6a2da1d718fb89377bd4570/experiments/epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)
- [Windows / NVIDIA / Ollamaガイド](https://github.com/bosakun/multi-agent-runtime/blob/c86e6fba2350ecfea6a2da1d718fb89377bd4570/docs/windows-nvidia-ollama.md)
- [HotpotQAの公開ベンチマーク](https://hotpotqa.github.io/)
