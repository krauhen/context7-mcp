import logging
import re
import sys

from http import HTTPStatus

from loguru import logger
from starlette.routing import Route, Mount

level_icons = {
    "DEBUG": "🐞",
    "INFO": "ℹ️ ",
    "SUCCESS": "✅",
    "WARNING": "⚠️ ",
    "ERROR": "🛑",
    "CRITICAL": "💥",
}


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(exception=record.exc_info, depth=6).log(level, record.getMessage())


def escape_invalid_tags(msg):
    known_tags = {
        "red",
        "green",
        "blue",
        "yellow",
        "magenta",
        "cyan",
        "white",
        "black",
        "bold",
        "blink",
        "level",
        "reset",
    }

    def replace_tag(m):
        tag = m.group(1).lstrip("/")
        if tag in known_tags:
            return m.group(0)
        else:
            return m.group(0).replace("<", "&lt;").replace(">", "&gt;")

    return re.sub(r"<(/?\w+)>", replace_tag, msg)


def color_http(message_str):
    HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"]

    def code_color(code):
        if 200 <= code < 300:
            return "green"
        elif 300 <= code < 400:
            return "yellow"
        elif 400 <= code < 600:
            return "red"
        else:
            return "white"

    for method in HTTP_METHODS:
        pattern = rf"\b{method}\b"
        replacement = f"<blue>{method}</blue>"
        message_str = re.sub(pattern, replacement, message_str)

    message_str = re.sub(
        r"\bhttps?\b",
        lambda m: f"<magenta>{m.group(0)}</magenta>",
        message_str,
        flags=re.IGNORECASE,
    )

    for status in HTTPStatus:
        code = str(status.value)
        color = code_color(status.value)
        pattern = rf"\b{code}\b"
        replacement = f"<{color}>{code}</{color}>"
        message_str = re.sub(pattern, replacement, message_str)

    return message_str


def colorize_outside_tags(s):
    result = []
    i = 0

    while i < len(s):
        if s[i] == "<":
            tag_end = s.find(">", i)
            if tag_end != -1:
                potential_tag = s[i : tag_end + 1]
                if re.match(
                    r"</?(?:red|green|blue|yellow|magenta|cyan|white|black|bold|blink|level)>",
                    potential_tag,
                ):
                    result.append(potential_tag)
                    i = tag_end + 1
                    continue

        c = s[i]
        if c == ":":
            result.append("<red>:</red>")
        elif c == "/":
            result.append("<yellow>/</yellow>")
        elif c == ".":
            result.append("<green>.</green>")
        elif c == "{":
            result.append("<red>{</red>")
        elif c == "}":
            result.append("<red>}</red>")
        elif c == "[":
            result.append("<cyan>[</cyan>")
        elif c == "]":
            result.append("<cyan>]</cyan>")
        elif c == "'":
            result.append("<green>'</green>")
        elif c == "_":
            result.append("<magenta>_</magenta>")
        elif c == "-":
            result.append("<magenta>-</magenta>")
        elif c == ",":
            result.append("<green>,</green>")
        else:
            result.append(c)
        i += 1

    return "".join(result)


def validate_balanced_tags(s):
    """Ensure all tags are properly balanced"""
    stack = []

    for match in re.finditer(r"<(/?)(\w+)>", s):
        is_closing = bool(match.group(1))
        tag_name = match.group(2)

        if is_closing:
            if not stack or stack[-1] != tag_name:
                return re.sub(
                    r"</?(?:red|green|blue|yellow|magenta|cyan|white|black|bold|blink|level)>",
                    "",
                    s,
                )
            stack.pop()
        else:
            stack.append(tag_name)

    if stack:
        return re.sub(
            r"</?(?:red|green|blue|yellow|magenta|cyan|white|black|bold|blink|level)>",
            "",
            s,
        )

    return s


def escape_curly_outside_tags(s: str) -> str:
    result = []
    i = 0

    while i < len(s):
        if i < len(s) - 1 and s[i] == "<":
            tag_end = s.find(">", i)
            if tag_end != -1:
                potential_tag = s[i : tag_end + 1]
                if re.match(r"</?(\w+)>", potential_tag):
                    result.append(potential_tag)
                    i = tag_end + 1
                    continue

        c = s[i]
        if c == "{":
            result.append("{{")
        elif c == "}":
            result.append("}}")
        else:
            result.append(c)
        i += 1

    return "".join(result)


