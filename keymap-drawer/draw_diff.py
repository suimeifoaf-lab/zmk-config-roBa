import json, math, sys, yaml
from PIL import Image, ImageDraw, ImageFont

S = sys.argv[1]; repo = sys.argv[2]; out = sys.argv[3]
layout = json.load(open(f"{repo}/config/roBa.json"))["layouts"]["default_layout"]["layout"]
old = yaml.safe_load(open(f"{S}/v3.yaml"))["layers"]
new = yaml.safe_load(open(f"{S}/v5.yaml"))["layers"]
OLDMAP = {"default":"Mac","SYMBOL":"Sym","NUM":"Num","ARROW":"Arrow","4":"Mouse","5":"Scroll","CONFIG":"Config"}
# 旧yaml内のレイヤー参照名を新名称に揃える（&mo 5 → Scroll など）
def norm(k):
    if isinstance(k, dict):
        d = dict(k)
        if d.get("t") != "BT":
            for f in ("t","h"):
                if f in d and isinstance(d[f], str) and d[f] in OLDMAP: d[f] = OLDMAP[d[f]]
        return d
    if isinstance(k, str) and k in OLDMAP: return k
    return k
old = {OLDMAP[n]: [norm(k) for k in L] for n, L in old.items()}

F = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
def font(sz): return ImageFont.truetype(F, sz)
U = 96; KW = U - 10
PAD = 30; TITLE_H = 54
LW = int(13.6 * U) + 2 * PAD; LH = int(5.1 * U) + TITLE_H
ORDER = ["Mac","Sym","Num","Arrow","Win","Mouse","Scroll","Config","WinArrow","WinScroll"]
DESC = {"Mac":"0 ベース（Mac）","Sym":"1 Sym（Space ホールド）","Num":"2 Num（かな ホールド）","Arrow":"3 Arrow（Enter ホールド）変更なし",
        "Win":"4 Win【新設】Config の W でトグル","Mouse":"5 Mouse（ボールで自動）","Scroll":"6 Scroll（Mouse で ; ホールド）",
        "Config":"7 Config（Scroll の右端キーでトグル）","WinArrow":"8 WinArrow【新設】Win＋Arrow で自動","WinScroll":"9 WinScroll【新設】Win＋Scroll で自動"}
COLS = 2; ROWS = math.ceil(len(ORDER)/COLS)
HEAD = 120
img = Image.new("RGB", (LW*COLS + PAD, HEAD + LH*ROWS + PAD), "white")
d = ImageDraw.Draw(img)

C_SAME = ("#F3F4F6", "#C9CDD3"); C_CHG = ("#FFF1A8", "#D9A400"); C_NEW = ("#D6F5D6", "#3C9A3C"); C_TR = ("#FAFAFA", "#DDDDDD")
def is_trans(k): return isinstance(k, dict) and k.get("type") == "trans" or k == "" or k is None
def is_held(k): return isinstance(k, dict) and k.get("type") == "held"
C_HELD = ("#FBE3E3", "#D98A8A")
def parts(k):
    if is_trans(k): return ("▽", None)
    if isinstance(k, dict): return (str(k.get("t","")), k.get("h"))
    return (str(k), None)
def wrap(s, n=8):
    if len(s) <= n: return [s]
    if "+" in s:
        segs = s.split("+"); lines=[]; cur=""
        for sg in segs:
            cand = (cur + "+" if cur else "") + sg
            if len(cand) > n and cur: lines.append(cur + "+"); cur = sg
            else: cur = cand
        lines.append(cur); return lines
    return [s]
def text_c(x, y, s, fnt, fill):
    w = d.textlength(s, font=fnt); d.text((x - w/2, y), s, font=fnt, fill=fill)

def key_pos(k):
    cx, cy = k["x"] + 0.5, k["y"] + 0.5
    if "r" in k:
        a = math.radians(k["r"]); rx, ry = k["rx"], k["ry"]
        dx, dy = cx - rx, cy - ry
        cx = rx + dx*math.cos(a) - dy*math.sin(a); cy = ry + dx*math.sin(a) + dy*math.cos(a)
    return cx, cy

# 見出し・凡例
d.text((PAD, 22), "roBa キーマップ 変更点   V3（現行・既定ブランチ） → v5-layout", font=font(34), fill="black")
lx = PAD; ly = 76
for col, lab in ((C_CHG,"変更あり（下段の赤字が旧）"),(C_NEW,"新設レイヤーの有効キー"),(C_SAME,"変更なし"),(C_TR,"透過（下の層が効く）"),(C_HELD,"この層を出すために押さえているキー")):
    d.rectangle((lx, ly, lx+26, ly+26), fill=col[0], outline=col[1], width=2)
    d.text((lx+34, ly+2), lab, font=font(20), fill="#333"); lx += 34 + d.textlength(lab, font=font(20)) + 40

changed_total = 0
for i, name in enumerate(ORDER):
    ox = PAD + (i % COLS) * LW; oy = HEAD + (i // COLS) * LH
    newL = new[name]; oldL = old.get(name)
    n_chg = 0
    for idx, k in enumerate(layout):
        cx, cy = key_pos(k)
        x0 = ox + PAD + (cx-0.5)*U; y0 = oy + TITLE_H + (cy-0.5)*U
        nk = newL[idx]; ok = oldL[idx] if oldL else None
        if is_held(nk):
            col = C_HELD; chg = False
        elif oldL is None:
            col = C_TR if is_trans(nk) else C_NEW; chg = False
        else:
            chg = (nk != ok); col = C_CHG if chg else (C_TR if is_trans(nk) else C_SAME)
        if chg: n_chg += 1
        d.rounded_rectangle((x0, y0, x0+KW, y0+KW), radius=8, fill=col[0], outline=col[1], width=2)
        t, h = parts(nk)
        if is_held(nk): t, h = "(押下中)", None
        lines = wrap(t); ml = max(len(l) for l in lines); fs = 20 if ml <= 6 else (15 if ml <= 8 else (12 if ml <= 11 else 10))
        top = y0 + 8 if (h or chg) else y0 + (KW - fs*len(lines)*1.1)/2
        for j, l in enumerate(lines): text_c(x0+KW/2, top + j*fs*1.1, l, font(fs), "#999" if t=="▽" else "black")
        if h: text_c(x0+KW/2, y0 + KW - 36 - (16 if chg else 0), h, font(13), "#444")
        if chg:
            ot, oh = parts(ok); os_ = ot + (f"/{oh}" if oh else "")
            text_c(x0+KW/2, y0 + KW - 20, ("旧 " + os_)[:14], font(12), "#C62828")
    changed_total += n_chg
    tag = "" if oldL is None else f"   変更 {n_chg} キー"
    d.text((ox + PAD, oy + 10), DESC[name] + tag, font=font(26), fill="black")
img.save(out)
print("changed keys total:", changed_total, "size:", img.size)
