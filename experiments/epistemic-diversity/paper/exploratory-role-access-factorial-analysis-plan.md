# Existing Role × Access grid — exploratory analysis plan

2026-10-02。**post-hoc / exploratory plan only**。既存30問のみ、新model callなし。今回はfactorial analysis、p値・CI・regression・再集計を実行していない。[Protocol 3.1](../docs/protocol-3.1-hotpotqa-main.md)のfresh24主比較C3−C2、P2〜P5、multiplicity方針、既存のdescriptive interactionの位置づけは変更しない。

## 既存条件の配置

| | Full access | Partitioned access |
| --- | --- | --- |
| Neutral role | C1 | C3 |
| Diverse role | C2 | C4 |

C1〜C4はsame model、3 Workers＋1 Synthesizerの同じ協調構造である。C0はsingle-agent baselineなのでfactorial gridへ入れない。accessは外部documentの割当であり、roleや事前学習知識を同じものとしない。input token量が同一でないため、構造だけの効果へ一般化しない。

## possible contrasts（計算していない）

question iの既存Answer F1を`Y_i(Ck)`とする。

- Role contrasts: full内`C2−C1`、partitioned内`C4−C3`。
- Access contrasts: neutral内`C3−C1`、diverse内`C4−C2`。
- 平均Role contrast候補: `[(C2−C1)+(C4−C3)]/2`。
- 平均Access contrast候補: `[(C3−C1)+(C4−C2)]/2`。
- Interaction候補: `(C4−C3)−(C2−C1)`（同値に`(C4−C2)−(C3−C1)`）。Protocol 3.1のdescriptive interactionをconfirmatoryへ昇格させない。

全てquestion内paired quantitiesであり、120 cellsを独立sampleとしない。本計画の全30問解析はpilot6問を含むpost-hoc記述とする。fresh24を別に示す場合も、主比較を置き換えたり新たなconfirmatory発見と呼んだりしない。

## 実行前に固定する事項

endpoint（Answer F1を第一候補）、対象範囲30／fresh24別層、missingの扱い、contrast family、descriptiveのみか探索的CIを出すか、multiplicity・software version・source hashesを人間が決める。CIを採るならquestion-clustered paired bootstrapで4条件を同時に保持し、seed/drawsを事前固定する。今回は設定を実行せず新数値を作らない。

N=30、1モデル、1反復、文書length選択、弱いrole manipulation、partition依存、質問間依存、compute/input差、pilot/復旧phaseをlimitationsとして併記する。多contrastの中から好都合なものだけ強調しない。p値を後から主結果として選ぶ方式をとらず、rare outcomesに不安定な回帰・mixed effectsを主結論の根拠としない。

この配置はC2/C3の二要因同時変更を認めるための設計上の説明であり、純粋なaccess causal effectをC2/C3から分離したという結果ではない。今後の未使用標本・別モデル・反復・role-only/access-only・compute統制・Artifact表現介入は、human review→failure pattern→specific hypothesis→人間の新たな計画という順序で相談する。本計画は次の実験の実行承認ではない。
