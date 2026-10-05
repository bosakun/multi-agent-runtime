# Adjudication Rules — candidate v0.2.0

2026-10-05。**未採用・実協議0件**。[CODEBOOK](CODEBOOK.md)の候補と同時にpilotで確認する。人間の判断をコードで置き換えない。

## 独立性と保存

<!-- rule: ADJ-INDEPENDENT-001 -->
同一batch・同一版の判定中は2名で相談しない。registry R1/R2とstageの各独立票を別々にimmutable lockし、両者の票・lock hash・時刻・資料版を保持する。pilotでも同じ順序。各batch内の全arm票を揃えてから協議し、片方のunfinished票へ協議内容を戻さない。mainのS1→S5 progressive disclosureを保持する。

<!-- rule: ADJ-IAA-001 -->
協議前の票とmatching unit一覧を保存し、pre-adjudication IAAを再計算可能にする。raw agreement、matrix、marginals、missing/applicabilityを区別する。adjudicated labelsからagreementを計算しない。pilotのIAAはguidelineの曖昧さ確認であり研究結果や妥当性証明ではない。

## 解決の優先順位

<!-- rule: ADJ-PRIORITY-001 -->
1. 採用版Codebookの明示rule（pilotではbatch-frozen candidate、mainではhuman-frozen v1.0）。
2. evidence pointerとactual saved record（before/after、actual input、最終文字列）。
3. frozen Fact Registry、support set・path・requiredness。goldだけに経路を狭めない。
4. 同じ版と整合するcalibration precedent。
5. 解決不能はunclear（導出の未確定summaryはundetermined）。多数決や正答scoreで決めない。

規則とrawが矛盾する／registry自体に問題がある場合は、規則で原文を覆い隠さずambiguityを記録する。pilotではrevision候補、mainではSTOP→amendment手順。false precisionでラベルを確定しない。

<!-- rule: ADJ-UNCLEAR-001 -->
双方がrecordを確認しても合理的な読みが複数残れば、semantic adjudicated_label=unclear、resolution_status=unresolved。record欠損ならnull＋missing_recordでありunclearへ変換しない。identity_aliasはNA / no_separate_transition、unknown transitionは非識別のまま。root causeやfirst failureを人間の票欄へ足さない。

## 記録必須項目

unit_id、field、reviewer1_label、reviewer2_label、adjudicated_label、reason、guideline_rule（stable ID）、**evidence_pointer**、adjudicator、timestamp、codebook_version、resolution_statusを保存する。元票のhash / lock / source版へのリンクも協議資料のmanifestへ残す。両者labelを勝手に訂正してからIAAを出さない。original labelsは上書きせずadjudication_logとfinal_adjudicated_labelsへ別version保存する。候補規則が不十分ならambiguity logにaffected fields、競合label、既存rule、修正候補、blockerかを残す。

## 第三者・訂正

翻訳ambiguityはGEN-TRANS-001と[固定訳方針](BILINGUAL-REVIEW-POLICY.md)を適用する。協議recordのevidence_pointerに英語原文位置と固定訳のpair位置/hashを対応づけ、原文基準で検討する。解決不能はunclear、翻訳修正が必要なら停止・新版・両者への同一修正版・全影響判定の再判定とし、旧訳・独立票は保持する。

<!-- rule: ADJ-THIRD-001 -->
第三adjudicatorを使うか、適格性、担当範囲、いつ開示するかを**pilot/main開始前に**人間が固定する。今回担当者は未選定。不一致を見て都合のよいcaseだけ第三者を導入しない。第三者なしなら2名discussion後も未解決をunclearとして残す。非独立の協議票をhuman reviewer追加1名と数えない。

<!-- rule: ADJ-AMEND-001 -->
事務的誤記の訂正も旧票を保持し、追加version・理由・影響IAAを記録する。semantic guidelineの変更はpilot中はchange log＋新candidate版で全影響pilot unitsを再判定／旧票保存。main開始後はSTOP→amendment→new version→事前定義したaffected scopeの全case再判定→旧票保存。結果に合うcaseだけrelabellingしない。

人工boundary例は[examples](examples/semantic-boundaries.md)。実caseの協議や判定例の追加は人間がpilotを実施した後のみ行う。
