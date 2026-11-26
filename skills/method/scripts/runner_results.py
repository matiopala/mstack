"""Read a named case from a test runner's result."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def junit_case(output, selector):
    try:
        root = ET.fromstring(output)
    except (ET.ParseError, ValueError, LookupError):
        return "unverified", None
    if root.tag not in ("testsuite", "testsuites"):
        return "unverified", None
    matches = []
    pending = [(root, None)]
    while pending:
        node, inherited_file = pending.pop()
        source = node.get("file") or inherited_file
        if node.tag in ("testsuite", "testsuites"):
            pending.extend((child, source) for child in node)
        elif node.tag == "testcase":
            name = ".".join(filter(None, [node.get("classname"), node.get("name")]))
            if name == selector:
                matches.append((node, source))
    if len(matches) != 1:
        return "unverified", None
    case, source = matches[0]
    status = case.get("status", "run").lower()
    result = case.get("result", "completed").lower()
    if (status not in ("run", "passed", "completed", "failed")
            or result not in ("completed", "passed", "failed")
            or any(child.tag not in ("failure", "system-out", "system-err", "properties") for child in case)):
        return "unverified", source
    if case.find("failure") is not None:
        return "fail", source
    if status == "failed" or result == "failed":
        return "unverified", source
    return "pass", source


def unittest_case(output, selector):
    try:
        record = json.loads(output)
    except (ValueError, UnicodeError):
        return "unverified", None
    if isinstance(record, dict) and record.get("selector") == selector:
        matches = record.get("matches")
        if isinstance(matches, list) and len(matches) == 1 and isinstance(matches[0], dict) and matches[0].get("file"):
            return matches[0].get("outcome"), matches[0]["file"]
    return "unverified", None


def tap_case(output, selector):
    lines = [line.strip() for line in output.decode("utf-8", errors="replace").splitlines()
             if line.strip() and not line.strip().startswith("#")]
    if lines and lines[0] == "TAP version 13":
        lines.pop(0)
    if len(lines) == 2 and "1..1" in lines:
        lines.remove("1..1")
        if "#" not in lines[0]:
            return {f"ok 1 - {selector}": "pass", f"not ok 1 - {selector}": "fail"}.get(lines[0], "unverified")
    return "unverified"


def selected_result(report_format, selector, output, exit_code, workspace, test_files, expected_source=None):
    source = None
    if report_format == "unittest":
        outcome, source = unittest_case(output, selector)
    elif report_format == "junit":
        outcome, source = junit_case(output, selector)
    else:
        outcome = tap_case(output, selector)
    if source:
        root = Path(workspace).resolve()
        try:
            source = str((root / source).resolve().relative_to(root))
        except (ValueError, OSError, RuntimeError):
            return "unverified", None
        if source not in test_files:
            outcome = "unverified"
    if expected_source and expected_source != source:
        outcome = "unverified"
    if (outcome == "pass" and exit_code == 0) or (outcome == "fail" and exit_code > 0):
        return outcome, source
    return "unverified", source
