#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import csv
import os
import json
from datetime import datetime, date
import threading
import sys
import tempfile
import shutil
from typing import Optional


DEFAULT_HOST = os.environ.get("ALLOWANCE_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("ALLOWANCE_PORT", "8000"))
ALLOWANCE_CSV = "allowance.csv"
GOALS_CSV = "goals.csv"
lock = threading.Lock()

def ensure_csv(path, header):
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(header)

def read_rows(path):
    ensure_csv(path, ["date","item","amount","balance"] if path==ALLOWANCE_CSV else ["goal","amount"])
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.reader(f))

def append_row(path, row):
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

def get_balance():
    rows = read_rows(ALLOWANCE_CSV)
    if len(rows) <= 1:
        return 0
    try:
        return int(rows[-1][3])
    except Exception:
        return 0

def add_record(item: str, amount: int, d: Optional[str] = None):
    if not d:
        d = date.today().isoformat()
    with lock:
        try:
            amount = int(amount)
        except Exception:
            raise ValueError("amount must be int")
        bal = get_balance() + amount
        append_row(ALLOWANCE_CSV, [d, item, str(amount), str(bal)])
    return {"date": d, "item": item, "amount": amount, "balance": bal}

def month_summary(yyyymm: str):
    rows = read_rows(ALLOWANCE_CSV)
    inc, exp = 0, 0
    for i, r in enumerate(rows):
        if i==0 or len(r)<4:
            continue
        d, _, amt, _ = r
        if d.startswith(yyyymm):
            try:
                v = int(amt)
                if v >= 0:
                    inc += v
                else:
                    exp += -v
            except Exception:
                pass
    return {"income": inc, "expense": exp, "net": inc - exp}

def ok_json(handler, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)

