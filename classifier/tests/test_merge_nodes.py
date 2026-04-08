import json
from pathlib import Path
from classifier.data.frameworks.merge_nodes import merge_into_nodes_json

REPO = Path(__file__).resolve().parents[2]


def test_merge_preserves_existing_frameworks(tmp_path):
    base = [
        {"node_id": "owasp_llm:LLM01", "framework": "owasp_llm", "title": "x", "text": "x"},
        {"node_id": "aiuc_1:CTL-1", "framework": "aiuc_1", "title": "y", "text": "y"},
    ]
    new1 = [{"node_id": "owasp_dsgai:DSGAI01", "framework": "owasp_dsgai", "title": "z", "text": "z"}]
    new2 = [{"node_id": "eu_ai_act:Art1", "framework": "eu_ai_act", "title": "a", "text": "a"}]

    base_path = tmp_path / "nodes.json"
    base_path.write_text(json.dumps(base))

    new_dir = tmp_path / "frameworks"
    new_dir.mkdir()
    (new_dir / "owasp_dsgai.json").write_text(json.dumps(new1))
    (new_dir / "eu_ai_act.json").write_text(json.dumps(new2))

    result = merge_into_nodes_json(base_path, new_dir)
    merged = json.loads(base_path.read_text())
    assert len(merged) == 4
    fws = {n["framework"] for n in merged}
    assert {"owasp_llm", "aiuc_1", "owasp_dsgai", "eu_ai_act"} == fws
    assert result["added"] == 2 and result["base"] == 2 and result["total"] == 4


def test_merge_does_not_duplicate_on_re_run(tmp_path):
    base = [{"node_id": "owasp_dsgai:DSGAI01", "framework": "owasp_dsgai", "title": "x", "text": "x"}]
    new = [{"node_id": "owasp_dsgai:DSGAI01", "framework": "owasp_dsgai", "title": "x", "text": "x"}]
    base_path = tmp_path / "nodes.json"
    base_path.write_text(json.dumps(base))
    new_dir = tmp_path / "frameworks"
    new_dir.mkdir()
    (new_dir / "owasp_dsgai.json").write_text(json.dumps(new))
    merge_into_nodes_json(base_path, new_dir)
    merged = json.loads(base_path.read_text())
    assert len(merged) == 1
