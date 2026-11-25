#!/usr/bin/env python3
"""Update Antigravity conversation title across all three storage layers.

Layers updated:
1. annotations/<cid>.pbtxt
2. agyhub_summaries_proto.pb
3. conversation_summaries.db (SQLite + FTS index)
"""

import argparse
import os
import re
import sqlite3


def resolve_antigravity_home(cli_home=None):
    if cli_home:
        return os.path.abspath(os.path.expanduser(cli_home))
    env_home = os.environ.get("ANTIGRAVITY_HOME")
    if env_home:
        return os.path.abspath(os.path.expanduser(env_home))
    # Auto-detect from script location: <any-drive>/.../.gemini/config/skills/chinese-summary/scripts/set_title.py
    inferred_gemini = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    inferred_ag = os.path.join(inferred_gemini, "antigravity")
    if os.path.isfile(os.path.join(inferred_ag, "conversation_summaries.db")) or os.path.isdir(
        os.path.join(inferred_ag, "annotations")
    ):
        return inferred_ag
    gemini_home = os.environ.get("GEMINI_HOME")
    if gemini_home:
        cand = os.path.join(os.path.abspath(os.path.expanduser(gemini_home)), "antigravity")
        if os.path.isdir(cand):
            return cand
    return os.path.join(os.path.expanduser("~"), ".gemini", "antigravity")


# Minimal Protobuf wire-format helpers (stdlib-only, zero external dependencies)
def decode_protobuf(data):
    if not data:
        return []
    i = 0
    fields = []
    while i < len(data):
        key = 0
        shift = 0
        while True:
            b = data[i]
            i += 1
            key |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        field_num = key >> 3
        wire_type = key & 7
        if wire_type == 0:
            val = 0
            shift = 0
            while True:
                b = data[i]
                i += 1
                val |= (b & 0x7F) << shift
                if not (b & 0x80):
                    break
                shift += 7
            fields.append((field_num, wire_type, val))
        elif wire_type == 2:
            length = 0
            shift = 0
            while True:
                b = data[i]
                i += 1
                length |= (b & 0x7F) << shift
                if not (b & 0x80):
                    break
                shift += 7
            val = data[i : i + length]
            i += length
            fields.append((field_num, wire_type, val))
        else:
            fields.append((field_num, wire_type, None))
            break
    return fields


def encode_varint(n):
    res = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            res.append(b | 0x80)
        else:
            res.append(b)
            break
    return bytes(res)


def encode_field(field_num, wire_type, val):
    key = (field_num << 3) | wire_type
    if wire_type == 0:
        return encode_varint(key) + encode_varint(val)
    if wire_type == 2:
        return encode_varint(key) + encode_varint(len(val)) + val
    raise ValueError(f"Unsupported wire type: {wire_type}")


def encode_protobuf(fields):
    out = bytearray()
    for f_num, w_type, val in fields:
        out.extend(encode_field(f_num, w_type, val))
    return bytes(out)


def update_raw_summary(blob, new_title):
    if not blob:
        return blob
    fields = decode_protobuf(blob)
    new_fields = []
    for f_num, w_type, val in fields:
        if f_num == 1:
            new_fields.append((f_num, w_type, new_title.encode("utf-8")))
        elif f_num == 15:
            try:
                subfields = decode_protobuf(val)
                new_subfields = []
                for sf_num, sf_type, sf_val in subfields:
                    if sf_num == 1:
                        new_subfields.append((sf_num, sf_type, new_title.encode("utf-8")))
                    else:
                        new_subfields.append((sf_num, sf_type, sf_val))
                new_fields.append((f_num, w_type, encode_protobuf(new_subfields)))
            except Exception:
                new_fields.append((f_num, w_type, val))
        else:
            new_fields.append((f_num, w_type, val))
    return encode_protobuf(new_fields)


def apply_title_update(cid, new_title, base_dir=None):
    base_dir = resolve_antigravity_home(base_dir)
    ann_dir = os.path.join(base_dir, "annotations")
    ann_file = os.path.join(ann_dir, f"{cid}.pbtxt")
    pb_file = os.path.join(base_dir, "agyhub_summaries_proto.pb")
    db_file = os.path.join(base_dir, "conversation_summaries.db")

    # 1. Update annotations/<cid>.pbtxt
    os.makedirs(ann_dir, exist_ok=True)
    if os.path.exists(ann_file):
        with open(ann_file, "r", encoding="utf-8") as f:
            content = f.read()
        if re.search(r'title:\s*"[^"]*"', content):
            new_content = re.sub(r'title:\s*"[^"]*"', f'title:"{new_title}"', content)
        else:
            new_content = content.rstrip() + f'\ntitle:"{new_title}"\n'
        with open(ann_file, "w", encoding="utf-8") as f:
            f.write(new_content)
    else:
        with open(ann_file, "w", encoding="utf-8") as f:
            f.write(f'title:"{new_title}"\n')

    # 2. Update agyhub_summaries_proto.pb
    if os.path.exists(pb_file):
        with open(pb_file, "rb") as f:
            pb_data = f.read()
        top_fields = decode_protobuf(pb_data)
        new_top_fields = []
        for fn, wt, val in top_fields:
            sub = decode_protobuf(val)
            sub_cid = None
            for sfn, swt, sval in sub:
                if sfn == 1 and swt == 2:
                    sub_cid = sval.decode("utf-8", errors="ignore")
            if sub_cid == cid:
                new_sub = []
                for sfn, swt, sval in sub:
                    if sfn == 2:
                        new_sub.append((sfn, swt, update_raw_summary(sval, new_title)))
                    else:
                        new_sub.append((sfn, swt, sval))
                new_top_fields.append((fn, wt, encode_protobuf(new_sub)))
            else:
                new_top_fields.append((fn, wt, val))
        with open(pb_file, "wb") as f:
            f.write(encode_protobuf(new_top_fields))

    # 3. Update SQLite database & FTS index
    if os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        row = cur.execute(
            "SELECT raw_summary FROM conversation_summaries WHERE conversation_id = ?",
            (cid,),
        ).fetchone()
        if row:
            new_raw = update_raw_summary(row[0], new_title)
            cur.execute(
                "UPDATE conversation_summaries SET title = ?, preview = ?, raw_summary = ? WHERE conversation_id = ?",
                (new_title, new_title, new_raw, cid),
            )
            try:
                cur.execute(
                    "UPDATE conversations_fts SET title = ? WHERE conversation_id = ? AND title != ''",
                    (new_title, cid),
                )
            except sqlite3.OperationalError:
                pass
            conn.commit()
            cur.execute("PRAGMA wal_checkpoint(FULL);")
        conn.close()

    print(f"Successfully updated conversation {cid} title to: {new_title}")


def main():
    parser = argparse.ArgumentParser(
        description="Update Antigravity conversation title across all storage layers."
    )
    parser.add_argument("--cid", required=True, help="Conversation ID to update")
    parser.add_argument("--title", required=True, help="New Chinese title (4-10 characters)")
    parser.add_argument(
        "--home",
        default=None,
        help="Optional Antigravity data dir (defaults to $ANTIGRAVITY_HOME or ~/.gemini/antigravity)",
    )
    args = parser.parse_args()
    apply_title_update(args.cid, args.title, base_dir=args.home)


if __name__ == "__main__":
    main()
