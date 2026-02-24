from app.llm.prompt_builder import load_prompt


def test_load_system_prompt():
    text = load_prompt("system")
    assert "Podcast" in text
    assert "JSON" in text


def test_load_title_generation_with_vars():
    text = load_prompt(
        "title_generation",
        topic="科技趨勢",
        audience="上班族",
        style="輕鬆",
    )
    assert "科技趨勢" in text
    assert "上班族" in text
    assert "輕鬆" in text


def test_load_script_generation_with_vars():
    text = load_prompt(
        "script_generation",
        selected_title="AI 新時代",
        topic="人工智慧",
        audience="學生",
        style="知識型",
        duration_min="30",
        host_count="2",
    )
    assert "AI 新時代" in text
    assert "30" in text


def test_load_script_refinement_with_vars():
    text = load_prompt(
        "script_refinement",
        original_content="原始內容",
        feedback="需要更生動",
        scores="內容:4, 結構:3",
    )
    assert "原始內容" in text
    assert "需要更生動" in text
