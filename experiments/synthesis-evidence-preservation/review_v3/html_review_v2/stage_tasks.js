// Presentation/input layer only. No semantic judgments or future-stage sources.
let unit = 0;
const recordNames = {
  input: "最初のAIが実際に読んだ文章",
  public: "そのAIが他のAIに伝えた文章",
  shared: "共有用のデータに移った後の文章",
  received: "最後に回答を作るAIが実際に読んだ文章",
  final: "最終回答"
};
const questions = {
  S1: "この事実と判断できる内容が、最初のAIが実際に読んだ文章の中にありますか？",
  S2: "この事実は、他のAIに伝えた文章に正しく残っていますか？",
  S3: "この事実は、共有前の文章から共有用のデータへ移った後も残っていますか？",
  S4: "この事実は、最後に回答を作るAIが実際に読んだ文章に正しく入っていますか？",
  S5a: "最終回答は、この事実を述べていますか、それとも矛盾していますか？",
  S5b: "ここに示す事実の組み合わせを含む受信証拠から、最終回答を支持できますか？"
};
function content(p) {
  if (Array.isArray(p)) return p.map(content).join("");
  if (p && typeof p === "object" && !Object.hasOwn(p, "ja"))
    return Object.values(p).map(content).join("");
  return pair(p);
}
function activeGroups(c, a, rowStage) {
  const kinds = {S1:["input"],S2:["public"],S3:["public","shared"],S4:["received"],S5a:["received","final"],S5b:["received","final"]}[rowStage];
  return (c.observed || []).filter(g => kinds.includes(g.kind)).map(g => {
    const perWorker = ["input","public","shared"].includes(g.kind);
    const items = perWorker && a.worker_id ? (g.worker ? (g.worker === a.worker_id ? g.items : []) : g.items.filter(x => x.id === a.worker_id)) : g.items;
    return {...g, items};
  }).filter(g => !g.worker || !a.worker_id || g.worker === a.worker_id);
}
function compare() {
  const c=rows[index], row=c.form[unit], a=row.annotation;
  const factIds = a.fact_id ? [a.fact_id] : (c.paths.find(p => p.id === a.path_id)?.facts || []);
  const targets = factIds.map(id => c.facts.find(f => f.id === id)).filter(Boolean);
  let base='<section class="card question"><h2>① 今回確認する事実'+(row.stage === "S5b" ? "の組み合わせ" : "")+'</h2>';
  base += targets.length ? targets.map(f => '<div class="fact">'+content(f.text)+'</div>').join("") : '<p>対象の記録がありません。担当者へ報告してください。</p>';
  if(row.stage === "S5b") base += '<p>この組み合わせは事前に決まっています。新しい事実を追加したり、組み合わせを作り直したりしないでください。</p>';
  base += '<details><summary>質問と元の資料を確認</summary>'+content(c.question)+(c.reference||[]).map(x=>content(x.text)).join("")+'</details></section>';
  let observed='<section class="card observed"><h2>② 実際の文章</h2>';
  for(const g of activeGroups(c,a,row.stage)) {
    observed+='<section class="entry"><h3>'+esc(recordNames[g.kind])+'</h3>';
    if(g.available === false) observed+='<p>文章の記録がありません。判断を決めず担当者へ報告してください。</p>';
    if(g.transition === "identity_alias") observed+='<p>共有前後は同じ記録です。別の移行段階がないため、この判定は対象外です。</p>';
    if(g.transition === "unknown") observed+='<p>別の移行段階があるか記録から確認できません。</p>';
    observed += g.items.map(x=>'<div class="sentence">'+(x.route?'<p class="subtle">'+(x.route === "Artifact" ? "AI同士で共有された情報" : "追加された資料")+'</p>':"")+content(x.text)+'</div>').join("");
    if(!g.items.length && g.available !== false) observed+='<p>この文章の一覧には該当する記録がありません。</p>';
    observed+='</section>';
  }
  return '<div class="columns">'+base+observed+'</section></div>';
}
function renderLabels() {
  const c=rows[index], s=stateFor(), row=c.form[unit], a=row.annotation, i=unit;
  let opts=stateOptions[row.stage]||[];
  if(a.publication_transition_type === "identity_alias" || a.applicability === "not_applicable") opts=["NA"];
  let out='<section class="card"><h2>③ あなたの判定</h2><p class="fact">'+esc(questions[row.stage])+'</p><p>書いてある内容だけを比べてください。AIの考えを推測しません。迷ったら英語原文を確認してください。</p>';
  const stageLabels = row.stage === "S3" ? {retained:"残っている：共有前の事実が共有後にも正しく残っている",partial_loss:"一部が消えた：共有前にあった事実の一部が欠けている",distorted:"変わった：共有後の重要な内容が事実と矛盾している",lost:"消えた：共有前にあった事実が共有後には書かれていない"} : {};
  for(const value of opts) out+='<label class="choice"><input type="radio" name="label-'+i+'" value="'+esc(value)+'" '+(s.labels[i]===value?'checked':'')+'>'+esc(stageLabels[value]||labelText[value]||value)+'<small class="canonical">'+esc(value)+'</small></label>';
  if(row.stage === "S4") out+='<label>この事実が書かれていたのはどちらですか？<select data-route="'+i+'"><option value="">選んでください</option>'+Object.entries({artifact:"AI同士で共有された情報",supplementary_evidence:"追加された資料",both:"両方",neither:"どちらにもない",unclear:"判断できない"}).map(([v,t])=>'<option value="'+v+'" '+(s.routes[i]===v?'selected':'')+'>'+t+'</option>').join("")+'</select></label>';
  if(s.labels[i]==="NA" && a.publication_transition_type!=="identity_alias") out+='<label>対象外とした理由<textarea data-na-reason="'+i+'">'+esc(s.naReasons[i]||"")+'</textarea></label>';
  out+='<label>判断理由／判断できない場合は迷った点<textarea data-note="'+i+'">'+esc(s.notes[i]||"")+'</textarea></label><p>判断の根拠になった文章を選んでください（任意）。</p>';
  for(const [gno,g] of activeGroups(c,a,row.stage).entries()) for(const [n,x] of g.items.entries()) {
    const pointer=x.id||('display:'+gno+':'+n);
    out+='<label class="choice"><input type="checkbox" data-evidence-choice="'+i+'" value="'+esc(pointer)+'" '+((s.evidence[i]||[]).includes(pointer)?'checked':'')+'>'+content(x.text)+'</label>';
  }
  out+='<details><summary>詳細情報（担当者向け）</summary><pre>'+esc(JSON.stringify({stage:row.stage,fact_id:a.fact_id,path_id:a.path_id,worker_id:a.worker_id},null,2))+'</pre></details><button id="export" class="primary">この問題の回答をJSONとして保存</button><p>この問題のすべての判定を終えてから保存してください。入力は資料そのものを書き換えません。</p><button id="clear-case">この問題の下書きを消す</button></section>';
  return out;
}
function draw() {
  const c=rows[index], row=c.form[unit];
  document.getElementById("counter").textContent='問題 '+(index+1)+' / '+rows.length+' ・ 判定 '+(unit+1)+' / '+c.form.length;
  document.getElementById("progressbar").style.width=((unit+1)/c.form.length*100)+'%';
  root.innerHTML=(c.synthetic?'<p class="mark">SYNTHETIC CALIBRATION MATERIAL · NOT STUDY DATA · NOT MODEL OUTPUT</p>':"")+'<section class="taskbox"><h2>今回確認すること</h2><p>'+esc(questions[row.stage])+'</p><p>'+esc(guide.purpose)+'</p><p class="subtle">この段階ではまだ見ないもの：'+esc(guide.avoid)+'</p></section>'+compare()+renderLabels()+'<div class="navrow"><button id="previous" '+(index===0&&unit===0?'disabled':'')+'>前の判定</button><span>判定 '+(unit+1)+' / '+c.form.length+'</span><button id="next" '+(index===rows.length-1&&unit===c.form.length-1?'disabled':'')+'>次の判定</button></div><p id="save-status">入力はこのブラウザの下書きに保存されます。</p>';
  root.querySelector('#previous').onclick=()=>navigate(-1);
  root.querySelector('#next').onclick=()=>navigate(1);
  root.querySelectorAll('input[type="radio"]').forEach(el=>el.onchange=()=>{stateFor().labels[unit]=el.value;save();draw()});
  root.querySelectorAll('[data-note]').forEach(el=>el.oninput=()=>{stateFor().notes[unit]=el.value;save()});
  root.querySelectorAll('[data-na-reason]').forEach(el=>el.oninput=()=>{stateFor().naReasons[unit]=el.value;save()});
  root.querySelectorAll('[data-route]').forEach(el=>el.onchange=()=>{stateFor().routes[unit]=el.value;save()});
  root.querySelectorAll('[data-evidence-choice]').forEach(el=>el.onchange=()=>{stateFor().evidence[unit]=[...root.querySelectorAll('[data-evidence-choice]:checked')].map(x=>x.value);save()});
  root.querySelector('#export').onclick=exportBallot;
  root.querySelector('#clear-case').onclick=()=>{delete memory[c.case_id];save();draw()};
  document.getElementById('clear-all').onclick=()=>{memory={};try{localStorage.removeItem(key)}catch(_e){}draw()};
}
function navigate(delta) {
  save();unit+=delta;
  if(unit<0){index--;unit=rows[index].form.length-1}
  if(unit>=rows[index].form.length){index++;unit=0}
  draw();
}
