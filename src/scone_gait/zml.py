"""Minimal parser for ZML, the configuration format used by SCONE.

ZML is a list of ``key = value`` pairs and ``key { ... }`` blocks. Values are
bare words, quoted strings, arrays in square brackets, or nested blocks.
``#`` starts a comment. Keys may repeat (a gait template has one ``GaitPlot``
block per plot), so blocks are returned as lists of ``(key, value)`` pairs.

Only the subset needed for SCONE gait analysis templates and scenario files is
supported.
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[{}\[\]=]|[^\s{}\[\]="]+')

Block = list[tuple[str, object]]


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for line in text.splitlines():
        # drop comments that are not inside a quoted string
        out, in_string = [], False
        for ch in line:
            if ch == '"':
                in_string = not in_string
            if ch == "#" and not in_string:
                break
            out.append(ch)
        tokens.extend(_TOKEN.findall("".join(out)))
    return tokens


class ZmlError(ValueError):
    pass


def _unquote(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] == '"':
        return token[1:-1].replace('\\"', '"')
    return token


def _parse_value(tokens: list[str], i: int) -> tuple[object, int]:
    if i >= len(tokens):
        raise ZmlError("unexpected end of input, expected a value")
    tok = tokens[i]
    if tok == "{":
        return _parse_block(tokens, i + 1, closing="}")
    if tok == "[":
        items: list[object] = []
        i += 1
        while i < len(tokens) and tokens[i] != "]":
            value, i = _parse_value(tokens, i)
            items.append(value)
        if i >= len(tokens):
            raise ZmlError("missing ']'")
        return items, i + 1
    if tok in "}]=":
        raise ZmlError(f"unexpected {tok!r}")
    return _unquote(tok), i + 1


def _parse_block(tokens: list[str], i: int, closing: str | None) -> tuple[Block, int]:
    block: Block = []
    while i < len(tokens):
        tok = tokens[i]
        if tok == closing:
            return block, i + 1
        if tok in "{}[]=":
            raise ZmlError(f"unexpected {tok!r}, expected a key")
        key = _unquote(tok)
        i += 1
        if i < len(tokens) and tokens[i] == "=":
            i += 1
        elif i < len(tokens) and tokens[i] in "{[":
            pass
        else:
            raise ZmlError(f"expected '=' or '{{' after {key!r}")
        value, i = _parse_value(tokens, i)
        block.append((key, value))
    if closing is not None:
        raise ZmlError(f"missing {closing!r}")
    return block, i


def parse_zml(text: str) -> Block:
    block, _ = _parse_block(_tokenize(text), 0, closing=None)
    return block


def get(block: Block, key: str, default: object = None) -> object:
    """First value stored under key in a block."""
    for k, v in block:
        if k == key:
            return v
    return default
