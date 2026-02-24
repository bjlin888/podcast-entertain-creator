from __future__ import annotations

from linebot.v3.messaging import (
    FlexContainer,
    FlexMessage,
    PostbackAction,
    QuickReply,
    QuickReplyItem,
    TextMessage,
)


# ── LLM Selection ─────────────────────────────────────────


def build_llm_select_quick_reply() -> QuickReply:
    return QuickReply(
        items=[
            QuickReplyItem(
                action=PostbackAction(label="Claude", data="llm=claude", display_text="Claude"),
            ),
            QuickReplyItem(
                action=PostbackAction(label="Gemini", data="llm=gemini", display_text="Gemini"),
            ),
        ]
    )


def build_welcome_message() -> TextMessage:
    return TextMessage(
        text=(
            "歡迎使用 Podcast Entertainment Creator!\n"
            "我可以協助你產製 Podcast 內容。\n\n"
            "請先選擇你想使用的 AI 模型："
        ),
        quick_reply=build_llm_select_quick_reply(),
    )


# ── Info Collection Quick Replies ──────────────────────────


def build_duration_quick_reply() -> QuickReply:
    return QuickReply(
        items=[
            QuickReplyItem(action=PostbackAction(label="15 分鐘", data="duration=15", display_text="15 分鐘")),
            QuickReplyItem(action=PostbackAction(label="30 分鐘", data="duration=30", display_text="30 分鐘")),
            QuickReplyItem(action=PostbackAction(label="45 分鐘", data="duration=45", display_text="45 分鐘")),
            QuickReplyItem(action=PostbackAction(label="60 分鐘", data="duration=60", display_text="60 分鐘")),
        ]
    )


def build_style_quick_reply() -> QuickReply:
    return QuickReply(
        items=[
            QuickReplyItem(action=PostbackAction(label="輕鬆閒聊", data="style=輕鬆閒聊", display_text="輕鬆閒聊")),
            QuickReplyItem(action=PostbackAction(label="知識教學", data="style=知識教學", display_text="知識教學")),
            QuickReplyItem(action=PostbackAction(label="訪談對話", data="style=訪談對話", display_text="訪談對話")),
            QuickReplyItem(action=PostbackAction(label="故事敘述", data="style=故事敘述", display_text="故事敘述")),
        ]
    )


# ── Title Flex Messages ────────────────────────────────────


def build_title_flex_message(titles: list[dict]) -> FlexMessage:
    """Build a carousel of title bubbles for TITLE_REVIEW."""
    bubbles = []
    for i, t in enumerate(titles, 1):
        bubble = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"#{i}", "size": "sm", "color": "#888888"},
                    {"type": "text", "text": t["title_zh"], "weight": "bold", "size": "lg", "wrap": True, "margin": "sm"},
                    {"type": "text", "text": t.get("title_en", ""), "size": "sm", "color": "#999999", "wrap": True, "margin": "md"},
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "postback", "label": "選擇這個標題", "data": f"select_title={t['title_id']}"},
                        "style": "primary",
                    }
                ],
            },
        }
        bubbles.append(bubble)

    return FlexMessage(
        alt_text="候選標題",
        contents=FlexContainer.from_dict({"type": "carousel", "contents": bubbles}),
    )


# ── Script Segment Flex Messages ───────────────────────────

_SEGMENT_TYPE_LABEL = {"opening": "開場", "main": "主題", "closing": "結尾"}


def build_segment_flex(segment: dict, index: int) -> FlexMessage:
    """Build a Flex bubble for a single script segment."""
    seg_type = segment.get("segment_type", "main")
    label = _SEGMENT_TYPE_LABEL.get(seg_type, seg_type)
    content_preview = segment["content"][:200] + ("..." if len(segment["content"]) > 200 else "")

    bubble = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"段落 {index + 1} — {label}", "weight": "bold", "size": "lg"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": content_preview, "wrap": True, "size": "sm"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "修改這段",
                        "data": f"edit_segment={segment['segment_id']}",
                    },
                    "style": "secondary",
                    "flex": 1,
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "生成示範音檔",
                        "data": f"tts_segment={segment['segment_id']}",
                    },
                    "style": "primary",
                    "flex": 1,
                },
            ],
        },
    }
    return FlexMessage(
        alt_text=f"段落 {index + 1} — {label}",
        contents=FlexContainer.from_dict(bubble),
    )


# ── TTS Quick Replies ──────────────────────────────────────


def build_voice_quick_reply() -> QuickReply:
    return QuickReply(
        items=[
            QuickReplyItem(action=PostbackAction(label="女聲", data="voice=cmn-TW-Wavenet-A", display_text="女聲")),
            QuickReplyItem(action=PostbackAction(label="男聲", data="voice=cmn-TW-Wavenet-C", display_text="男聲")),
        ]
    )


def build_speed_quick_reply() -> QuickReply:
    return QuickReply(
        items=[
            QuickReplyItem(action=PostbackAction(label="慢 (0.8x)", data="speed=0.8", display_text="慢速")),
            QuickReplyItem(action=PostbackAction(label="正常 (1.0x)", data="speed=1.0", display_text="正常")),
            QuickReplyItem(action=PostbackAction(label="快 (1.2x)", data="speed=1.2", display_text="快速")),
        ]
    )


# ── Voice Comparison Flex ──────────────────────────────────


def build_voice_comparison_flex(tts_url: str, host_url: str) -> FlexMessage:
    """Side-by-side comparison bubble for TTS vs host recording."""
    bubble = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "語音對照", "weight": "bold", "size": "lg"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "TTS 示範", "weight": "bold", "flex": 1},
                        {
                            "type": "button",
                            "action": {"type": "uri", "label": "播放", "uri": tts_url},
                            "style": "primary",
                            "height": "sm",
                            "flex": 1,
                        },
                    ],
                },
                {"type": "separator"},
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "主持人錄音", "weight": "bold", "flex": 1},
                        {
                            "type": "button",
                            "action": {"type": "uri", "label": "播放", "uri": host_url},
                            "style": "secondary",
                            "height": "sm",
                            "flex": 1,
                        },
                    ],
                },
            ],
        },
    }
    return FlexMessage(
        alt_text="語音對照：TTS vs 主持人錄音",
        contents=FlexContainer.from_dict(bubble),
    )


# ── Feedback Scoring Flex ──────────────────────────────────


def _score_buttons(aspect: str, label: str) -> dict:
    """Generate a row of 1-5 score buttons for a single aspect."""
    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": [
            {"type": "text", "text": label, "weight": "bold", "size": "sm"},
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "postback", "label": str(i), "data": f"score_{aspect}={i}"},
                        "style": "secondary",
                        "height": "sm",
                    }
                    for i in range(1, 6)
                ],
            },
        ],
    }


def build_scoring_flex() -> FlexMessage:
    """Build a Flex bubble with 3 scoring aspects (1-5 each)."""
    bubble = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "腳本評分", "weight": "bold", "size": "lg"},
                {"type": "text", "text": "請為每個面向打 1-5 分", "size": "sm", "color": "#999999"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "lg",
            "contents": [
                _score_buttons("content", "內容品質"),
                _score_buttons("engagement", "吸引力"),
                _score_buttons("structure", "結構完整度"),
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "評分後可輸入文字回饋，或輸入「滿意」完成。", "size": "xs", "color": "#999999", "wrap": True},
            ],
        },
    }
    return FlexMessage(
        alt_text="腳本評分",
        contents=FlexContainer.from_dict(bubble),
    )
