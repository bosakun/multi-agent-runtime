# 人工semantic boundary例 — 教材仕様のみ

すべて架空のentity・値・文章。real HotpotQA、実研究case、pilot labels、human票ではない。人工例のexpected categoryは判定規則の仕様を説明するもので、コードが自然言語を自動判定する機能ではない。

共通reference：`青葉研究所は2012年に設立された`。question/pathが設立年のみを要する場合と完全日付を要する場合を区別する。

| 重要label / rule | Clear positive example | Boundary example | Counterexample（そのlabelにしない） |
| --- | --- | --- | --- |
| semantic correct / GEN-SEM-001, S2-CORRECT-001 | 「青葉研究所の創設年は2012年」 | 年だけ必要なら「2012年」でentityが局所的に一意なら可 | 「2013年」はdistorted |
| partial / S2-PARTIAL-001 | referenceが「2012年3月4日」で完全日付が必要なのに「2012年」のみ | 設立年だけ必要なpathなら年のみでもcorrect | 「2013年3月4日」はpartialでなくdistorted |
| distorted / S2-DISTORT-001 | 「青葉研究所は2013年設立」 | 「北研究所が南研究所を運営」を逆転する記述もdistorted | 正しい一意なparaphraseをdistortedにしない |
| absent / S2-ABSENT-001 | public recordがcitation IDだけでfactの記述なし | 読める空のfindingsもabsent | public recordが失われているならmissing |
| unclear / S2-UNCLEAR-001 | 同じ文脈で2研究所があり「それは2012年創設」で指示先が決まらない | 「青葉か北が2012年」は一意な対象主張なし | 明白な「2013年」をunclearで弱めずdistorted |
| missing / GEN-MISS-001 | public recordそのものが存在しない | fileはあるが破損して読めない→unreadable | 読める空outputはmissingでなくabsent |
| alias / GEN-ALIAS-001 | rawが「青葉研究所（以下A研）」と定義 | 同名2entityならunclear | 外部知識だけで略称を補完しない |
| normalization / GEN-NORM-001 | 明示された同一単位で「1,000」↔「1000」 | 「03/04」は暦・日月順が不明ならunclear | 年のみを完全日付に正規化しない |
| unsupported addition / GEN-ADD-001 | 元factの必要qualifierに未支持な「唯一」を追加→unclear候補 | 別claimは別に記録し対象factと混ぜない | 原文が複数を明示するのに「唯一」はdistorted |
| S0 complete / S0-PRESENCE-001 | 登録setの文が必要fact全体を支持 | 同factを支持する別setがcompleteならORでcomplete | gold IDだけでsemantic completeにはしない |
| S0 partial / S0-PRESENCE-001 | 完全日付factの原文に年のみ | registered factが年のみならcomplete | 根拠全くなしはabsent |
| S0 absent / S0-PRESENCE-001 | complete rawには所在地しかなく設立情報なし | sourceが欠損ならmissing | 曖昧な複数解釈はunclear |
| S0 unclear / S0-PRESENCE-001 | reference mappingのentityが一意でない | pointerの対応未確定も根拠を記録 | 明示された矛盾をunclearへ隠さない |
| S1 complete / S1-ACCESS-001 | set={s1,s2}が当該Worker実inputに両方ある | alternative set={s3}だけでも十分性yesならcomplete | Worker間unionを個人completeにしない |
| S1 partial / S1-ACCESS-001 | set={s1,s2}のs1だけ見える | 十分なalternative setがあればcomplete | 何もないこと確認済みならnone |
| S1 none / S1-ACCESS-001 | 実inputを照合し全registered supportが不在 | parametricな正答はaccessを変えない | input不明をnoneにしない |
| S1 unclear / S1-ACCESS-001 | actual inputのsentence mapping不能 | input欠損ならmissing metadata併記 | intended partition一致だけでcompleteにしない |
| S3 retained / S3-RETENTION-001 | separate beforeのcorrect factがafterにも同じ意味 | 語順変更でも保持可 | aliasではretainedでなくNA |
| S3 partial_loss / S3-RETENTION-001 | before完全日付→after年のみ、日付必要 | pathが年のみならretained | 年が2013へ変わるならdistorted |
| S3 distorted / S3-RETENTION-001 | before2012→after2013 | 関係方向の反転も該当 | 元beforeから誤っているときpublication failureを新規帰属しない |
| S3 lost / S3-RETENTION-001 | beforeのcorrect factがafterから全消失 | 一部残存ならpartial_loss | before absentのcascadeをlostとしない |
| S3 unclear / S3-RETENTION-001 | before/afterを読めるがafterの指示先不明 | before欠損はmissing | identity_aliasをunclear semantic retentionとして採点しない |
| identity_alias / S3-ALIAS-001 | provenanceで同一public outputのaliasと確認→NA | text一致だけならtransition unknownの可能性 | NAをpublication success/failureへ補完しない |
| unknown / S3-UNKNOWN-001 | before/afterの出自が不明→non-identifiable | S4がcorrectでもpublication帰属は不明 | unknownをpublication失敗と数えない |
| S4 route / S4-ROUTE-001 | Artifactにfact不在、補足原文にcorrect→supplementary | 両routeに同一fact→both | supplementaryをWorker survivalへ帰属しない |
| machine match / S4-MACHINE-001 | 同じ誤年payloadが届く→matchだがdistorted | 無関係metadata mismatchは別diagnostic | payload matchからcorrectを生成しない |
| S5a reflected / S5A-RELATION-001 | final「2012年」は対象answer factを表現 | entityがquestionで一意なら短答可 | bridge非記載はnot_asserted |
| S5a contradicted / S5A-RELATION-001 | final「2013年」がregistered yearと矛盾 | 必要な否定の逆転も矛盾 | 非記載を矛盾にしない |
| S5a not_asserted / S5A-RELATION-001 | short answerにbridgeの運営関係を書かない | pathの支持はS5bで別確認 | これだけでfailureにしない |
| S5a unclear / S5A-RELATION-001 | finalのentity指示が複数解釈 | 読めないfinalはmissing | 明白な誤年をunclearにしない |
| S5b fully_supported / S5B-SUPPORT-001 | S4のcomplete pathが2012を支持しfinalも2012 | bridgeがfinalにないがpath内にそろうなら可 | goldだけ一致しS4にpathがなければprimary successでない |
| S5b partially_supported / S5B-SUPPORT-001 | 複数主要claimのうち受信pathが一部のみ支持 | primary complete-path subsetを保った感度値は別 | 完全に誤った主claimをpartialへ弱めない |
| S5b unsupported / S5B-SUPPORT-001 | complete received pathは2012、final主要claimは2013 | path不在の場合はsecondary観測、primary不適格 | partial supportをunsupported eventに自動変換しない |
| S5b unclear / S5B-SUPPORT-001 | 読めるfinalの主要claimが曖昧 | 競合解釈をpointerで記録 | 既知誤答scoreだけでunsupportedとしない |
| structural NA / GEN-NA-001 | identity_aliasに独立S3なし | 非適用理由を明記 | 空出力や欠損をNAにしない |

## Pathと協議の人工例

raw：青葉の設立年2012、北の設立年2015。比較question「どちらが先か」へのpathは登録2年＋2012<2015の比較relationで十分（PATH-LOGIC-001）。各年はこのpath内required=yes。別pathが存在してもこのrequirednessは変えない。冗長な所在地factはrequired=no。

rawに直接「青葉は北より早い」という別の十分な文があれば、system output開示前にR1候補として登録・R2で妥当性確認したalternative pathはvalid候補。goldと異なることはinvalid理由にならない。

rawに「青葉は首都にある」とだけあり、国の首都名を外部知識で補うpathはinvalid（未登録external factual premise）。同名entity linkingが不明ならpath=unclear。モデルの正答を見て思いついたshortcutはpost_freeze_candidate_pathでありprimary追加不可。

partial対distortedの協議では「年は2012だが日付が欠ける」と「年を2013と誤る」をGEN-PART-001 / GEN-DIST-001で分ける。両者が指示先を確定できなければADJ-UNCLEAR-001でunclear。これらは人工の教材例であり、実adjudication recordは今回保存しない。
