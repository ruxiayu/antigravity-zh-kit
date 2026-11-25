import argparse
import datetime
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import urllib.parse
import zipfile
from collections import Counter, defaultdict

def _resolve_base_dir() -> str:
    env_home = os.environ.get("ANTIGRAVITY_HOME")
    if env_home:
        return os.path.abspath(os.path.expanduser(env_home))
    # Auto-detect from script location: <any-drive>/.../.gemini/config/skills/session-organizer/scripts/organize_sessions.py
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


def _resolve_set_title_script() -> str:
    sibling = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "chinese-summary", "scripts", "set_title.py")
    )
    if os.path.isfile(sibling):
        return sibling
    return os.path.join(os.path.expanduser("~"), ".gemini", "config", "skills", "chinese-summary", "scripts", "set_title.py")


BASE_DIR = _resolve_base_dir()
DB_PATH = os.path.join(BASE_DIR, "conversation_summaries.db")
ANN_DIR = os.path.join(BASE_DIR, "annotations")
PB_PATH = os.path.join(BASE_DIR, "agyhub_summaries_proto.pb")
BRAIN_DIR = os.path.join(BASE_DIR, "brain")
CONV_DIR = os.path.join(BASE_DIR, "conversations")
BACKUP_ROOT = os.path.abspath(
    os.path.expanduser(os.environ.get("ANTIGRAVITY_BACKUP_DIR") or os.path.join(BASE_DIR, "backups"))
)
SET_TITLE_SCRIPT = _resolve_set_title_script()

STOP_WORDS = {
    "的", "了", "和", "与", "在", "是", "问题", "排查", "修复", "处理", "整理",
    "配置", "解析", "分析", "使用", "优化", "测试", "功能", "方案", "指南", "教程",
    "任务", "继续", "续接", "如何", "怎么", "一下", "一个", "相关", "管理",
}


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def clean_ws(ws: str) -> str:
    s = urllib.parse.unquote(ws or "").strip()
    s = re.sub(r'^\["?(?:file:///)?', "", s)
    s = re.sub(r'"?\]$', "", s)
    return s or "(无工作区)"


def dir_size_bytes(path: str) -> int:
    total = 0
    if not os.path.isdir(path):
        return 0
    for dp, _, fns in os.walk(path):
        for fn in fns:
            fp = os.path.join(dp, fn)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def session_disk_bytes(cid: str) -> int:
    total = dir_size_bytes(os.path.join(BRAIN_DIR, cid))
    for ext in (".db", ".db-wal", ".db-shm"):
        fp = os.path.join(CONV_DIR, f"{cid}{ext}")
        if os.path.isfile(fp):
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def tokenize_title(text: str) -> set:
    if not text:
        return set()
    low = text.lower()
    tokens = set()
    # English/number words (>=2 chars)
    for w in re.findall(r"[a-z0-9][a-z0-9_.-]{1,}", low):
        if len(w) >= 2:
            tokens.add(w)
    # CJK bigrams and trigrams
    for seg in re.findall(r"[\u4e00-\u9fff]+", low):
        if len(seg) == 1:
            continue
        for n in (2, 3):
            for i in range(len(seg) - n + 1):
                g = seg[i : i + n]
                if g not in STOP_WORDS:
                    tokens.add(g)
    return tokens


def first_user_prompt(cid: str, max_chars: int = 240) -> str:
    tpath = os.path.join(BRAIN_DIR, cid, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.isfile(tpath):
        return ""
    try:
        with open(tpath, "r", encoding="utf-8", errors="replace") as f:
            for i, raw in enumerate(f):
                if i > 20:
                    break
                obj = json.loads(raw)
                if obj.get("type") == "USER_INPUT":
                    c = (obj.get("content") or "").strip()
                    m = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", c, re.S)
                    if m:
                        c = m.group(1).strip()
                    return c[:max_chars]
    except Exception:
        pass
    return ""


def parse_dt(s: str):
    if not s:
        return None
    try:
        dt = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None


def create_cold_backup(tag: str, extra_cids=None) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = os.path.join(BACKUP_ROOT, f"session_organizer_{tag}_{ts}")
    os.makedirs(bdir, exist_ok=True)
    for src in (DB_PATH, PB_PATH):
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(bdir, os.path.basename(src)))
    if extra_cids:
        ann_bak = os.path.join(bdir, "annotations")
        os.makedirs(ann_bak, exist_ok=True)
        for cid in extra_cids:
            af = os.path.join(ANN_DIR, f"{cid}.pbtxt")
            if os.path.exists(af):
                shutil.copy2(af, os.path.join(ann_bak, f"{cid}.pbtxt"))
    return bdir


