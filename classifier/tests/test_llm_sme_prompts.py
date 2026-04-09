from classifier.labeling.prompts import render_prompt, prompt_sha


def test_render_prompt_stable_hash():
    ctx = {
        "source_framework": "owasp_llm",
        "source_id": "LLM01",
        "source_text": "Prompt injection risk",
        "target_framework": "mitre_atlas",
        "target_node_id": "mitre_atlas:AML.T0051.000",
        "target_text": "Direct prompt injection technique",
    }
    sys1, usr1 = render_prompt(ctx)
    sys2, usr2 = render_prompt(ctx)
    assert sys1 == sys2
    assert usr1 == usr2
    h = prompt_sha(sys1, usr1)
    assert len(h) == 64
    assert prompt_sha(sys2, usr2) == h


def test_render_prompt_includes_ids():
    ctx = {
        "source_framework": "owasp_llm", "source_id": "LLM01",
        "source_text": "x", "target_framework": "mitre_atlas",
        "target_node_id": "mitre_atlas:AML.T0054", "target_text": "y",
    }
    _, usr = render_prompt(ctx)
    assert "LLM01" in usr
    assert "mitre_atlas:AML.T0054" in usr