INDEX_HTML = """<!doctype html>
<html lang=ja>
<head>
  <meta charset=utf-8>
  <meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>お小遣い帳</title>
  <style>
    :root { --pad:14px; --gap:10px; --radius:14px; }
    body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, 'Noto Sans JP', sans-serif; background:#f7f7f8; color:#111; }
    .header { position:sticky; top:0; background:#fff; border-bottom:1px solid #ececec; padding:var(--pad); z-index:1; }
    .wrap { max-width:760px; margin:0 auto; padding:var(--pad); }
    .card { background:#fff; border-radius:var(--radius); box-shadow:0 1px 2px rgba(0,0,0,.05); padding:var(--pad); margin-bottom:var(--gap); }
    .row { display:flex; gap:var(--gap); } .row>* { flex:1; }
    input[type=text], input[type=number], input[type=date], input[type=month] { width:100%; font-size:16px; padding:12px; border:1px solid #ddd; border-radius:10px; box-sizing:border-box; }
    .btn { display:inline-block; width:100%; text-align:center; padding:12px; font-weight:700; border-radius:12px; border:none; background:#111; color:#fff; }
    .btn.sec { background:#eee; color:#111; }
    .tabs { display:flex; gap:8px; } .tab { flex:1; text-align:center; padding:10px; border-radius:999px; background:#eee; font-weight:700; cursor:pointer; } .tab.active { background:#111; color:#fff; }
    table { width:100%; border-collapse:collapse; } th,td { padding:10px; border-bottom:1px solid #eee; font-size:14px; }
    .pos { color:#0a7; font-weight:700; } .neg { color:#d33; font-weight:700; }
    .footer { text-align:center; color:#777; font-size:12px; padding:20px; }
  </style>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/htm@3.1.1/dist/htm.umd.js"></script>
</head>
<body>
  <div id=root></div>
  <script>
    const html = htm.bind(React.createElement);
    function fmtYen(n) {
      const v = Number(n||0);
      const s = v.toLocaleString('ja-JP');
      if (v>0) return html`<span class=pos>+${s}円</span>`;
      if (v<0) return html`<span class=neg>${s}円</span>`;
      return s + '円';
    }
    async function api(path, opts={}) {
      const res = await fetch(path, opts);
      if (!res.ok) throw new Error(await res.text());
      const ct = res.headers.get('content-type')||'';
      return ct.includes('application/json') ? res.json() : res.text();
    }
    function Tabs({tab, setTab}) {
      const T = (k, label) => html`<div class=${'tab '+(tab===k?'active':'')} onClick=${()=>setTab(k)}>${label}</div>`;
      return html`<div class=tabs>${T('add','入力')}${T('list','履歴')}${T('sum','集計')}${T('exp','エクスポート')}</div>`
    }
    function AddForm({onAdded, nowBalance}) {
      const [item, setItem] = React.useState('');
      const [amount, setAmount] = React.useState('');
      const [dateStr, setDateStr] = React.useState(new Date().toISOString().slice(0,10));
      const [err, setErr] = React.useState('');
      const submit = async (e)=>{
        e.preventDefault(); setErr('');
        if (!item.trim()) return setErr('内容は必須です');
        if (!/^[-+]?\\d+$/.test(amount)) return setErr('金額は整数（入金=正、出金=負）');
        const payload = { item, amount: parseInt(amount,10), date: dateStr };
        await api('/api/records', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
        setItem(''); setAmount(''); onAdded && onAdded();
      };
      return html`
        <div class=card>
          <div style="font-weight:800; margin-bottom:8px;">入出金の登録</div>
          <form onSubmit=${submit} style="display:flex; flex-direction:column; gap:10px;">
            <input type=text placeholder="内容（例: お小遣い / おやつ）" value=${item} onChange=${e= / />setItem(e.target.value)} required>
            <div class=row>
              <input type=number inputmode=numeric placeholder="金額（入=正 / 出=負）" value=${amount} onChange=${e= / />setAmount(e.target.value)} required>
              <input type=date value=${dateStr} onChange=${e= / />setDateStr(e.target.value)}>
            </div>
            <button class=btn type=submit>登録</button>
            ${err && html`<div style="color:#d33;">${err}</div>`}
          </form>
          <div style="margin-top:8px;">現在の残高: ${fmtYen(nowBalance)}</div>
        </div>`
    }
    function ListView({records}) {
      if (!records.length) return html`<div class=card>記録がありません</div>`;
      return html`<div class=card>
        <div style="font-weight:800; margin-bottom:8px;">履歴</div>
        <table>
          <tr><th>日付</th><th>内容</th><th style="text-align:right">金額</th><th style="text-align:right">残高</th></tr>
          ${records.map(r=>html`<tr>
            <td>${r.date}</td>
            <td>${r.item}</td>
            <td style="text-align:right">${fmtYen(r.amount)}</td>
            <td style="text-align:right">${fmtYen(r.balance)}</td>
          </tr>`)}
        </table>
      </div>`
    }
    function SummaryView() {
      const ym0 = new Date().toISOString().slice(0,7);
      const [ym, setYm] = React.useState(ym0);
      const [data, setData] = React.useState({income:0, expense:0, net:0});
      const load = async (m)=>{ setData(await api('/api/summary?month='+encodeURIComponent(m))); };
      React.useEffect(()=>{ load(ym); },[]);
      return html`<div class=card>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div style="font-weight:800;">月次集計</div>
          <div class=row style="max-width:260px;">
            <input type=month value=${ym} onChange=${e= / />setYm(e.target.value)}>
            <button class="btn sec" onClick=${()=>load(ym)} style="width:auto">表示</button>
          </div>
        </div>
        <div style="margin-top:10px;">
          <div>対象: <span style="padding:4px 8px; background:#eee; border-radius:999px;">${ym}</span></div>
          <div style="margin-top:8px;">収入: ${fmtYen(data.income)}</div>
          <div>支出: ${fmtYen(-data.expense)}</div>
          <div style="font-weight:800;">差額: ${fmtYen(data.net)}</div>
        </div>
      </div>`
    }
    function ExportView() {
      return html`<div class=card>
        <div style="font-weight:800; margin-bottom:8px;">エクスポート</div>
        <div class=row>
          <a class=btn sec href="/export?file=allowance" download>allowance.csv をダウンロード</a>
          <a class=btn sec href="/export?file=goals" download>goals.csv をダウンロード</a>
        </div>
      </div>`
    }
    function App(){
      const [tab, setTab] = React.useState('add');
      const [records, setRecords] = React.useState([]);
      const [balance, setBalance] = React.useState(0);
      const load = async ()=>{
        const data = await api('/api/records');
        setRecords(data.records); setBalance(data.balance);
      };
      React.useEffect(()=>{ load(); },[]);
      return html`
        <div class=header><div class=wrap>
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="font-weight:900; font-size:18px;">お小遣い帳</div>
            <div style="padding:4px 8px; background:#f0f0f0; border-radius:999px;">残高: ${fmtYen(balance)}</div>
          </div>
        </div></div>
        <div class=wrap>
          ${html`<${Tabs} tab=${tab} setTab=${setTab} />`}
          ${tab==='add' && html`<${AddForm} onAdded=${load} nowBalance=${balance} />`}
          ${tab==='list' && html`<${ListView} records=${records} />`}
          ${tab==='sum' && html`<${SummaryView} />`}
          ${tab==='exp' && html`<${ExportView} />`}
          <div class=footer>ローカル専用 / ${window.location.host} / CSV保存</div>
        </div>`
    }
    ReactDOM.createRoot(document.getElementById('root')).render(html`<${App} />`);
  </script>
</body>
</html>
"""

