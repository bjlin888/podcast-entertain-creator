from app.tts.ssml_builder import text_to_ssml


def test_basic_text():
    result = text_to_ssml("你好世界")
    assert result == "<speak>你好世界</speak>"


def test_pause():
    result = text_to_ssml("第一段(停頓)第二段")
    assert '<break time="800ms"/>' in result


def test_long_pause():
    result = text_to_ssml("段落一(長停頓)段落二")
    assert '<break time="1500ms"/>' in result


def test_bgm_stripped():
    result = text_to_ssml("[BGM fade in]歡迎收聽[BGM fade out]")
    assert "BGM" not in result
    assert "歡迎收聽" in result


def test_sfx_stripped():
    result = text_to_ssml("[SFX: applause]謝謝大家")
    assert "SFX" not in result
    assert "謝謝大家" in result


def test_emphasis():
    result = text_to_ssml("這是(強調)重點(/強調)內容")
    assert '<emphasis level="strong">重點</emphasis>' in result


def test_soft_voice():
    result = text_to_ssml("(輕聲)悄悄話(/輕聲)")
    assert '<prosody volume="soft">悄悄話</prosody>' in result