def create_zip_cold_backup(tag: str, cids: list, include_brain: bool = True) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    zpath = os.path.join(BACKUP_ROOT, f"session_organizer_{tag}_{ts}.zip")
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src in (DB_PATH, PB_PATH):
            if os.path.isfile(src):
                zf.write(src, arcname=os.path.join("index", os.path.basename(src)))
        for cid in cids:
            af = os.path.join(ANN_DIR, f"{cid}.pbtxt")
            if os.path.isfile(af):
                zf.write(af, arcname=os.path.join("annotations", f"{cid}.pbtxt"))
            for ext in (".db", ".db-wal", ".db-shm"):
                cf = os.path.join(CONV_DIR, f"{cid}{ext}")
                if os.path.isfile(cf):
                    zf.write(cf, arcname=os.path.join("conversations", f"{cid}{ext}"))
            if include_brain:
                bpath = os.path.join(BRAIN_DIR, cid)
                if os.path.isdir(bpath):
                    for dp, _, fns in os.walk(bpath):
                        for fn in fns:
                            fp = os.path.join(dp, fn)
                            rel = os.path.relpath(fp, BRAIN_DIR)
                            try:
                                zf.write(fp, arcname=os.path.join("brain", rel))
                            except OSError:
                                pass
    if not os.path.isfile(zpath) or os.path.getsize(zpath) == 0:
        raise RuntimeError(f"Cold backup zip verification failed: {zpath}")
    return zpath


