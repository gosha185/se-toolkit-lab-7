"""Inline keyboard buttons for common actions.

Provides keyboard layouts for quick user actions.
"""

from typing import List, Tuple


def get_quick_actions_keyboard() -> List[List[Tuple[str, str]]]:
    """Return inline keyboard buttons for common actions.

    Returns:
        List of rows, each row is a list of (label, callback_data) tuples.
    """
    return [
        [
            ("🏥 Health", "health"),
            ("📚 Labs", "labs"),
        ],
        [
            ("📊 Scores Lab-01", "scores_lab-01"),
            ("📊 Scores Lab-02", "scores_lab-02"),
            ("📊 Scores Lab-03", "scores_lab-03"),
        ],
        [
            ("📊 Scores Lab-04", "scores_lab-04"),
            ("📊 Scores Lab-05", "scores_lab-05"),
            ("📊 Scores Lab-06", "scores_lab-06"),
        ],
        [
            ("👥 Top Learners", "top_learners"),
            ("📈 Completion Rate", "completion_rate"),
        ],
    ]


def get_help_keyboard() -> List[List[Tuple[str, str]]]:
    """Return keyboard for help menu."""
    return [
        [
            ("What labs are available?", "query_what_labs"),
            ("Show my scores", "query_scores"),
        ],
        [
            ("Who are top students?", "query_top"),
            ("Compare groups", "query_groups"),
        ],
    ]


def format_keyboard_message(text: str, keyboard: List[List[Tuple[str, str]]]) -> str:
    """Format a message with keyboard hint for Telegram.

    Note: Full inline keyboard support requires aiogram types.
    This returns a text hint for now.

    Args:
        text: Main message text
        keyboard: Keyboard layout

    Returns:
        Formatted message with button hints
    """
    button_hints = []
    for row in keyboard:
        for label, _ in row:
            button_hints.append(f"• {label}")

    return f"{text}\n\n🔘 Quick actions:\n" + "\n".join(button_hints)
