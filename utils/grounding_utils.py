"""Visualize structured boxes with an explicit coordinate convention."""
import json
from io import BytesIO
from pathlib import Path
from utils.coordinates import parse_coordinates, to_pixel_box


def visualize_box_image(name, url, boxes_with_labels_ori, coord_parser="0-1000", resized_size=None):
    from PIL import Image, ImageDraw
    if str(url).startswith(("http://", "https://")):
        import requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")
    else:
        image = Image.open(url).convert("RGB")
    boxes = json.loads(boxes_with_labels_ori) if isinstance(boxes_with_labels_ori, str) else boxes_with_labels_ori
    draw = ImageDraw.Draw(image)
    aliases = {"norm": "0-1", "qwen2": "0-1000", "pixel": "pixel"}
    mode = aliases.get(coord_parser, coord_parser)
    for index, item in enumerate(boxes):
        raw = parse_coordinates(item["box"]) if isinstance(item["box"], str) else item["box"]
        if mode == "sr":
            if not resized_size or len(resized_size) != 2:
                raise ValueError("Resized-pixel boxes require explicit resized_size=(width, height)")
            box = to_pixel_box(raw, *resized_size, "pixel")
            box = [value * image.size[i % 2] / resized_size[i % 2] for i, value in enumerate(box)]
        else:
            box = to_pixel_box(raw, *image.size, mode)
        draw.rectangle(box, outline="lime", width=2)
        draw.text((box[0], max(0, box[1] - 12)), f'{index}: {item.get("type", item.get("category", ""))}', fill="red")
    output = Path(f"{name}.png")
    image.save(output)
    return output