def load_top_sessions():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT conversation_id, title, preview, step_count, last_modified_time,
               workspace_uris, status, parent_conversation_id, nesting_depth
        FROM conversation_summaries
        ORDER BY last_modified_time DESC
        """
    ).fetchall()
    conn.close()
    top = [
        r for r in rows
        if (r["nesting_depth"] or 0) == 0 and not (r["parent_conversation_id"] or "")
    ]
    return rows, top


def cmd_audit(args):
    rows, top_level = load_top_sessions()
    total = len(rows)
    non_cjk = [r for r in top_level if not has_cjk(r["title"]) or not (r["title"] or "").strip()]
    short_sessions = [r for r in top_level if (r["step_count"] or 0) <= args.short_steps]

    now = datetime.datetime.now(datetime.timezone.utc)
    stale_30d = []
    ws_counter = Counter()
    for r in top_level:
        ws_counter[clean_ws(r["workspace_uris"])] += 1
        dt = parse_dt(r["last_modified_time"])
        if dt and (now - dt).days >= 30:
            stale_30d.append(r)

    brain_sizes = []
    total_brain_bytes = 0
    if os.path.isdir(BRAIN_DIR):
        title_map = {r["conversation_id"]: (r["title"] or "(未命名)") for r in rows}
        for name in os.listdir(BRAIN_DIR):
            p = os.path.join(BRAIN_DIR, name)
            if os.path.isdir(p):
                sz = dir_size_bytes(p)
                total_brain_bytes += sz
                brain_sizes.append((sz, name, title_map.get(name, "(未在索引中)")))
    brain_sizes.sort(reverse=True)

    print("=== Antigravity 左侧会话体检报告（只读） ===")
    print(f"索引总会话数: {total}（其中顶层主会话: {len(top_level)}）")
    print(f"残留英文/未命名标题: {len(non_cjk)} 条")
    print(f"极短/疑似测试会话 (step_count <= {args.short_steps}): {len(short_sessions)} 条")
    print(f"超过 30 天未活跃会话: {len(stale_30d)} 条")
    print(f"brain/ 目录总占用: {total_brain_bytes / (1024 * 1024):.1f} MB ({len(brain_sizes)} 个目录)")

    print("\n--- 工作区分布 (Top 8) ---")
    for ws, cnt in ws_counter.most_common(8):
        print(f"  {cnt:3d} 条 | {ws}")

    if non_cjk:
        print(f"\n--- 残留英文/未命名标题 (展示前 {args.limit} 条) ---")
        for r in non_cjk[: args.limit]:
            t = (r["title"] or "(空标题)").strip()
            print(f"  {r['conversation_id'][:8]} | steps={r['step_count']:3d} | {r['last_modified_time'][:10]} | {t}")

    if short_sessions:
        print(f"\n--- 极短/疑似测试会话 (展示前 {args.limit} 条) ---")
        for r in short_sessions[: args.limit]:
            t = (r["title"] or "(空标题)").strip()
            print(f"  {r['conversation_id'][:8]} | steps={r['step_count']:3d} | {r['last_modified_time'][:10]} | {t}")

    if brain_sizes:
        print("\n--- 磁盘占用 Top 8 会话 ---")
        for sz, cid, title in brain_sizes[:8]:
            print(f"  {sz / (1024 * 1024):6.1f} MB | {cid[:8]} | {title}")


def cmd_cluster(args):
    _, top = load_top_sessions()
    by_ws = defaultdict(list)
    for r in top:
        by_ws[clean_ws(r["workspace_uris"])].append(r)

    clusters = []
    for ws, items in by_ws.items():
        if len(items) < 2:
            continue
        # Prepare features
        feats = []
        for r in items:
            cid = r["conversation_id"]
            title = (r["title"] or "").strip()
            t_toks = tokenize_title(title)
            p_toks = tokenize_title(first_user_prompt(cid, 160))
            dt = parse_dt(r["last_modified_time"])
            sz = session_disk_bytes(cid)
            feats.append({
                "cid": cid,
                "title": title,
                "steps": r["step_count"] or 0,
                "date": (r["last_modified_time"] or "")[:10],
                "dt": dt,
                "size_bytes": sz,
                "t_toks": t_toks,
                "all_toks": t_toks | p_toks,
            })

        # Union-Find clustering within the same workspace
        n = len(feats)
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for i in range(n):
            for j in range(i + 1, n):
                fi, fj = feats[i], feats[j]
                # 1. Exact title match
                if fi["title"] and fi["title"] == fj["title"]:
                    union(i, j)
                    continue
                # 2. Title token overlap
                ti, tj = fi["t_toks"], fj["t_toks"]
                t_inter = ti & tj
                t_min = min(len(ti), len(tj)) if (ti and tj) else 1
                t_sim = len(t_inter) / t_min if t_min else 0.0
                # 3. Combined title+prompt token Jaccard
                ai, aj = fi["all_toks"], fj["all_toks"]
                a_union = ai | aj
                a_jacc = (len(ai & aj) / len(a_union)) if a_union else 0.0
                # 4. Time proximity bonus (within 7 days)
                near_days = False
                if fi["dt"] and fj["dt"]:
                    near_days = abs((fi["dt"] - fj["dt"]).days) <= 7

                score = t_sim * 0.7 + a_jacc * 0.3 + (0.12 if near_days else 0.0)
                if score >= args.threshold and (len(t_inter) >= 2 or a_jacc >= 0.28):
                    union(i, j)

        groups = defaultdict(list)
        for idx in range(n):
            groups[find(idx)].append(feats[idx])

        for members in groups.values():
            if len(members) < 2:
                continue
            members.sort(key=lambda x: x["date"], reverse=True)
            total_sz = sum(m["size_bytes"] for m in members)
            total_steps = sum(m["steps"] for m in members)
            # Pick shared tokens as group theme hint
            tok_cnt = Counter()
            for m in members:
                for tok in m["t_toks"]:
                    tok_cnt[tok] += 1
            common = [k for k, v in tok_cnt.most_common(4) if v >= 2]
            clusters.append({
                "workspace": ws,
                "theme": " / ".join(common) if common else members[0]["title"],
                "count": len(members),
                "total_steps": total_steps,
                "total_mb": round(total_sz / (1024 * 1024), 1),
                "reclaimable_mb": round((total_sz - members[0]["size_bytes"]) / (1024 * 1024), 1),
                "members": [
                    {
                        "cid": m["cid"],
                        "title": m["title"],
                        "date": m["date"],
                        "steps": m["steps"],
                        "mb": round(m["size_bytes"] / (1024 * 1024), 1),
                    }
                    for m in members
                ],
            })

    clusters.sort(key=lambda g: (g["count"], g["total_mb"]), reverse=True)

    if args.json:
        print(json.dumps(clusters, ensure_ascii=False, indent=2))
        return

    total_redundant = sum(g["count"] - 1 for g in clusters)
    total_reclaim = sum(g["reclaimable_mb"] for g in clusters)
    print("=== 左侧会话智能聚类体检报告（只读） ===")
    print(f"发现疑似重复/续接碎片组: {len(clusters)} 组")
    print(f"可减少左侧冗余条目: {total_redundant} 条")
    print(f"预计可释放 K 盘缓存空间: 约 {total_reclaim:.1f} MB（冷备至 G 盘后）\n")

    for idx, g in enumerate(clusters[: args.limit], 1):
        ws_short = os.path.basename(g["workspace"].rstrip("/\\")) or g["workspace"]
        print(f"[组 {idx}] 板块: {ws_short} | 主题词: {g['theme']} | {g['count']} 条会话 | 共 {g['total_steps']} 步 | 总占 {g['total_mb']:.1f} MB")
        for m in g["members"]:
            print(f"    - {m['cid'][:8]} | {m['date']} | {m['steps']:4d} 步 | {m['mb']:5.1f} MB | {m['title']}")


def cmd_extract_group(args):
    cids = [c.strip() for c in args.cids.split(",") if c.strip()]
    if not cids:
        print("ERROR: Provide --cids")
        sys.exit(1)

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    meta = {}
    for cid in cids:
        row = conn.execute(
            "SELECT title, step_count, last_modified_time, workspace_uris FROM conversation_summaries WHERE conversation_id = ?",
            (cid,),
        ).fetchone()
        meta[cid] = row
    conn.close()

    # Sort chronologically by last_modified_time ascending
    cids.sort(key=lambda c: (meta[c][2] if meta[c] else ""))

    out_lines = [
        f"# 跨会话融合提取素材（共 {len(cids)} 条）",
        f"- 提取时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    for idx, cid in enumerate(cids, 1):
        row = meta[cid]
        title = row[0] if row else "(未命名)"
        steps = row[1] if row else 0
        lm = (row[2] or "")[:10] if row else ""
        out_lines.append(f"## [{idx}] {title} (`{cid}` | {lm} | {steps} 步)")
        tpath = os.path.join(BRAIN_DIR, cid, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.isfile(tpath):
            out_lines.append("- *(未找到 transcript.jsonl)*\n")
            continue

        user_msgs = []
        model_msgs = []
        checkpoints = []
        with open(tpath, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                stype = obj.get("type", "")
                c = (obj.get("content") or "").strip()
                if not c:
                    continue
                if stype == "USER_INPUT":
                    m = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", c, re.S)
                    if m:
                        c = m.group(1).strip()
                    if c and c != "/compact":
                        user_msgs.append(c[:400])
                elif stype == "PLANNER_RESPONSE":
                    model_msgs.append(c)
                elif stype == "CHECKPOINT":
                    checkpoints.append(c)

        if checkpoints:
            out_lines.append("### 已有压缩检查点（最新）")
            out_lines.append(checkpoints[-1][:2500])
        out_lines.append("### 用户核心诉求轨迹")
        sampled_u = user_msgs[:4] + (["..."] if len(user_msgs) > 8 else []) + (user_msgs[-4:] if len(user_msgs) > 4 else [])
        for u in sampled_u:
            out_lines.append(f"- {u.replace(chr(10), ' ')[:260]}")
        out_lines.append("### 最终阶段关键结论（最后 2 条模型回复）")
        for mtxt in model_msgs[-2:]:
            out_lines.append(mtxt[:1800])
            out_lines.append("")

    result = "\n".join(out_lines)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"EXTRACT_OK: {args.out} ({len(result)} chars)")
    else:
        print(result)


def cmd_merge_finalize(args):
    drop_cids = [c.strip() for c in args.drop_cids.split(",") if c.strip()]
    if not drop_cids:
        print("ERROR: Provide --drop-cids")
        sys.exit(1)

    if args.keep_cid and args.keep_cid in drop_cids:
        print("ERROR: --keep-cid cannot be in --drop-cids")
        sys.exit(1)

    total_reclaim = sum(session_disk_bytes(c) for c in drop_cids)
    if not args.confirm:
        print(f"[DRY-RUN] 计划移出左侧并归档 {len(drop_cids)} 条碎片会话（未加 --confirm，未做任何修改）：")
        if args.keep_cid:
            print(f"  保留主会话: {args.keep_cid}")
        for c in drop_cids:
            print(f"  - 移出: {c} ({session_disk_bytes(c)/(1024*1024):.1f} MB)")
        print(f"  若启用 --purge-brain，预计释放本地磁盘空间: {total_reclaim/(1024*1024):.1f} MB（默认写入前会先备份至 {BACKUP_ROOT}，可用 --no-backup 跳过）")
        return

    zpath = None
    if not getattr(args, "no_backup", False):
        zpath = create_zip_cold_backup("merge", drop_cids, include_brain=True)
        print(f"[BACKUP] Verified ZIP backup created at: {zpath} ({os.path.getsize(zpath)/(1024*1024):.1f} MB)")
    else:
        print("[BACKUP] Skipped (--no-backup specified).")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    removed_rows = 0
    for cid in drop_cids:
        cur.execute("DELETE FROM conversation_summaries WHERE conversation_id = ?", (cid,))
        removed_rows += cur.rowcount
        try:
            cur.execute("DELETE FROM conversations_fts WHERE conversation_id = ?", (cid,))
        except Exception:
            pass
        af = os.path.join(ANN_DIR, f"{cid}.pbtxt")
        if os.path.isfile(af):
            os.remove(af)
    conn.commit()
    conn.close()

    freed_bytes = 0
    if args.purge_brain:
        for cid in drop_cids:
            bpath = os.path.join(BRAIN_DIR, cid)
            if os.path.isdir(bpath):
                sz = dir_size_bytes(bpath)
                shutil.rmtree(bpath, ignore_errors=True)
                freed_bytes += sz
            for ext in (".db", ".db-wal", ".db-shm"):
                cf = os.path.join(CONV_DIR, f"{cid}{ext}")
                if os.path.isfile(cf):
                    try:
                        freed_bytes += os.path.getsize(cf)
                        os.remove(cf)
                    except OSError:
                        pass

    if args.keep_cid and args.new_title:
        subprocess.run(
            [sys.executable, SET_TITLE_SCRIPT, "--cid", args.keep_cid, "--title", args.new_title],
            check=False,
        )
        print(f"[RENAME] Keep session {args.keep_cid[:8]} -> {args.new_title}")

    print(
        f"MERGE_FINALIZE_OK: removed {removed_rows} sidebar entries, "
        f"freed {freed_bytes/(1024*1024):.1f} MB, backup={zpath or 'skipped'}"
    )


def cmd_rename(args):
    mapping = {}
    if args.map:
        with open(args.map, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    elif args.cid and args.title:
        mapping = {args.cid: args.title}
    else:
        print("ERROR: Provide --cid & --title, or --map <json_file>")
        sys.exit(1)

    if not getattr(args, "no_backup", False):
        bdir = create_cold_backup("rename", extra_cids=list(mapping.keys()))
        print(f"[BACKUP] Backup created at: {bdir}")

    ok_cnt = 0
    for cid, new_title in mapping.items():
        res = subprocess.run(
            [sys.executable, SET_TITLE_SCRIPT, "--cid", cid, "--title", new_title],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            ok_cnt += 1
            print(f"  [OK] {cid[:8]} -> {new_title}")
        else:
            print(f"  [FAIL] {cid[:8]} -> {res.stderr.strip() or res.stdout.strip()}")
    print(f"Rename finished: {ok_cnt}/{len(mapping)} succeeded.")


def cmd_export(args):
    cid = args.cid
    log_path = os.path.join(BRAIN_DIR, cid, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(log_path):
        print(f"ERROR: Transcript not found at {log_path}")
        sys.exit(1)

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    lines = [f"# 会话归档：{cid}\n", f"- 导出时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n"]
    turn = 0
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            stype = obj.get("type", "")
            content = (obj.get("content") or "").strip()
            if not content:
                continue
            if stype == "USER_INPUT":
                turn += 1
                lines.append(f"\n## 第 {turn} 轮 · 用户\n\n{content}\n")
            elif stype == "PLANNER_RESPONSE":
                lines.append(f"\n### 助手回复\n\n{content}\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"EXPORT_OK: {out_path} ({turn} turns)")


def cmd_clean(args):
    cids = [c.strip() for c in args.cids.split(",") if c.strip()]
    if not cids:
        print("ERROR: No conversation IDs specified.")
        sys.exit(1)

    if not args.confirm:
        print(f"[DRY-RUN] 将要清理 {len(cids)} 条会话（未加 --confirm，未执行任何修改）：")
        for c in cids:
            print(f"  - {c}")
        return

    bdir = None
    if not getattr(args, "no_backup", False):
        bdir = create_cold_backup("clean", extra_cids=cids)
        print(f"[BACKUP] Backup created at: {bdir}")
    else:
        print("[BACKUP] Skipped (--no-backup specified).")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    removed = 0
    for cid in cids:
        cur.execute("DELETE FROM conversation_summaries WHERE conversation_id = ?", (cid,))
        removed += cur.rowcount
        try:
            cur.execute("DELETE FROM conversations_fts WHERE conversation_id = ?", (cid,))
        except Exception:
            pass
        af = os.path.join(ANN_DIR, f"{cid}.pbtxt")
        if os.path.exists(af):
            os.remove(af)
    conn.commit()
    conn.close()
    print(f"CLEAN_OK: removed {removed} rows from index. Backup={bdir or 'skipped'}")


def main():
    p = argparse.ArgumentParser(description="Antigravity Left Sidebar Session Organizer v2.0")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("audit", help="Read-only audit of sidebar conversations")
    pa.add_argument("--short-steps", type=int, default=4, help="Threshold for short sessions")
    pa.add_argument("--limit", type=int, default=15, help="Max items shown per category")

    pcl = sub.add_parser("cluster", help="Read-only clustering of duplicate/continuation sessions")
    pcl.add_argument("--threshold", type=float, default=0.38, help="Similarity threshold (0-1)")
    pcl.add_argument("--limit", type=int, default=20, help="Max clusters to display")
    pcl.add_argument("--json", action="store_true", help="Output JSON")

    pex = sub.add_parser("extract-group", help="Extract concise timeline from a group of sessions for AI fusion")
    pex.add_argument("--cids", required=True, help="Comma-separated conversation IDs")
    pex.add_argument("--out", help="Optional output markdown file path")

    pmf = sub.add_parser("merge-finalize", help="Remove redundant sidebar entries, optionally backup and purge brain cache")
    pmf.add_argument("--drop-cids", required=True, help="Comma-separated redundant conversation IDs to remove")
    pmf.add_argument("--keep-cid", help="Optional primary conversation ID to keep")
    pmf.add_argument("--new-title", help="Optional new title for kept conversation")
    pmf.add_argument("--purge-brain", action="store_true", help="Also purge removed sessions' brain/ and conversations/ files to free disk space")
    pmf.add_argument("--no-backup", action="store_true", help="Skip ZIP backup before deleting (saves disk space)")
    pmf.add_argument("--confirm", action="store_true", help="Actually execute changes")

    pr = sub.add_parser("rename", help="Batch or single safe 3-layer rename")
    pr.add_argument("--cid", help="Single conversation ID")
    pr.add_argument("--title", help="New title")
    pr.add_argument("--map", help="JSON file mapping cid -> title")
    pr.add_argument("--no-backup", action="store_true", help="Skip index backup before renaming")

    pe = sub.add_parser("export", help="Export conversation transcript to Markdown")
    pe.add_argument("--cid", required=True, help="Conversation ID")
    pe.add_argument("--out", required=True, help="Output Markdown path")

    pc = sub.add_parser("clean", help="Clean confirmed conversation IDs (cold backup first)")
    pc.add_argument("--cids", required=True, help="Comma-separated conversation IDs")
    pc.add_argument("--no-backup", action="store_true", help="Skip index backup before cleaning")
    pc.add_argument("--confirm", action="store_true", help="Actually apply cleanup")

    args = p.parse_args()
    if args.cmd == "audit":
        cmd_audit(args)
    elif args.cmd == "cluster":
        cmd_cluster(args)
    elif args.cmd == "extract-group":
        cmd_extract_group(args)
    elif args.cmd == "merge-finalize":
        cmd_merge_finalize(args)
    elif args.cmd == "rename":
        cmd_rename(args)
    elif args.cmd == "export":
        cmd_export(args)
    elif args.cmd == "clean":
        cmd_clean(args)


if __name__ == "__main__":
    main()
