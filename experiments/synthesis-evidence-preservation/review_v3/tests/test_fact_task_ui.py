"""Mechanical DOM checks of artificial UI, not semantic human annotation."""

import json
import re
import shutil
import subprocess

import pytest
from review_v3.html_display_v1.examples import synthetic_b
from review_v3.html_review_v2.renderer import normalize_b, page_html


@pytest.mark.parametrize("phase", ["S1", "S2", "S3", "S4", "S5"])
def test_one_fixed_annotation_per_screen_and_no_jargon_in_main(phase):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node required for synthetic DOM execution")
    case = normalize_b(synthetic_b(phase), phase)
    text = page_html([case], phase, "synthetic").decode()
    data = re.search(
        r'<script id="review-data" type="application/json">(.*?)</script>', text, re.S
    )[1]
    script = re.search(r"<script>(.*?)</script>", text, re.S)[1]
    harness = r"""
const assert=require('assert');
const els={};
const element=()=>({innerHTML:'',textContent:'',style:{},
  querySelector:()=>({}),querySelectorAll:()=>[]});
global.document={getElementById:id=>els[id]||(els[id]=element())};
document.getElementById('review-data').textContent=DATA;
global.location={search:'?reviewer=synthetic-test&case=0'};
global.localStorage={getItem:()=>null,setItem:()=>{},removeItem:()=>{}};
SCRIPT
const view=els['case-screen'].innerHTML;
const main=view.replace(/<details>[\s\S]*?<\/details>/g,'');
assert(main.includes('① 今回確認する事実'));
assert(main.includes('② 実際の文章'));
assert(main.includes('③ あなたの判定'));
assert.equal((main.match(/name="label-0"/g)||[]).length,EXPECTED);
assert(!main.includes('name="label-1"'));
for(const word of ['Registry','support set','path ID','必要な情報全部',
  '必要な情報がそろっている','根拠sentence ID']) assert(!main.includes(word),word);
assert(main.includes('data-evidence-choice'));
assert(!main.includes('data-evidence="'));
assert(!main.includes('Fact ID'));
console.log('synthetic DOM verified');
"""
    # The synthetic S3 example is structurally NA (identity alias). S5a
    # retains its canonical applicability choice rather than inferring it.
    choices = {"S1": 4, "S2": 5, "S3": 1, "S4": 5, "S5": 5}[phase]
    harness = (
        harness.replace("DATA", json.dumps(data))
        .replace("SCRIPT", script)
        .replace("EXPECTED", str(choices))
    )
    result = subprocess.run(
        [node, "-"], input=harness, capture_output=True, text=True, encoding="utf-8"
    )
    assert result.returncode == 0, result.stderr


def test_worker_groups_preserve_mechanical_identity():
    case = normalize_b(synthetic_b("S1"), "S1")
    assert all(g["kind"] == "input" and g["worker"] for g in case["observed"])
    assert all(row["annotation"]["state"] is None for row in case["form"])
