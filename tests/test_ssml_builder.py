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


def test_tone_cues_stripped():
    """Tone/mood cues like (輕鬆語氣) should be stripped, not read aloud."""
    result = text_to_ssml("(輕鬆語氣)大家好(語氣上揚)歡迎(輕笑)")
    assert "輕鬆語氣" not in result
    assert "語氣上揚" not in result
    assert "輕笑" not in result
    assert "大家好" in result
    assert "歡迎" in result


def test_mixed_cues_and_pauses():
    """Tone cues stripped while pauses still convert to SSML breaks."""
    result = text_to_ssml("(興奮語氣)太棒了(停頓)(認真語氣)接下來")
    assert "興奮語氣" not in result
    assert "認真語氣" not in result
    assert '<break time="800ms"/>' in result
    assert "太棒了" in result
    assert "接下來" in result
