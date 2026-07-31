"""Styles and the escape sequences they render as."""

from __future__ import annotations

import pytest

from navkit.style import BLUE, RED, WHITE, Style


def test_default_style_only_resets():
    assert Style().sgr() == "\x1b[0m"


@pytest.mark.parametrize(
    ("style", "expected"),
    [
        (Style(fg=RED), "\x1b[0;31m"),
        (Style(bg=BLUE), "\x1b[0;44m"),
        (Style(fg=WHITE), "\x1b[0;97m"),  # bright colours use the 90/100 range
        (Style(bg=WHITE), "\x1b[0;107m"),
        (Style(fg=200), "\x1b[0;38;5;200m"),  # 256-colour palette
        (Style(bg=200), "\x1b[0;48;5;200m"),
        (Style(fg=(1, 2, 3)), "\x1b[0;38;2;1;2;3m"),  # true colour
        (Style(bg=(1, 2, 3)), "\x1b[0;48;2;1;2;3m"),
        (Style(fg=RED, bg=BLUE), "\x1b[0;31;44m"),
    ],
)
def test_colour_sequences(style, expected):
    assert style.sgr() == expected


@pytest.mark.parametrize(
    ("style", "expected"),
    [
        (Style(bold=True), "\x1b[0;1m"),
        (Style(dim=True), "\x1b[0;2m"),
        (Style(italic=True), "\x1b[0;3m"),
        (Style(underline=True), "\x1b[0;4m"),
        (Style(reverse=True), "\x1b[0;7m"),
        (Style(bold=True, underline=True, fg=RED), "\x1b[0;1;4;31m"),
    ],
)
def test_attribute_sequences(style, expected):
    assert style.sgr() == expected


def test_sequences_are_self_contained():
    # Every sequence starts with a reset, so the renderer can emit one without
    # knowing what was in effect before it.
    for style in (Style(), Style(fg=RED), Style(bold=True, bg=BLUE)):
        assert style.sgr().startswith("\x1b[0")


def test_derive_returns_a_new_style():
    base = Style(fg=RED)
    derived = base.derive(bg=BLUE, bold=True)
    assert derived == Style(fg=RED, bg=BLUE, bold=True)
    assert base == Style(fg=RED)  # unchanged


def test_styles_are_immutable_and_comparable():
    assert Style(fg=RED) == Style(fg=RED)
    assert Style(fg=RED) != Style(fg=BLUE)
    with pytest.raises(AttributeError):
        Style().fg = RED