class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            p = urlparse(self.path)
            if p.path == "/":
                self._send(200, "text/html; charset=utf-8", INDEX_HTML.encode("utf-8"))
                return
            if p.path == "/api/records":
                rows = read_rows(ALLOWANCE_CSV)
                recs = []
                for i, r in enumerate(rows):
                    if i==0 or len(r)<4:
                        continue
                    d, item, amt, bal = r
                    try:
                        recs.append({"date": d, "item": item, "amount": int(amt), "balance": int(bal)})
                    except Exception:
                        pass
                recs.reverse()
                ok_json(self, {"records": recs, "balance": get_balance()})
                return
            if p.path == "/api/summary":
                q = parse_qs(p.query)
                month = (q.get("month") or [date.today().strftime("%Y-%m")])[0]
                if not valid_month(month):
                    month = date.today().strftime("%Y-%m")
                ok_json(self, month_summary(month))
                return
            if p.path == "/export":
                q = parse_qs(p.query)
                which = (q.get("file") or ["allowance"])[0]
                path = ALLOWANCE_CSV if which=="allowance" else GOALS_CSV
                ensure_csv(path, ["date","item","amount","balance"] if path==ALLOWANCE_CSV else ["goal","amount"])
                with open(path, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{which}.csv"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self._send(404, "text/plain; charset=utf-8", b"Not Found")
        except Exception as e:
            self._send(500, "text/plain; charset=utf-8", str(e).encode("utf-8"))

    def do_POST(self):
        try:
            p = urlparse(self.path)
            length = int(self.headers.get("Content-Length","0"))
            raw = self.rfile.read(length)
            if p.path == "/api/records":
                try:
                    body = json.loads(raw.decode("utf-8"))
                except Exception:
                    self._send(400, "text/plain; charset=utf-8", b"invalid json")
                    return
                item = (body.get("item") or "").strip()
                amount = body.get("amount")
                d = (body.get("date") or "").strip()
                if not item:
                    self._send(400, "text/plain; charset=utf-8", b"item required"); return
                if not is_int(amount):
                    self._send(400, "text/plain; charset=utf-8", b"amount must be int"); return
                if d and not valid_date(d):
                    self._send(400, "text/plain; charset=utf-8", b"invalid date"); return
                rec = add_record(item, int(amount), d or None)
                ok_json(self, rec)
                return
            self._send(404, "text/plain; charset=utf-8", b"Not Found")
        except Exception as e:
            self._send(500, "text/plain; charset=utf-8", str(e).encode("utf-8"))

    def _send(self, code:int, ctype:str, data:bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

def is_int(x):
    try:
        int(x)
        return True
    except Exception:
        return False

def valid_date(s:str):
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except Exception:
        return False

def valid_month(s:str):
    try:
        datetime.strptime(s, "%Y-%m")
        return True
    except Exception:
        return False

def run_self_tests():
    global ALLOWANCE_CSV, GOALS_CSV
    print("[SELFTEST] start")
    assert is_int(0) and is_int("10") and is_int(-5)
    assert not is_int("a")
    assert valid_date("2025-09-01") and not valid_date("2025-13-01")
    assert valid_month("2025-09") and not valid_month("2025-00")
    tmp = tempfile.mkdtemp(prefix="allowance_test_")
    old_allow = ALLOWANCE_CSV
    old_goals = GOALS_CSV
    try:
        ALLOWANCE_CSV = os.path.join(tmp, "allowance.csv")
        GOALS_CSV = os.path.join(tmp, "goals.csv")
        ensure_csv(ALLOWANCE_CSV, ["date","item","amount","balance"])
        ensure_csv(GOALS_CSV, ["goal","amount"])
        append_row(ALLOWANCE_CSV, ["2025-08-31", "test0", "200", "200"])
        append_row(ALLOWANCE_CSV, ["2025-09-10", "test1", "1000", "1200"])
        append_row(ALLOWANCE_CSV, ["2025-09-11", "test2", "-300", "900"])
        s_sep = month_summary("2025-09")
        assert s_sep["income"] == 1000
        assert s_sep["expense"] == 300
        assert s_sep["net"] == 700
        s_aug = month_summary("2025-08")
        assert s_aug["income"] == 200 and s_aug["expense"] == 0 and s_aug["net"] == 200
        rec1 = add_record("bonus", 500, "2025-09-12")
        assert rec1["balance"] == 1400
        rec2 = add_record("snack", -200, "2025-09-13")
        assert rec2["balance"] == 1200
        s_sep2 = month_summary("2025-09")
        assert s_sep2["income"] == 1500
        assert s_sep2["expense"] == 500
        assert s_sep2["net"] == 1000
        s_empty = month_summary("2025-07")
        assert s_empty == {"income":0, "expense":0, "net":0}
        before = month_summary("2025-09")
        append_row(ALLOWANCE_CSV, ["2025-09-14", "bad", "abc", "1000"])
        after = month_summary("2025-09")
        assert before == after
        print("[SELFTEST] OK")
    finally:
        shutil.rmtree(tmp)
        ALLOWANCE_CSV = old_allow
        GOALS_CSV = old_goals

def try_bind_server(host: str, port: int):
    return HTTPServer((host, port), AppHandler)

def start_server_with_fallback():
    hosts = [DEFAULT_HOST]
    for h in ["127.0.0.1", "0.0.0.0", "::1"]:
        if h not in hosts:
            hosts.append(h)
    port_candidates = [DEFAULT_PORT, 8000, 8080, 3000, 5173, 5500, 9000, 0]
    seen = set(); ports = []
    for p in port_candidates:
        if p not in seen:
            seen.add(p); ports.append(p)
    last_err = None
    for h in hosts:
        for p in ports:
            try:
                srv = try_bind_server(h, p)
                actual_host, actual_port = srv.server_address
                display_host = "127.0.0.1" if actual_host in ("0.0.0.0", "::") else actual_host
                print(f"Serving on http://{display_host}:{actual_port} (bound {actual_host}:{actual_port})")
                return srv
            except Exception as e:
                last_err = e
                continue
    print("[WARN] HTTP server could not bind to any host/port in this environment.")
    print("       Try on Android/Termux or set ALLOWANCE_HOST/ALLOWANCE_PORT.\n       You can still run self tests: python allowance_react.py --selftest")
    if last_err:
        print(f"[DETAIL] last error: {last_err}")
    return None

def main():
    if "--selftest" in sys.argv:
        run_self_tests()
        return
    ensure_csv(ALLOWANCE_CSV, ["date","item","amount","balance"])
    ensure_csv(GOALS_CSV, ["goal","amount"])
    srv = start_server_with_fallback()
    if srv is None:
        return
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")

if __name__ == '__main__':
    main()
