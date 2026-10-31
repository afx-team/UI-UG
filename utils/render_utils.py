"""JSON DSL to HTML, with optional explicit Playwright screenshots."""
import argparse
import base64
from html import escape
import json
import os
from pathlib import Path
import re


class DslRenderer:
    """Render the HTML-tag subset of the supplied UI DSL."""

    def _find_data_fields_recursive(self, node, fields):
        if not isinstance(node, dict):
            return
        for config in node.get("params", {}).values():
            if isinstance(config, dict) and config.get("bindType") == "Data":
                field = config.get("bindField")
                if field:
                    fields[field] = config.get("bindMock", f"Sample{field}")
        for child in node.get("children", []):
            self._find_data_fields_recursive(child, fields)

    def generate_mock_data(self, dsl_json_string):
        tree = json.loads(dsl_json_string)
        fields = {}
        self._find_data_fields_recursive(tree, fields)
        return fields

    def render(self, dsl_json_string, data=None):
        return self._render_node_recursive(json.loads(dsl_json_string), data or {})

    def _render_node_recursive(self, node, data):
        if not isinstance(node, dict) or node.get("type") not in ("Tag", "Component"):
            raise ValueError("DSL node requires type Tag or Component")
        if node["type"] == "Component":
            raise ValueError("Component nodes require the matching front-end component runtime")
        tag = node.get("name", "div")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", tag):
            raise ValueError("Invalid HTML tag")
        if tag.lower() in {"script", "iframe", "object", "embed", "base", "meta", "link", "style"}:
            raise ValueError("Unsupported DSL tag")
        attributes = []
        if node.get("className"):
            attributes.append('class="' + escape(str(node["className"]), quote=True) + '"')
        text = ""
        for name, config in node.get("params", {}).items():
            if not isinstance(config, dict):
                raise ValueError("DSL parameter definitions must be objects")
            if config.get("bindType") == "Static":
                value = config.get("value", "")
            elif config.get("bindType") == "Data":
                value = data.get(config.get("bindField"), "")
            else:
                raise ValueError("Unknown DSL binding type")
            if name == "textContent":
                text = escape(str(value))
            else:
                if not re.fullmatch(r"[A-Za-z_:][A-Za-z0-9_.:-]*", name) or name.lower().startswith("on"):
                    raise ValueError("Invalid DSL attribute")
                if name.lower() in ("href", "src") and str(value).strip().lower().startswith("javascript:"):
                    raise ValueError("Invalid URL attribute")
                attributes.append(name + '="' + escape(str(value), quote=True) + '"')
        attrs = (" " + " ".join(attributes)) if attributes else ""
        if tag.lower() in {"img", "br", "hr", "input", "source", "wbr", "area", "col"}:
            return f"<{tag}{attrs}>"
        children = "".join(self._render_node_recursive(child, data) for child in node.get("children", []))
        return f"<{tag}{attrs}>{text}{children}</{tag}>"


def build_html(dsl_data, tailwind_css_path=None, font_ttf_path=None):
    renderer = DslRenderer()
    if isinstance(dsl_data, dict) and "dsl_code" in dsl_data:
        code = dsl_data["dsl_code"]
        mock = dsl_data.get("mock_data")
        data = json.loads(mock) if isinstance(mock, str) else mock
    else:
        code = dsl_data if isinstance(dsl_data, str) else json.dumps(dsl_data)
        data = None
    if data is None:
        data = renderer.generate_mock_data(code)
    css_path = tailwind_css_path or os.getenv("TAILWIND_CSS_PATH")
    font_path = font_ttf_path or os.getenv("FONT_TTF_PATH")
    css = Path(css_path).read_text() if css_path else ""
    font = ""
    if font_path:
        encoded = base64.b64encode(Path(font_path).read_bytes()).decode("ascii")
        font = "@font-face{font-family:UISans;src:url(data:font/ttf;base64," + encoded + ")}body{font-family:UISans,sans-serif}"
    body = renderer.render(code, data)
    return ('<!doctype html><html><head><meta charset="utf-8"><style>'
            + css + font + '</style></head><body style="margin:0">'
            + '<div id="component-root" style="display:inline-block">' + body + '</div></body></html>')


def capture_component_screenshot(html_content, output_path, target_selector="#component-root"):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 800, "height": 600}, java_script_enabled=False)
            page.set_content(html_content)
            page.locator(target_selector).screenshot(path=str(output_path), timeout=15000)
        finally:
            browser.close()


def process_and_screenshot_task(renderer, dsl_data, output_path, html_name=None):
    html = build_html(dsl_data)
    if html_name:
        Path(html_name).write_text(html)
    capture_component_screenshot(html, output_path)
    return f"Success: {Path(output_path).name}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON DSL file")
    parser.add_argument("--html", required=True, help="Output HTML file")
    parser.add_argument("--png", help="Optional screenshot; explicitly starts Chromium")
    parser.add_argument("--tailwind-css")
    parser.add_argument("--font")
    args = parser.parse_args()
    html = build_html(json.loads(Path(args.input).read_text()), args.tailwind_css, args.font)
    Path(args.html).write_text(html)
    if args.png:
        capture_component_screenshot(html, args.png)


if __name__ == "__main__":
    main()