def formatter(record):
    try:
        time_str = f"<green>{record['time']:%y-%m-%d %H:%M:%S}</green>"
        icon = level_icons.get(record["level"].name, "")
        if record["level"].name in ["WARNING", "ERROR", "CRITICAL"]:
            icon = f"<blink>{icon}</blink>"

        file_path = record["file"].path
        parts = file_path.split("contex7-python")
        file_path = "." + parts[-1]
        max_len = 25
        line_str = str(record["line"])
        loc_content = f"{file_path}:{line_str}"

        if len(loc_content) > max_len:
            pad_len = max_len - 3
            loc_content = "..." + loc_content[-pad_len:]
        else:
            loc_content = loc_content.ljust(max_len)

        for base_dir in ["src", "eval", "tests"]:
            if base_dir in file_path:
                loc_content = f"<bold>{loc_content}</bold>"
                break

        loc_str = f"<white>{loc_content}</white>"

        message_str = str(record["message"])

        message_str = colorize_outside_tags(message_str)
        message_str = color_http(message_str)
        message_str = escape_curly_outside_tags(message_str)
        message_str = escape_invalid_tags(message_str)

        message_str = validate_balanced_tags(message_str)

        links = [time_str, icon, loc_str, message_str]
        return "|".join(links) + "\n"
    except Exception as e:
        print(f"Formatter error: {e}")
        return f"{record['time']:%y-%m-%d %H:%M:%S} | {record['level'].name} | {record['message']}\n"


def print_settings(settings):
    if settings is not None:
        lines = str(settings).split("\n")
        logger.info(f"<red>{lines[0]}</red>")
        for line in lines[1:]:
            logger.info(line)
    else:
        logger.warning("No settings found")


def print_routes(app):
    if app is not None:
        route_width = 7
        name_width = 15
        path_width = 40

        route_offset = route_width
        name_offset = route_offset + name_width
        path_offset = name_offset + path_width

        route_header_offset = route_offset
        name_header_offset = name_offset
        path_header_offset = path_offset

        def _print_recursive(route):
            if isinstance(route, Route):
                route_name = (
                    route.name[:name_width]
                    if len(route.name) < name_width
                    else route.name[:name_width] + "..."
                )
                route_path = (
                    route.path[:path_width]
                    if len(route.path) < path_width
                    else route.path[:path_width] + "..."
                )
                logger.info(
                    f"{'Route'.ljust(route_offset)}{route_name.ljust(name_offset)}{route_path.ljust(path_offset)}{route.methods}"
                )
            elif isinstance(route, Mount):
                _print_recursive(route.routes)

        header_methods = (
            "<red>"
            + "type".ljust(route_header_offset)
            + "name".ljust(name_header_offset)
            + "path".ljust(path_header_offset)
            + "methods</red>"
        )
        logger.info(header_methods)
        for route in app.routes:
            _print_recursive(route)
    else:
        logger.warning("No FastAPI application found.")


def print_mcp_server(mcp_server):
    if mcp_server is not None:
        name_width = 24
        description_width = 96

        type_end = 7
        name_end = type_end + name_width

        header = (
            "<red>"
            + "type".ljust(type_end)
            + "name".ljust(name_end)
            + "description"
            + "</red>"
        )
        logger.info(header)

        for tool in mcp_server.tools:
            tool_name = (
                tool.name
                if len(tool.name) < name_width
                else tool.name[:name_width] + "..."
            )
            tool_description: str = (
                tool.description
                if len(tool.description) < description_width
                else tool.description[:description_width] + "..."
            )
            parts = tool_description.split("\n")
            tool_description = "\n".join(parts[1:])
            tool_description = tool_description.replace("\n", " ")
            logger.info(
                f"{'Tool'.ljust(type_end)}{tool_name.ljust(name_end)}{tool_description}"
            )


def pretty_logging(app=None, settings=None, mcp_server=None):
    logger.info("")
    logger.info("")
    logger.info("=" * 128)
    logger.info("=" * 128)
    logger.info("=" * 128)
    logger.info("")
    print_settings(settings)
    logger.info("")
    print_routes(app)
    logger.info("")
    print_mcp_server(mcp_server)
    logger.info("")
    logger.info("=" * 128)
    logger.info("=" * 128)
    logger.info("=" * 128)
    logger.info("")
    logger.info("")


def setup_logging(log_level="INFO", settings=None):
    if settings and hasattr(settings, "log_level"):
        log_level = settings.log_level

    logger.remove()
    logger.add(
        sys.stderr,
        colorize=True,
        format=formatter,
        level=log_level,
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


setup_logging()


if __name__ == "__main__":
    setup_logging()
    logger.info("Testing colors: . / : { } [ ] ' _ - ,")
    logger.info("HTTP test: GET /api/users 200")
    logger.warning("Warning with special chars: {key: 'value'}")
    logger.error("Error message with https://example.com")
