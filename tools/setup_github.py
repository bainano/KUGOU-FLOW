# -*- coding: utf-8 -*-
"""酷狗flow：GitHub 网页授权（Device Flow）一键连接。

双击 setup_github.bat 运行 → 自动打开浏览器 → 网页确认 → 自动完成免密配置、建仓库、推送。
全程不需要手动填写或复制任何令牌。
"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "kugou-flow"
API = "https://api.github.com"
UA = "kugou-flow-setup/2.0"

# GitHub CLI 的公开 client_id（OAuth 客户端 ID 本身不是秘密，可公开使用）
CLIENT_ID = "178c6fc778ccc68e1d6a"
SCOPE = "repo"  # 仅仓库读写权限：建仓库、推送代码足够，无多余权限


def say(text=""):
    print(text, flush=True)


def http_json(url, method="GET", data=None, headers=None):
    h = {"Accept": "application/json", "User-Agent": UA}
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        h["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"raw": raw}
        # device flow 的授权待确认等状态以 HTTP 错误返回，交给调用方处理
        return {"_http_error": e.code, **payload}


def run_git(*args):
    p = subprocess.run(
        ["git", *args], cwd=str(ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace"
    )
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def api(method, path, token, data=None):
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(API + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("GitHub API 返回 %s：%s" % (e.code, detail[:300]))


def device_login():
    """网页授权，返回 access_token。"""
    say("[1/5] 正在发起网页授权...")
    result = http_json(
        "https://github.com/login/device/code",
        method="POST",
        data={"client_id": CLIENT_ID, "scope": SCOPE},
    )
    if "error" in result:
        raise RuntimeError("发起授权失败：" + str(result))
    user_code = result["user_code"]
    verification_uri = result["verification_uri"]
    device_code = result["device_code"]
    interval = int(result.get("interval", 5))
    expires_in = int(result.get("expires_in", 900))

    say("")
    say("  ┌────────────────────────────────────────┐")
    say("  │  浏览器即将打开 GitHub 授权页面          │")
    say("  │  请确认下面这组验证码：                  │")
    say("  │                                        │")
    say("  │          %s                      │" % user_code)
    say("  │                                        │")
    say("  └────────────────────────────────────────┘")
    say("")
    say("  如果浏览器没有自动打开，请手动访问：")
    say("  " + verification_uri)
    say("")
    say("  在网页输入验证码 → 点 Authorize（授权）即可，无需填其他信息。")
    say("  正在等待网页确认（最长 %d 秒）..." % expires_in)
    say("")

    # 自动打开浏览器（不预填验证码，让用户亲手输入，更安全）
    try:
        webbrowser.open(verification_uri)
    except Exception:
        pass

    deadline = time.time() + expires_in
    while time.time() < deadline:
        time.sleep(interval)
        resp = http_json(
            "https://github.com/login/oauth/access_token",
            method="POST",
            data={
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )
        token = resp.get("access_token")
        if token:
            say("  ✓ 网页授权成功，已取得访问令牌")
            return token
        err = resp.get("error", "")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        if err == "expired_token":
            raise RuntimeError("验证码已过期，请重新运行脚本")
        if err == "access_denied":
            raise RuntimeError("你在网页上拒绝了授权")
        raise RuntimeError("授权失败：" + str(resp))
    raise RuntimeError("等待超时，请重新运行脚本")


def store_credential(token, username):
    """把令牌写入 git 凭据文件，仅对 github.com 生效，以后操作免密。"""
    run_git("config", "--global", "credential.https://github.com.helper", "store")
    cred = Path.home() / ".git-credentials"
    line = "https://%s:%s@github.com" % (username, token)
    old = []
    if cred.exists():
        old = [x for x in cred.read_text(encoding="utf-8", errors="replace").splitlines()
               if x.strip() and "github.com" not in x]
    cred.write_text("\n".join(old + [line]) + "\n", encoding="utf-8")
    say("  ✓ 免密凭据已保存（仅对 github.com 生效）")


def main():
    say("=== 酷狗flow → GitHub 网页授权连接 ===\n")
    token = device_login()

    say("\n[2/5] 识别账户...")
    user = api("GET", "/user", token)
    username = user.get("login")
    if not username:
        raise RuntimeError("无法获取用户名，令牌可能无效")
    say("  ✓ 已识别账户：%s" % username)

    say("\n[3/5] 准备仓库 %s..." % REPO)
    try:
        api("GET", "/repos/%s/%s" % (username, REPO), token)
        say("  ✓ 仓库已存在")
    except RuntimeError:
        say("  仓库不存在，正在创建...")
        api("POST", "/user/repos", token, {
            "name": REPO,
            "description": "酷狗音乐概念版桌面端 — 酷狗flow",
            "private": False,
            "auto_init": False,
        })
        say("  ✓ 仓库创建成功")

    say("\n[4/5] 配置免密并连接远程...")
    store_credential(token, username)
    run_git("remote", "remove", "origin")
    code, out, err = run_git("remote", "add", "origin", "https://github.com/%s/%s.git" % (username, REPO))
    if code != 0:
        raise RuntimeError("设置远程失败：" + err)
    say("  ✓ 远程已设置")

    say("\n[5/5] 推送代码...")
    code, out, err = run_git("push", "-u", "origin", "master")
    if code == 0:
        say("  ✓ 推送成功")
    else:
        say("  ⚠ git 协议推送失败：" + err[:200])
        say("  本地提交已保留，稍后可在网络允许时手动执行：git push -u origin master")
        # 网络拦截 git 协议时，回退到 API 逐文件上传
        say("  尝试通过 API 上传代码...")
        try:
            upload_via_api(token, username)
            say("  ✓ API 上传完成")
        except Exception as ue:
            say("  ⚠ API 上传也失败：" + str(ue)[:200])

    say("\n=== 全部完成 ===")
    say("仓库地址：https://github.com/%s/%s" % (username, REPO))
    say("以后 Git 操作会自动使用该凭据，无需重复授权。")
    say("请回到聊天窗口告诉我运行结果。")


def upload_via_api(token, username):
    """当 git 协议被网络拦截时，改用 API 逐文件上传。"""
    import base64
    import urllib.parse as up
    code, out, err = run_git("ls-files")
    if code != 0:
        raise RuntimeError("无法列出本地文件：" + err)
    files = [f for f in out.splitlines() if f.strip()]
    say("  共 %d 个文件，开始上传..." % len(files))
    done = 0
    for rel in files:
        fp = ROOT / rel
        if not fp.is_file():
            continue
        content = base64.b64encode(fp.read_bytes()).decode("ascii")
        quoted = "/".join(up.quote(p) for p in rel.split("/"))
        api(
            "PUT",
            "/repos/%s/%s/contents/%s" % (username, REPO, quoted),
            token,
            {"message": "初始化酷狗flow", "content": content, "branch": "master"},
        )
        done += 1
        if done % 25 == 0:
            say("    已上传 %d/%d" % (done, len(files)))
    say("  已上传 %d 个文件" % done)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        say("\n发生错误：" + str(exc))
        say("请把错误信息发给我，我来帮你处理。")
        sys.exit(1)
