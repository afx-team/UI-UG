"""Coordinate parsing and explicit conversion; no ground-truth-dependent guessing."""
import json
import math
import re


def parse_coordinates(text):
    """Accept one JSON point/box, optionally enclosed in a Markdown code fence."""
    value = (text or '').strip()
    if value.startswith('```'):
        value = re.sub(r'^```(?:json)?\s*|\s*```$', '', value)
    try:
        result = json.loads(value)
    except (ValueError, TypeError):
        return None
    return result if isinstance(result, list) and len(result) in (2, 4) else None


def to_pixel_box(coordinates, width, height, mode, order='xy'):
    if mode not in ('0-1', '0-1000', 'pixel') or order not in ('xy', 'yx'):
        raise ValueError('Unknown coordinate mode/order')
    if width <= 0 or height <= 0 or not isinstance(coordinates, (list, tuple)):
        raise ValueError('Invalid image size or coordinates')
    if len(coordinates) not in (2, 4):
        raise ValueError('Expected a point or bounding box')
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) for value in coordinates):
        raise ValueError('Coordinates must be finite numbers')
    values = list(coordinates)
    if len(values) == 2:
        values *= 2
    if order == 'yx':
        values = [values[1], values[0], values[3], values[2]]
    if mode != 'pixel':
        maximum = 1 if mode == '0-1' else 1000
        if any(value < 0 or value > maximum for value in values):
            raise ValueError('Coordinates outside the declared range')
        values = [value / maximum * (width if index % 2 == 0 else height)
                  for index, value in enumerate(values)]
    x1, y1, x2, y2 = values
    if not (0 <= x1 <= x2 <= width and 0 <= y1 <= y2 <= height):
        raise ValueError('Invalid or out-of-bounds box')
    return values
