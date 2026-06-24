#!/usr/bin/env python3
"""Generuje importovatelnu iOS Skratku (.shortcut, binarny plist) z vstavanych
akcii: stiahne TikTok video (+cover) cez tikwm a ulozi do Fotiek.

Vyhne sa akciam tretich appiek (a-Shell), takze sa da importovat. NEROBI frame 0
(vstavane akcie iOS nevedia dekodovat snimok) -> uklada cover obrazok.
"""
import plistlib
import uuid
from pathlib import Path

OUT = Path(__file__).resolve().parent / "Download_TikTok.shortcut"


def uid() -> str:
    return str(uuid.UUID(int=0)).upper()  # nahradeny nizsie deterministicky


def new_uuid(i: int) -> str:
    # deterministicke, citatelne UUID (Math.random nie je dostupny)
    return f"00000000-0000-0000-0000-{i:012d}"


def text_with_input(prefix: str) -> dict:
    """Textovy token s vlozenou premennou Shortcut Input (ExtensionInput)."""
    placeholder = "￼"
    string = prefix + placeholder
    loc = len(prefix)
    return {
        "WFSerializationType": "WFTextTokenString",
        "Value": {
            "string": string,
            "attachmentsByRange": {
                f"{{{loc}, 1}}": {"Type": "ExtensionInput"},
            },
        },
    }


def var_ref(name: str) -> dict:
    """Odkaz na pomenovanu premennu."""
    return {
        "WFSerializationType": "WFTextTokenAttachment",
        "Value": {"Type": "Variable", "VariableName": name},
    }


def action(identifier: str, params: dict) -> dict:
    return {
        "WFWorkflowActionIdentifier": identifier,
        "WFWorkflowActionParameters": params,
    }


actions = []

# 1) URL: tikwm API s vlozenym vstupom (zdielany odkaz)
actions.append(action("is.workflow.actions.url", {
    "WFURLActionURL": text_with_input("https://www.tikwm.com/api/?hd=1&url="),
}))

# 2) Get Contents of URL (GET) -> JSON odpoved
actions.append(action("is.workflow.actions.downloadurl", {
    "WFHTTPMethod": "GET",
}))

# 3) Uloz JSON do premennej API
actions.append(action("is.workflow.actions.setvariable", {
    "WFVariableName": "API",
}))

# 4) data -> play  (URL videa)
actions.append(action("is.workflow.actions.getvalueforkey", {
    "WFInput": var_ref("API"),
    "WFGetDictionaryValueType": "Value",
    "WFDictionaryKey": "data",
}))
actions.append(action("is.workflow.actions.getvalueforkey", {
    "WFGetDictionaryValueType": "Value",
    "WFDictionaryKey": "play",
}))

# 5) Stiahni video a uloz do Fotiek
actions.append(action("is.workflow.actions.downloadurl", {"WFHTTPMethod": "GET"}))
actions.append(action("is.workflow.actions.savetocameraroll", {}))

# 6) data -> origin_cover (cover obrazok)
actions.append(action("is.workflow.actions.getvalueforkey", {
    "WFInput": var_ref("API"),
    "WFGetDictionaryValueType": "Value",
    "WFDictionaryKey": "data",
}))
actions.append(action("is.workflow.actions.getvalueforkey", {
    "WFGetDictionaryValueType": "Value",
    "WFDictionaryKey": "origin_cover",
}))
actions.append(action("is.workflow.actions.downloadurl", {"WFHTTPMethod": "GET"}))
actions.append(action("is.workflow.actions.savetocameraroll", {}))

# 7) Notifikacia
actions.append(action("is.workflow.actions.notification", {
    "WFNotificationActionBody": "Hotovo - video a cover su vo Fotkach.",
    "WFNotificationActionTitle": "Stiahni TikTok",
}))

workflow = {
    "WFWorkflowClientVersion": "2605.0.5",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowIcon": {
        "WFWorkflowIconStartColor": 4274264319,
        "WFWorkflowIconGlyphNumber": 61440,
    },
    "WFWorkflowImportQuestions": [],
    "WFWorkflowTypes": ["ActionExtension"],
    "WFWorkflowInputContentItemClasses": [
        "WFStringContentItem",
        "WFURLContentItem",
    ],
    "WFWorkflowHasShortcutInputVariables": True,
    "WFWorkflowActions": actions,
}

# Validacia struktury: round-trip cez plistlib
data = plistlib.dumps(workflow, fmt=plistlib.FMT_BINARY)
reloaded = plistlib.loads(data)
assert reloaded["WFWorkflowActions"][0]["WFWorkflowActionIdentifier"] == "is.workflow.actions.url"
OUT.write_bytes(data)
print(f"OK -> {OUT}  ({len(data)} bytes, {len(actions)} akcii)")
