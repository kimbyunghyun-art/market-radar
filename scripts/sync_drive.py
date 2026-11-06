#!/usr/bin/env python3
"""Google Drive 공개 폴더에서 대시보드 데이터 JSON을 받아 data/ 폴더를 갱신한다.

동작:
 1. 폴더 안의 파일 목록을 읽는다 (DRIVE_API_KEY가 있으면 Drive API v3, 없으면 공개 폴더 HTML 뷰).
 2. market.json, macro.json, imf.json, vn_trailer.json, excavators.json 중 폴더에 있는 것만 내려받는다.
 3. 유효한 JSON인지, 기존 파일과 최상위 키 집합이 같은지, "updated"/"fetched" 날짜가 뒤로 가지 않는지 확인한다.
 4. 내용이 바뀐 파일만 data/ 에 쓰고, GitHub Actions 출력(changed, summary)을 남긴다.
안전장치에 걸린 파일은 건너뛰고 로그에 이유를 남긴다. 어떤 파일도 통과하지 못하면 커밋하지 않는다.
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "").strip()
API_KEY = os.environ.get("DRIVE_API_KEY", "").strip()
FILES = ["market.json", "macro.json", "imf.json", "vn_trailer.json", "excavators.json"]
DATE_KEYS = ("updated", "fetched")
UA = {"User-Agent": "market-radar-sync/1.0"}


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def list_via_api():
    q = urllib.parse.quote(f"'{FOLDER_ID}' in parents and trashed = false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           f"&fields=files(id,name,modifiedTime)&orderBy=modifiedTime%20desc&pageSize=100&key={API_KEY}")
    data = json.loads(http_get(url))
    return [(f["name"], f["id"], f.get("modifiedTime", "")) for f in data.get("files", [])]


def list_via_html():
    url = f"https://drive.google.com/embeddedfolderview?id={FOLDER_ID}"
    page = http_get(url).decode("utf-8", "replace")
    out = []
    # <div class="flip-entry" id="entry-<ID>"> ... <div class="flip-entry-title">name</div>
    for m in re.finditer(r'id="entry-([A-Za-z0-9_-]+)"(.*?)flip-entry-title">([^<]*)<', page, re.S):
        out.append((html.unescape(m.group(3)).strip(), m.group(1), ""))
    if not out:
        # 대체 형식: 링크 + 제목
        for m in re.finditer(r'/file/d/([A-Za-z0-9_-]+)[^>]*>.*?title="([^"]+)"', page, re.S):
            out.append((html.unescape(m.group(2)).strip(), m.group(1), ""))
    return out


def download(file_id):
    urls = [
        f"https://drive.google.com/uc?export=download&id={file_id}",
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t",
    ]
    last = None
    for u in urls:
        try:
            raw = http_get(u, timeout=120)
            txt = raw.decode("utf-8")
            if txt.lstrip().startswith("{"):
                return txt
            last = f"not JSON (starts with {txt[:40]!r})"
        except Exception as e:  # noqa: BLE001
            last = str(e)
    raise RuntimeError(f"download failed: {last}")


def main():
    if not FOLDER_ID:
        print("DRIVE_FOLDER_ID is empty", file=sys.stderr)
        return 1
    entries = []
    if API_KEY:
        try:
            entries = list_via_api()
            print(f"listed {len(entries)} files via Drive API")
        except Exception as e:  # noqa: BLE001
            print(f"Drive API listing failed ({e}); falling back to HTML view")
    if not entries:
        entries = list_via_html()
        print(f"listed {len(entries)} files via folder HTML view")
    if not entries:
        print("폴더에서 파일 목록을 읽지 못했습니다. (폴더가 비었거나 공개 링크 공유가 꺼졌거나 HTML 형식이 바뀜)")
        set_output("changed", "false")
        return 0

    changed, notes = [], []
    for name in FILES:
        cands = [e for e in entries if e[0] == name]
        if not cands:
            continue
        # API 경로는 modifiedTime desc 정렬이라 첫 항목이 최신; HTML 경로는 보통 1개뿐
        file_id = cands[0][1]
        try:
            txt = download(file_id)
            new = json.loads(txt)
        except Exception as e:  # noqa: BLE001
            notes.append(f"{name}: 건너뜀 — {e}")
            continue
        if not isinstance(new, dict):
            notes.append(f"{name}: 건너뜀 — 최상위가 객체가 아님")
            continue
        path = os.path.join("data", name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                old = json.load(f)
            if set(old.keys()) != set(new.keys()):
                missing = sorted(set(old) - set(new)); extra = sorted(set(new) - set(old))
                notes.append(f"{name}: 건너뜀 — 최상위 키 불일치 (빠짐 {missing}, 추가 {extra})")
                continue
            for k in DATE_KEYS:
                if k in old and k in new and str(new[k]) < str(old[k]):
                    notes.append(f"{name}: 건너뜀 — {k}가 기존({old[k]})보다 과거({new[k]})")
                    break
            else:
                pretty = json.dumps(new, ensure_ascii=False, indent=2) + "\n"
                with open(path, encoding="utf-8") as f:
                    if f.read() == pretty:
                        notes.append(f"{name}: 변경 없음")
                        continue
                with open(path, "w", encoding="utf-8") as f:
                    f.write(pretty)
                stamp = next((str(new[k]) for k in DATE_KEYS if k in new), "")
                changed.append(f"{name}{(' ' + stamp) if stamp else ''}")
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(new, ensure_ascii=False, indent=2) + "\n")
            changed.append(f"{name} (신규)")

    for n in notes:
        print(n)
    if changed:
        summary = ", ".join(changed)
        print("갱신:", summary)
        set_output("changed", "true")
        set_output("summary", summary)
    else:
        print("갱신할 파일 없음")
        set_output("changed", "false")
    return 0


def set_output(k, v):
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"{k}={v}\n")


if __name__ == "__main__":
    sys.exit(main())
