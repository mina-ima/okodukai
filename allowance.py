#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import csv
import os
import json
from datetime import datetime, date, timedelta
import threading
import sys
import tempfile
import shutil
from typing import Optional
import cgi
import re

DEFAULT_HOST = os.environ.get("ALLOWANCE_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("ALLOWANCE_PORT", "8000"))

ALLOWANCE_CSV = "allowance.csv"
GOALS_CSV = "goals.csv"
PRESETS_CSV = "presets.csv"

lock = threading.Lock()

def ensure_csv(path, header):
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(header)

def read_rows(path):
    if path == ALLOWANCE_CSV:
        ensure_csv(path, ["date","item","amount","balance"])
    elif path == GOALS_CSV:
        ensure_csv(path, ["goal","amount"])
    elif path == PRESETS_CSV:
        ensure_csv(path, ["label","amount"])
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.reader(f))

def append_row(path, row):
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

def write_rows(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)

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
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
  <title>お小遣い帳</title>
  <style>
    :root { --pad:14px; --gap:10px; --radius:14px; }
    @media (prefers-color-scheme: dark) {
      :root { --bg:#111; --fg:#eee; --card:#1b1b1b; --line:#2a2a2a; --muted:#bbb; }
    }
    @media (prefers-color-scheme: light) {
      :root { --bg:#f7f7f8; --fg:#111; --card:#fff; --line:#ececec; --muted:#777; }
    }
    *{box-sizing:border-box}
    body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, 'Noto Sans JP', sans-serif; background:var(--bg); color:var(--fg); }
    a { color:inherit; text-decoration:none; }
    .header { position:sticky; top:0; background:var(--card); border-bottom:1px solid var(--line); padding:var(--pad); z-index:1; }
    .wrap { max-width:760px; margin:0 auto; padding:var(--pad); }
    .card { background:var(--card); border-radius:var(--radius); box-shadow:0 1px 2px rgba(0,0,0,.05); padding:var(--pad); margin-bottom:var(--gap); border:1px solid var(--line);}
    .row { display:flex; gap:var(--gap); } .row>* { flex:1; }
    input[type=text], input[type=number], input[type=date], input[type=month] { width:100%; font-size:16px; padding:12px; border:1px solid var(--line); background:transparent; color:var(--fg); border-radius:10px; }
    .btn { display:inline-flex; align-items:center; justify-content:center; gap:8px; width:100%; text-align:center; padding:12px; font-weight:700; border-radius:12px; border:1px solid var(--line); background:var(--card); color:var(--fg); cursor:pointer; }
    .btn.primary { background:#0b6; color:#fff; border:none; }
    .btn.warn { background:#d33; color:#fff; border:none; }
    .grid { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:10px; }
    .pill { padding:6px 10px; background:#eee3; border:1px solid var(--line); border-radius:999px; font-size:12px; }
    table { width:100%; border-collapse:collapse; } th,td { padding:10px; border-bottom:1px solid var(--line); font-size:14px; }
    .pos { color:#0a7; font-weight:700; } .neg { color:#f66; font-weight:700; }
    .muted { color:var(--muted); }
    .footer { text-align:center; color:var(--muted); font-size:12px; padding:20px; }
    .links { display:flex; gap:8px; flex-wrap:wrap; }
    .scroll { max-height:300px; overflow:auto; }
    .goalbar{ height:10px; background:#0002; border-radius:999px; overflow:hidden;}
    .goalbar>div{ height:10px; background:#0b6; }
  </style>
  <!-- React 17 固定 -->
  <script crossorigin src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/htm@3.1.1/dist/htm.umd.js"></script>
</head>
<body>
  <div id="root"></div>
  <script>
    const html = htm.bind(React.createElement);
    const Frag = React.Fragment;

    function fmtYen(n) {
      const v = Number(n||0);
      const s = v.toLocaleString('ja-JP');
      if (v>0) return html`<span className="pos">+${s}円</span>`;
      if (v<0) return html`<span className="neg">${s}円</span>`;
      return s + '円';
    }

    async function api(path, opts={}) {
      const res = await fetch(path, opts);
      if (!res.ok) throw new Error(await res.text());
      const ct = res.headers.get('content-type')||'';
      return ct.includes('application/json') ? res.json() : res.text();
    }

    function NavLinks({to}) {
      const Button = (k,label)=>html`<button className="btn" onClick=${()=>to(k)}>${label}</button>`;
      return html`<div className="links">
        ${Button('home','ホーム')}
        ${Button('withdraw','出金登録')}
        ${Button('goal','目標登録')}
        ${Button('admin','管理者')}
        ${Button('history','履歴')}
      </div>`;
    }

    function Home({go}) {
      const [data, setData] = React.useState({balance:0, last7:[], goals:[], presets:[]});
      const load = async()=> setData(await api('/api/home'));
      React.useEffect(()=>{ load(); },[]);
      return html`<${Frag}>
        <div className="card">
          <div style=${{display:'flex', alignItems:'baseline', gap:'10px'}}>
            <div style=${{fontWeight:900, fontSize:18}}>お小遣い帳</div>
            <span className="pill">ホーム</span>
          </div>
          <div style=${{marginTop:8}}>現在の残高: <b>${fmtYen(data.balance)}</b></div>
          <div style=${{marginTop:12}}>
            <div className="muted" style=${{marginBottom:6}}>お手伝い（プリセット）</div>
            <div className="grid">
              ${data.presets.length ? data.presets.map(p=>html`
                <button className="btn" onClick=${async()=>{
                  await api('/api/records',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({item:p.label, amount: parseInt(p.amount,10)})});
                  await load();
                }}>${p.label}（${p.amount}）</button>
              `) : html`<div className="muted">プリセット未登録です。管理者から追加できます。</div>`}
            </div>
          </div>
        </div>

        <div className="card">
          <div style=${{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
            <div style=${{fontWeight:800}}>過去7日間の履歴</div>
            <a href="#" className="pill" onClick=${e=>{e.preventDefault(); go('history');}}>すべて見る</a>
          </div>
          ${data.last7.length ? html`
            <div className="scroll">
              <table>
                <tr>
                  <th>日付</th>
                  <th>内容</th>
                  <th style=${{textAlign:'right'}}>金額</th>
                  <th style=${{textAlign:'right'}}>残高</th>
                </tr>
                ${data.last7.map(r=>html`<tr>
                  <td>${r.date}</td><td>${r.item}</td>
                  <td style=${{textAlign:'right'}}>${fmtYen(r.amount)}</td>
                  <td style=${{textAlign:'right'}}>${fmtYen(r.balance)}</td>
                </tr>`)}
              </table>
            </div>` : html`<div className="muted">直近7日間の記録はありません</div>`}
        </div>

        <div className="card">
          <div style=${{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
            <div style=${{fontWeight:800}}>目標</div>
            <a href="#" className="pill" onClick=${e=>{e.preventDefault(); go('goal');}}>目標登録へ</a>
          </div>
          ${data.goals.length ? data.goals.map(g=>html`<div style=${{margin:'10px 0'}}>
            <div style=${{display:'flex', justifyContent:'space-between'}}>
              <div>${g.goal}</div>
              <div>${fmtYen(g.amount)}（残り ${fmtYen(g.remaining)}）</div>
            </div>
            <div className="goalbar"><div style=${{width: (100*Math.min(1, (data.balance / Math.max(1, g.amount)))).toFixed(0)+'%'}}></div></div>
          </div>`) : html`<div className="muted">目標は未登録です</div>`}
        </div>

        <${NavLinks} to=${go} />
        <div className="footer">ローカル専用 / ${window.location.host} / CSV保存</div>
      </${Frag}>`;
    }

    function Withdraw({go}) {
      const [item, setItem] = React.useState('');
      const [amount, setAmount] = React.useState('');
      const [dateStr, setDateStr] = React.useState(new Date().toISOString().slice(0,10));
      const [err, setErr] = React.useState('');
      const submit = async (e)=>{
        e.preventDefault(); setErr('');
        if (!item.trim()) return setErr('内容は必須です');
        if (!/^[-+]?\d+$/.test(amount)) return setErr('金額は整数');
        const payload = { item, amount: -Math.abs(parseInt(amount,10)), date: dateStr };
        await api('/api/records', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
        setItem(''); setAmount('');
        alert('登録しました');
      };
      return html`<${Frag}>
        <div className="card">
          <div style=${{display:'flex', alignItems:'baseline', gap:'10px'}}><div style=${{fontWeight:900, fontSize:18}}>出金登録</div><span className="pill">支出</span></div>
          <form onSubmit=${submit} style=${{display:'flex', flexDirection:'column', gap:'10px', marginTop:8}}>
            <input type="text" placeholder="内容（例: おやつ）" value=${item} onChange=${e=>setItem(e.target.value)} required />
            <div className="row">
              <input type="number" inputmode="numeric" placeholder="金額（整数）" value=${amount} onChange=${e=>setAmount(e.target.value)} required />
              <input type="date" value=${dateStr} onChange=${e=>setDateStr(e.target.value)} />
            </div>
            ${err && html`<div className="neg">${err}</div>`}
            <button className="btn primary" type="submit">登録</button>
          </form>
        </div>
        <${NavLinks} to=${go} />
      </${Frag}>`;
    }

    function Goal({go}) {
      const [goals,setGoals] = React.useState([]);
      const [name,setName] = React.useState('');
      const [amt,setAmt] = React.useState('');
      const load = async()=> setGoals(await api('/api/goals'));
      React.useEffect(()=>{ load(); },[]);
      const add = async (e)=>{ e.preventDefault();
        if(!name.trim() || !/^[-+]?\d+$/.test(amt)) return;
        await api('/api/goals',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({goal:name, amount: parseInt(amt,10)})});
        setName(''); setAmt(''); await load();
      };
      const del = async (g)=>{ if(!confirm('削除しますか？')) return;
        await api('/api/goals?goal='+encodeURIComponent(g), {method:'DELETE'}); await load();
      };
      return html`<${Frag}>
        <div className="card">
          <div style=${{fontWeight:900, fontSize:18}}>目標登録</div>
          <form onSubmit=${add} className="row" style=${{marginTop:10}}>
            <input type="text" placeholder="目標名" value=${name} onChange=${e=>setName(e.target.value)} required />
            <input type="number" inputmode="numeric" placeholder="金額" value=${amt} onChange=${e=>setAmt(e.target.value)} required />
            <button className="btn primary" type="submit">追加</button>
          </form>
        </div>
        <div className="card">
          <div style=${{fontWeight:800}}>登録済み</div>
          ${goals.length ? html`<table>
            <tr>
              <th>目標</th>
              <th style=${{textAlign:'right'}}>金額</th>
              <th style=${{width:'1%'}}></th>
            </tr>
            ${goals.map(g=>html`<tr>
              <td>${g.goal}</td><td style=${{textAlign:'right'}}>${fmtYen(g.amount)}</td>
              <td><button className="btn warn" onClick=${()=>del(g.goal)}>削除</button></td>
            </tr>`)}
          </table>` : html`<div className="muted">なし</div>`}
        </div>
        <${NavLinks} to=${go} />
      </${Frag}>`;
    }

    function Admin({go}) {
      const [presets,setPresets] = React.useState([]);
      const [label,setLabel] = React.useState('');
      const [amount,setAmount] = React.useState('');
      const load = async()=> setPresets(await api('/api/presets'));
      React.useEffect(()=>{ load(); },[]);
      const add = async (e)=>{ e.preventDefault();
        if(!label.trim() || !/^[-+]?\d+$/.test(amount)) return;
        await api('/api/presets',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({label, amount: parseInt(amount,10)})});
        setLabel(''); setAmount(''); await load();
      };
      const del = async (lab)=>{ if(!confirm('削除しますか？')) return;
        await api('/api/presets?label='+encodeURIComponent(lab), {method:'DELETE'}); await load();
      };
      const ImportForm = ({name, label}) => html`
        <form method="POST" action="/import" encType="multipart/form-data" className="row">
          <input type="hidden" name="file" value=${name} />
          <input type="file" name="csvfile" accept=".csv" required />
          <button type="submit" className="btn">${label}をインポート</button>
        </form>
      `;
      return html`<${Frag}>\
        <div className="card">\
          <div style=${{fontWeight:900, fontSize:18}}>管理者</div>\
          <div style=${{marginTop:12}}>\
            <div className="muted" style=${{marginBottom:6}}>データ入出力</div>\
            <div className="grid">\
              <a className="btn" href="/export?file=presets" download>プリセット出力</a>\
              <a className="btn" href="/export?file=goals" download>目標リスト出力</a>\
              <a className="btn" href="/export?file=allowance" download>入出金履歴出力</a>\
            </div>\
            <div style=${{display:'flex', flexDirection:'column', gap:10, marginTop:10}}>\
              <${ImportForm} name="presets" label="プリセット" />\
              <${ImportForm} name="goals" label="目標リスト" />\
              <${ImportForm} name="allowance" label="入出金履歴" />\
            </div>\
          </div>\
        </div>\
\
        <div className="card">\
          <div style=${{fontWeight:800}}>お手伝いプリセット編集</div>\
          <form onSubmit=${add} className="row" style=${{marginTop:10}}>\
            <input type="text" placeholder="ラベル（例: 皿洗い）" value=${label} onChange=${e=>setLabel(e.target.value)} required />\
            <input type="number" inputmode="numeric" placeholder="金額（例: 100）" value=${amount} onChange=${e=>setAmount(e.target.value)} required />\
            <button className="btn primary" type="submit">追加</button>\
          </form>\
          <div style=${{fontWeight:800, marginTop:12}}>登録済みプリセット</div>\
          ${presets.length ? html`<table>\
            <tr>\
              <th>ラベル</th>\
              <th style=${{textAlign:'right'}}>金額</th>\
              <th style=${{width:'1%'}}></th>\
            </tr>\
            ${presets.map(p=>html`<tr>\
              <td>${p.label}</td><td style=${{textAlign:'right'}}>${fmtYen(p.amount)}</td>\
              <td><button className="btn warn" onClick=${()=>del(p.label)}>削除</button></td>\
            </tr>`)}\
          </table>` : html`<div className="muted">未登録</div>`}\
        </div>\
        <${NavLinks} to=${go} />\
      </${Frag}>`;
    }

    function History({go}) {
      const [records, setRecords] = React.useState([]);
      const load = async ()=>{ const d= await api('/api/records'); setRecords(d.records); };
      React.useEffect(()=>{ load(); },[]);
      return html`<${Frag}>
        <div className="card">
          <div style=${{fontWeight:900, fontSize:18}}>履歴</div>
          ${records.length ? html`<div className="scroll">
            <table>
              <tr>
                <th>日付</th>
                <th>内容</th>
                <th style=${{textAlign:'right'}}>金額</th>
                <th style=${{textAlign:'right'}}>残高</th>
              </tr>
              ${records.map(r=>html`<tr>
                <td>${r.date}</td><td>${r.item}</td>
                <td style=${{textAlign:'right'}}>${fmtYen(r.amount)}</td>
                <td style=${{textAlign:'right'}}>${fmtYen(r.balance)}</td>
              </tr>`)}
            </table></div>` : html`<div className="muted">なし</div>`}
        </div>
        <${NavLinks} to=${go} />
      </${Frag}>`;
    }

    function App(){
      const [page, setPage] = React.useState('home');
      const go = (p)=> setPage(p);
      const content = page==='home' ? html`<${Home} go=${go} />`
        : page==='withdraw' ? html`<${Withdraw} go=${go} />`
        : page==='goal' ? html`<${Goal} go=${go} />`
        : page==='admin' ? html`<${Admin} go=${go} />`
        : page==='history' ? html`<${History} go=${go} />`
        : html`<div className="card">Not Found</div>`;
      return html`<${Frag}>
        <div className="header"><div className="wrap">
          <div style=${{display:'flex', alignItems:'center', gap:'12px'}}>
            <div style=${{fontWeight:900, fontSize:18}}>お小遣い帳</div>
          </div>
        </div></div>
        <div className="wrap">${content}</div>
      </${Frag}>`;
    }
    ReactDOM.render(html`<${App} />`, document.getElementById('root'));
  </script>
</body>
</html>
"""

def is_int(x):
    try: int(x); return True
    except Exception: return False

def valid_date(s:str):
    try: datetime.strptime(s, "%Y-%m-%d"); return True
    except Exception: return False

def valid_month(s:str):
    try: datetime.strptime(s, "%Y-%m"); return True
    except Exception: return False

def list_goals():
    rows = read_rows(GOALS_CSV); out = []
    for i, r in enumerate(rows):
        if i==0 or len(r)<2: continue
        goal, amt = r
        try: out.append({"goal": goal, "amount": int(amt)})
        except Exception: pass
    return out

def list_presets():
    rows = read_rows(PRESETS_CSV); out = []
    for i, r in enumerate(rows):
        if i==0 or len(r)<2: continue
        label, amt = r
        try: out.append({"label": label, "amount": int(amt)})
        except Exception: pass
    return out

def last_n_days_records(n:int):
    rows = read_rows(ALLOWANCE_CSV)
    edge = date.today() - timedelta(days=n-1)
    out = []
    for i, r in enumerate(rows):
        if i==0 or len(r)<4: continue
        d, item, amt, bal = r
        try:
            dt = datetime.strptime(d,"%Y-%m-%d").date()
        except Exception:
            continue
        if dt >= edge:
            try:
                out.append({"date": d, "item": item, "amount": int(amt), "balance": int(bal)})
            except Exception:
                pass
    return out[::-1]

class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            p = urlparse(self.path)
            if p.path == "/":
                self._send(200, "text/html; charset=utf-8", INDEX_HTML.encode("utf-8")); return
            if p.path == "/api/records":
                rows = read_rows(ALLOWANCE_CSV); recs = []
                for i, r in enumerate(rows):
                    if i==0 or len(r)<4: continue
                    d, item, amt, bal = r
                    try: recs.append({"date": d, "item": item, "amount": int(amt), "balance": int(bal)})
                    except Exception: pass
                recs.reverse()
                ok_json(self, {"records": recs, "balance": get_balance()}); return
            if p.path == "/api/summary":
                q = parse_qs(p.query)
                month = (q.get("month") or [date.today().strftime("%Y-%m")])[0]
                if not valid_month(month):
                    month = date.today().strftime("%Y-%m")
                ok_json(self, month_summary(month)); return
            if p.path == "/api/home":
                bal = get_balance()
                goals_raw = list_goals()
                goals = [{"goal": g["goal"], "amount": g["amount"], "remaining": max(0, g["amount"]-bal)} for g in goals_raw]
                presets = list_presets()
                ok_json(self, {"balance": bal, "last7": last_n_days_records(7), "goals": goals, "presets": presets}); return
            if p.path == "/api/goals":
                ok_json(self, list_goals()); return
            if p.path == "/api/presets":
                ok_json(self, list_presets()); return
            if p.path == "/export":
                q = parse_qs(p.query)
                which = (q.get("file") or ["allowance"])[0]
                path = ALLOWANCE_CSV if which=="allowance" else (GOALS_CSV if which=="goals" else PRESETS_CSV)
                ensure_csv(path, ["date","item","amount","balance"] if path==ALLOWANCE_CSV else (["goal","amount"] if path==GOALS_CSV else ["label","amount"]))
                with open(path, "rb") as f: data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{which}.csv"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers(); self.wfile.write(data); return
            self._send(404, "text/plain; charset=utf-8", b"Not Found")
        except Exception as e:
            self._send(500, "text/plain; charset=utf-8", str(e).encode("utf-8"))

    def do_POST(self):
        try:
            p = urlparse(self.path)
            length = int(self.headers.get("Content-Length","0"))
            if p.path == "/import":
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST',
                             'CONTENT_TYPE': self.headers['Content-Type']}
                )
                file_type = form.getvalue('file')
                csv_file_item = form['csvfile']

                if not file_type or not csv_file_item.file:
                    self._send(400, b'bad request'); return

                path = ALLOWANCE_CSV if file_type == "allowance" else (GOALS_CSV if file_type == "goals" else PRESETS_CSV)
                
                # Overwrite the file with new content
                with open(path, "wb") as f:
                    f.write(csv_file_item.file.read())

                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
                return

            if p.path == "/api/records":
                raw = self.rfile.read(length)
                try: body = json.loads(raw.decode("utf-8"))
                except Exception:
                    self._send(400, "text/plain; charset=utf-8", b"invalid json"); return
                item = (body.get("item") or "").strip()
                amount = body.get("amount")
                d = (body.get("date") or "").strip()
                if not item: self._send(400, "text/plain; charset=utf-8", b"item required"); return
                if not is_int(amount): self._send(400, "text/plain; charset=utf-8", b"amount must be int"); return
                if d and not valid_date(d): self._send(400, "text/plain; charset=utf-8", b"invalid date"); return
                rec = add_record(item, int(amount), d or None)
                ok_json(self, rec); return
            if p.path == "/api/goals":
                raw = self.rfile.read(length)
                try: body = json.loads(raw.decode("utf-8"))
                except Exception:
                    self._send(400, "text/plain; charset=utf-8", b"invalid json"); return
                goal = (body.get("goal") or "").strip()
                amount = body.get("amount")
                if not goal or not is_int(amount):
                    self._send(400, "text/plain; charset=utf-8", b"bad params"); return
                append_row(GOALS_CSV, [goal, str(int(amount))])
                ok_json(self, {"ok": True}); return
            if p.path == "/api/presets":
                raw = self.rfile.read(length)
                try: body = json.loads(raw.decode("utf-8"))
                except Exception:
                    self._send(400, "text/plain; charset=utf-8", b"invalid json"); return
                label = (body.get("label") or "").strip()
                amount = body.get("amount")
                if not label or not is_int(amount):
                    self._send(400, "text/plain; charset=utf-8", b"bad params"); return
                append_row(PRESETS_CSV, [label, str(int(amount))])
                ok_json(self, {"ok": True}); return
            self._send(404, "text/plain; charset=utf-8", b"Not Found")
        except Exception as e:
            self._send(500, "text/plain; charset=utf-8", str(e).encode("utf-8"))

    def do_DELETE(self):
        try:
            p = urlparse(self.path)
            if p.path == "/api/goals":
                q = parse_qs(p.query); name = (q.get("goal") or [""])[0]
                rows = read_rows(GOALS_CSV)
                out = [rows[0]] + [r for r in rows[1:] if len(r)>=1 and r[0] != name]
                write_rows(GOALS_CSV, out)
                ok_json(self, {"ok": True}); return
            if p.path == "/api/presets":
                q = parse_qs(p.query); label = (q.get("label") or [""])[0]
                rows = read_rows(PRESETS_CSV)
                out = [rows[0]] + [r for r in rows[1:] if len(r)>=1 and r[0] != label]
                write_rows(PRESETS_CSV, out)
                ok_json(self, {"ok": True}); return
            self._send(404, "text/plain; charset=utf-8", b"Not Found")
        except Exception as e:
            self._send(500, "text/plain; charset=utf-8", str(e).encode("utf-8"))

    def _send(self, code:int, ctype:str, data:bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

def run_self_tests():
    global ALLOWANCE_CSV, GOALS_CSV, PRESETS_CSV
    print("[SELFTEST] start")
    assert is_int(0) and is_int("10") and is_int(-5)
    assert not is_int("a")
    assert valid_date("2025-09-01") and not valid_date("2025-13-01")
    assert valid_month("2025-09") and not valid_month("2025-00")
    tmp = tempfile.mkdtemp(prefix="allowance_test_")
    old_allow, old_goals, old_presets = ALLOWANCE_CSV, GOALS_CSV, PRESETS_CSV
    try:
        ALLOWANCE_CSV = os.path.join(tmp, "allowance.csv")
        GOALS_CSV = os.path.join(tmp, "goals.csv")
        PRESETS_CSV = os.path.join(tmp, "presets.csv")
        ensure_csv(ALLOWANCE_CSV, ["date","item","amount","balance"])
        ensure_csv(GOALS_CSV, ["goal","amount"])
        ensure_csv(PRESETS_CSV, ["label","amount"])
        append_row(ALLOWANCE_CSV, ["2025-08-31", "init", "200", "200"])
        append_row(ALLOWANCE_CSV, ["2025-09-10", "a", "1000", "1200"])
        append_row(ALLOWANCE_CSV, ["2025-09-11", "b", "-300", "900"])
        append_row(GOALS_CSV, ["Switch", "25000"])
        append_row(PRESETS_CSV, ["皿洗い", "100"])
        s = month_summary("2025-09"); assert s["income"]==1000 and s["expense"]==300 and s["net"]==700
        rec1 = add_record("bonus", 500, "2025-09-12"); assert rec1["balance"] == 1400
        rec2 = add_record("snack", -200, "2025-09-13"); assert rec2["balance"] == 1200
        last7 = last_n_days_records(7); assert isinstance(last7, list)
        print("[SELFTEST] OK")
    finally:
        shutil.rmtree(tmp)
        ALLOWANCE_CSV, GOALS_CSV, PRESETS_CSV = old_allow, old_goals, old_presets

def try_bind_server(host: str, port: int):
    return HTTPServer((host, port), AppHandler)

def start_server_with_fallback():
    hosts = [DEFAULT_HOST]
    for h in ["127.0.0.1", "0.0.0.0", "::1"]:
        if h not in hosts: hosts.append(h)
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
                last_err = e; continue
    print("[WARN] HTTP server could not bind to any host/port in this environment.")
    print("       Try on Android/Termux or set ALLOWANCE_HOST/ALLOWANCE_PORT.\n       You can still run self tests: python allowance.py --selftest")
    if last_err: print(f"[DETAIL] last error: {last_err}")
    return None

def main():
    if "--selftest" in sys.argv:
        run_self_tests(); return
    ensure_csv(ALLOWANCE_CSV, ["date","item","amount","balance"])
    ensure_csv(GOALS_CSV, ["goal","amount"])
    ensure_csv(PRESETS_CSV, ["label","amount"])
    srv = start_server_with_fallback()
    if srv is None: return
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")

if __name__ == '__main__':
    main()
