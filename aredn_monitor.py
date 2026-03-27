#!/usr/bin/env python3
"""AREDN Node Monitor - python3 aredn_monitor.py [--host 0.0.0.0] [--port 8765]"""
import argparse, json, re, sys, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

_SR = re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+([-+]?(?:NaN|[+-]?Inf|\d*\.?\d+(?:[eE][-+]?\d+)?))')
_LR = re.compile(r'(\w+)="([^"]*)"')

def parse_prom(text):
    r = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'): continue
        m = _SR.match(line)
        if not m: continue
        labels = dict(_LR.findall(m.group(2) or ''))
        try: val = float(m.group(3))
        except: val = None
        r.setdefault(m.group(1), []).append({'labels': labels, 'value': val})
    return r

PAGE = b"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AREDN Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d1117;--card:#161b22;--bdr:#30363d;--g:#00cc66;--t:#c9d1d9;--d:#8b949e;--w:#f0a500;--r:#ff4444;--b:#3b82f6}
body{background:var(--bg);color:var(--t);font:14px 'Segoe UI',sans-serif}
::-webkit-scrollbar{width:5px;height:5px}::-webkit-scrollbar-thumb{background:#333;border-radius:3px}
#hdr{position:sticky;top:0;z-index:99;background:rgba(13,17,23,.95);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--bdr);padding:9px 16px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.logo{font-size:16px;font-weight:700;color:var(--g);white-space:nowrap}
.logo small{color:var(--d);font-size:11px;font-weight:400;margin-left:5px}
#tabs{display:flex;gap:4px;flex-wrap:wrap;flex:1}
.tab{display:flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;cursor:pointer;
  font-size:12px;border:1px solid var(--bdr);background:var(--card);color:var(--d);transition:all .2s}
.tab.active{background:var(--g);color:#000;border-color:var(--g)}
.tab:hover:not(.active){border-color:var(--g);color:var(--t)}
.dot{width:6px;height:6px;border-radius:50%;background:var(--d);flex-shrink:0}
.tab.ok .dot{background:#00ff88;box-shadow:0 0 4px #00ff88}.tab.err .dot{background:var(--r)}
.tab .x{opacity:0;font-size:9px;margin-left:1px;transition:opacity .15s}
.tab:hover .x{opacity:.5}.tab .x:hover{opacity:1;color:var(--r)}
#ctrl{display:flex;align-items:center;gap:6px;margin-left:auto;flex-wrap:wrap}
select{background:var(--card);color:var(--t);border:1px solid var(--bdr);padding:3px 7px;border-radius:6px;font-size:12px}
.btn{padding:3px 10px;border-radius:6px;cursor:pointer;font-size:12px;border:1px solid var(--bdr);
  background:var(--card);color:var(--t);transition:all .2s;white-space:nowrap}
.btn:hover{border-color:var(--g);color:var(--g)}
.btn.p{background:var(--g);color:#000;border-color:var(--g)}.btn.p:hover{background:#00ee77}
.spin{display:inline-block;width:11px;height:11px;border:2px solid var(--bdr);
  border-top-color:var(--g);border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.ts{font-size:11px;color:var(--d)}
#alert{display:none;padding:7px 16px;font-size:12px}
#alert.e{display:block;background:#2d1010;border-bottom:1px solid #f445;color:#f99}
#main{padding:14px 16px 40px;max-width:1700px;margin:0 auto}
.bnr{display:grid;grid-template-columns:repeat(auto-fill,minmax(145px,1fr));gap:1px;
  background:var(--bdr);border:1px solid var(--bdr);border-radius:8px;overflow:hidden;margin-bottom:13px}
.ni{background:var(--card);padding:9px 12px}
.nl{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--d);margin-bottom:2px}
.nv{font-size:13px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.nv.hl{color:var(--g);font-size:15px;font-weight:700}
.sh{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--d);
  margin:15px 0 9px;padding-bottom:5px;border-bottom:1px solid var(--bdr)}
.grid{display:grid;gap:10px;margin-bottom:10px}
.g4{grid-template-columns:repeat(4,1fr)}.g2{grid-template-columns:repeat(2,1fr)}
@media(max-width:1100px){.g4{grid-template-columns:repeat(2,1fr)}}
@media(max-width:640px){.g4,.g2{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--bdr);border-radius:8px;padding:12px 14px;position:relative;overflow:hidden}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.cg::before{background:var(--g)}.cw::before{background:var(--w)}.cr::before{background:var(--r)}
.ct{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--d);margin-bottom:8px}
.sv{font-size:24px;font-weight:700;color:var(--g);line-height:1.1}
.su{font-size:11px;color:var(--d);margin-top:3px}
.sx{font-size:11px;color:var(--d);margin-top:6px;padding-top:6px;border-top:1px solid var(--bdr)}
.pb{margin-top:8px}.pbr{display:flex;justify-content:space-between;font-size:11px;color:var(--d);margin-bottom:3px}
.pbt{height:5px;background:#1a2030;border-radius:3px;overflow:hidden}
.pbf{height:100%;border-radius:3px;transition:width .5s}
.pbf.g{background:var(--g)}.pbf.w{background:var(--w)}.pbf.r{background:var(--r)}
.lbs{display:flex;gap:5px;align-items:flex-end;height:42px;margin-top:5px}
.lbw{display:flex;flex-direction:column;align-items:center;gap:2px;flex:1}
.lbv{font-size:11px}.lbt{background:#1a2030;border-radius:2px;width:100%;flex:1;display:flex;align-items:flex-end}
.lbf{width:100%;border-radius:2px;transition:height .5s;min-height:2px}.lbl{font-size:9px;color:var(--d)}
.cbox{height:180px;position:relative}
.tbl{width:100%;border-collapse:collapse;font-size:12px}
.tbl th{padding:6px 9px;color:var(--d);font-weight:500;font-size:10px;text-transform:uppercase;
  border-bottom:1px solid var(--bdr);text-align:left}
.tbl td{padding:6px 9px;border-bottom:1px solid #1e242e}
.tbl tr:last-child td{border-bottom:none}.tbl tbody tr:hover td{background:#1c2333}
.bdg{display:inline-block;padding:2px 7px;border-radius:10px;font-size:10px;font-weight:600}
.bg{background:#00441a33;color:#0c6;border:1px solid #00441a55}
.bw{background:#443a0033;color:#f0a500;border:1px solid #443a0055}
.br{background:#44000033;color:#f44;border:1px solid #44000055}
.bn{background:#22263033;color:var(--d);border:1px solid var(--bdr)}
.raw-hd{cursor:pointer;font-size:12px;color:var(--d);display:flex;align-items:center;gap:5px;user-select:none}
.raw-hd:hover{color:var(--g)}
.raw-bd{display:none;background:#090d12;border:1px solid var(--bdr);border-radius:6px;margin-top:6px;
  padding:11px;font-family:monospace;font-size:11px;color:#57f287;max-height:250px;overflow-y:auto;
  white-space:pre;word-break:break-all}
.raw-bd.open{display:block}
.ov{position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:200;display:none;
  align-items:center;justify-content:center;padding:16px}
.ov.open{display:flex}
.modal{background:var(--card);border:1px solid var(--bdr);border-radius:8px;padding:22px;width:420px;max-width:100%}
.modal h3{margin-bottom:13px;font-size:15px}
.modal label{display:block;margin-bottom:4px;font-size:12px;color:var(--d)}
.modal input{width:100%;background:var(--bg);border:1px solid var(--bdr);color:var(--t);
  padding:7px 9px;border-radius:6px;font-size:13px;margin-bottom:11px}
.modal input:focus{outline:none;border-color:var(--g)}
.hint{font-size:11px;color:var(--d);line-height:1.5;margin-bottom:11px}
.mbtns{display:flex;gap:7px;justify-content:flex-end}
.empty{text-align:center;padding:70px 20px;color:var(--d)}
.empty .ico{font-size:50px;margin-bottom:14px}.empty p{margin-bottom:16px;font-size:15px}
</style></head><body>

<div id="hdr">
  <div class="logo">&#x1F4E1; AREDN Monitor <small>Prometheus Dashboard</small></div>
  <div id="ctrl">
    <span id="sw" style="display:none"><span class="spin"></span></span>
    <select id="ivs" onchange="applyIv()">
      <option value="0">Manual</option><option value="15">15s</option>
      <option value="30" selected>30s</option><option value="60">60s</option>
      <option value="120">2min</option>
    </select>
    <select id="nodeSel" style="display:none;min-width:220px" onchange="nodeSelChanged()"></select>
    <button class="btn" onclick="fetchAll()">&#8635; Refresh</button>
    <button class="btn p" onclick="openMod()">+ Add Node</button>
    <button class="btn" id="rmBtn" style="display:none" onclick="removeActiveNode()">Remove Node</button>
    <span class="ts" id="ts">&#8212;</span>
  </div>
</div>

<div id="alert"></div>
<div id="main"><div class="empty"><div class="ico">&#x1F4E1;</div>
  <p>Add an AREDN node to get started</p>
  <button class="btn p" onclick="openMod()">+ Add Node</button></div></div>

<div class="ov" id="ov">
  <div class="modal">
    <h3>&#x1F4E1; Add AREDN Node</h3>
    <label>Hostname or IP address</label>
    <input id="ih" type="text" placeholder="localnode.local.mesh  or  10.x.x.x">
    <label>Display name <span style="color:var(--d)">(optional)</span></label>
    <input id="iname" type="text" placeholder="My Node">
    <div class="hint">Metrics are fetched server-side via <code style="color:var(--g)">/cgi-bin/metrics</code>.
      Your browser only needs to reach this dashboard server.</div>
    <div class="mbtns">
      <button class="btn" onclick="closeMod()">Cancel</button>
      <button class="btn p" onclick="addNode()">Add &amp; Fetch</button>
    </div>
  </div>
</div>

<script>
'use strict';
const CONFIG_NODES=__CONFIG_NODES__;
const DEFAULT_IV=__DEFAULT_IV__;
const S={nodes:(CONFIG_NODES||[]).map(n=>({host:n.host,name:n.name||n.host,status:'unknown',metrics:null,raw:'',error:null})),active:0,timer:null,hist:{},charts:{},MH:120};
const COLS=['#00cc66','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#ec4899','#06b6d4'];
const ge=id=>document.getElementById(id);
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

const fmt={
  b:v=>{if(v==null||isNaN(v))return'N/A';const u=['B','KB','MB','GB','TB'];let i=0;while(v>=1024&&i<4){v/=1024;i++;}return v.toFixed(i?1:0)+'\\u00A0'+u[i];},
  bps:v=>v==null?'N/A':fmt.b(v)+'/s',
  up:s=>{if(s==null)return'N/A';s=Math.floor(s);const d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60),sc=s%60;return d?d+'d '+h+'h '+m+'m':h?h+'h '+m+'m '+sc+'s':m+'m '+sc+'s';},
  pct:v=>v==null?'N/A':v.toFixed(1)+'%',
  ld:v=>v==null?'N/A':v.toFixed(2),
  n:v=>v==null?'N/A':Math.round(v).toLocaleString(),
  ts:()=>new Date().toLocaleTimeString()
};

function gv(M,n,lf){const s=(M[n]||[]).find(s=>!lf||Object.entries(lf).every(([k,v])=>s.labels[k]===v));return s?s.value:null;}
function ga(M,n){return M[n]||[];}
function pc(v){return v>90?['cr','r']:v>70?['cw','w']:['cg','g'];}
function lc(v){return v>1.5?'var(--r)':v>1?'var(--w)':'var(--g)';}
function qb(q){if(q==null)return'<span class="bdg bn">N/A</span>';return'<span class="bdg '+(q>.7?'bg':q>.4?'bw':'br')+'">'+(q*100).toFixed(0)+'%</span>';}
function sc(s){return s==null?'var(--d)':s>-65?'var(--g)':s>-80?'var(--w)':'var(--r)';}

function save(){try{localStorage.setItem('aredn',JSON.stringify(S.nodes.map(n=>({host:n.host,name:n.name}))));}catch(e){}}
function loadSaved(){try{const raw=localStorage.getItem('aredn');if(!raw)return;const d=JSON.parse(raw||'[]');if(Array.isArray(d)&&d.length){S.nodes=d.map(n=>({host:n.host,name:n.name||n.host,status:'unknown',metrics:null,raw:'',error:null}));}}catch(e){}}

function openMod(){ge('ov').classList.add('open');setTimeout(()=>ge('ih').focus(),80);}
function closeMod(){ge('ov').classList.remove('open');}
ge('ov').addEventListener('click',e=>{if(e.target===ge('ov'))closeMod();});
ge('ih').addEventListener('keydown',e=>{if(e.key==='Enter')ge('iname').focus();});
ge('iname').addEventListener('keydown',e=>{if(e.key==='Enter')addNode();});

function addNode(){
  const host=ge('ih').value.trim(),name=ge('iname').value.trim()||ge('ih').value.trim();
  if(!host)return;
  if(S.nodes.find(n=>n.host===host)){alert('Already added.');return;}
  S.nodes.push({host,name,status:'unknown',metrics:null,raw:'',error:null});
  S.active=S.nodes.length-1;
  save();closeMod();renderNodeSel();fetchAll();
  ge('ih').value='';ge('iname').value='';
}
function removeNode(i,e){
  if(e)e.stopPropagation();
  if(!confirm('Remove "'+S.nodes[i].name+'"?'))return;
  S.nodes.splice(i,1);
  if(S.active>=S.nodes.length)S.active=Math.max(0,S.nodes.length-1);
  save();renderNodeSel();S.nodes.length?renderDash():renderEmpty();updateAlert();
}
function selectNode(i){S.active=i;renderNodeSel();renderDash();updateAlert();}
function nodeSelChanged(){
  const sel=ge('nodeSel');
  const i=parseInt(sel.value);
  if(!isNaN(i))selectNode(i);
}
function removeActiveNode(){
  if(!S.nodes.length)return;
  removeNode(S.active);
}
function renderNodeSel(){
  const sel=ge('nodeSel');
  const rm=ge('rmBtn');
  if(!S.nodes.length){
    if(sel){sel.style.display='none';sel.innerHTML='';}
    if(rm)rm.style.display='none';
    return;
  }
  if(sel){
    sel.style.display='inline-block';
    const cur=S.active;
    sel.innerHTML=S.nodes.map((n,i)=>{
      const st=n.status==='ok'?'OK':n.status==='err'?'ERR':'?';
      return '<option value="'+i+'">'+esc(n.name)+' ('+esc(st)+')</option>';
    }).join('');
    sel.value=String(cur);
  }
  if(rm)rm.style.display='inline-block';
}

async function fetchAll(){
  if(!S.nodes.length)return;
  ge('sw').style.display='inline';
  await Promise.all(S.nodes.map(fetchNode));
  ge('sw').style.display='none';
  ge('ts').textContent='Updated '+fmt.ts();
  renderNodeSel();renderDash();updateAlert();
}
async function fetchNode(node){
  try{
    const r=await fetch('/api/metrics?node='+encodeURIComponent(node.host));
    const d=await r.json();
    if(!d.ok)throw new Error(d.error||'error');
    node.status='ok';node.error=null;node.metrics=d.metrics;node.raw=d.raw;
    updateHist(node.host,d.metrics);
  }catch(e){node.status='err';node.error=e.message;}
}

function updateHist(host,M){
  if(!S.hist[host])S.hist[host]={};
  const h=S.hist[host],t=Date.now();
  for(const m of['node_network_receive_bytes_total','node_network_transmit_bytes_total',
      'node_load1','node_memory_MemTotal_bytes','node_memory_MemAvailable_bytes']){
    for(const s of(M[m]||[])){
      const k=m+JSON.stringify(s.labels);
      if(!h[k])h[k]=[];
      h[k].push({t,v:s.value,labels:s.labels});
      if(h[k].length>S.MH)h[k].shift();
    }
  }
}

function renderEmpty(){ge('main').innerHTML='<div class="empty"><div class="ico">&#x1F4E1;</div><p>Add an AREDN node to get started</p><button class="btn p" onclick="openMod()">+ Add Node</button></div>';}
function updateAlert(){
  const n=S.nodes[S.active],b=ge('alert');
  if(!n||n.status!=='err'){b.className='';b.style.display='none';return;}
  b.className='e';b.style.display='block';
  b.innerHTML='&#9888; Cannot reach <strong>'+esc(n.host)+'</strong>: '+esc(n.error);
}

function renderDash(){
  const node=S.nodes[S.active];
  if(!node||!node.metrics){renderEmpty();return;}
  const M=node.metrics,host=node.host,h=S.hist[host]||{};

  const iS=ga(M,'node_arednlink_info'),rS=ga(M,'node_aredn_meshrf');
  const inf=iS.length?iS[0].labels:{},rf=rS.length?rS[0].labels:{};
  const nn=inf.node||rf.node||host,model=inf.model||rf.model||'Unknown',fw=inf.firmware||rf.firmware||'Unknown';
  const band=inf.band||rf.band||'N/A',ch=inf.channel||rf.channel||'N/A';
  const bw=inf.channel_width||rf.chanbw||'N/A',freq=inf.frequency||rf.frequency||'N/A';
  const ssid=inf.ssid||rf.ssid||'N/A',grid=inf.grid_square||'N/A',desc=inf.description||'';
  const lat=inf.lat?parseFloat(inf.lat).toFixed(5):null,lon=inf.lon?parseFloat(inf.lon).toFixed(5):null;

  const tN=gv(M,'node_time_seconds'),tB=gv(M,'node_boot_time_seconds');
  const up=(tN!=null&&tB!=null)?tN-tB:null;
  const mT=gv(M,'node_memory_MemTotal_bytes'),mA=gv(M,'node_memory_MemAvailable_bytes')??gv(M,'node_memory_MemFree_bytes');
  const mU=(mT&&mA)?mT-mA:null,mP=(mT&&mU)?mU/mT*100:null;
  const fsZ=gv(M,'node_filesystem_size_bytes',{mountpoint:'/'}),fsA=gv(M,'node_filesystem_avail_bytes',{mountpoint:'/'});
  const fsU=(fsZ&&fsA)?fsZ-fsA:null,fsP=(fsZ&&fsU)?fsU/fsZ*100:null;
  const l1=gv(M,'node_load1'),l5=gv(M,'node_load5'),l15=gv(M,'node_load15');
  const nbrs=gv(M,'node_arednlink_neighbors_count_total'),rts=gv(M,'node_arednlink_routes_count_total');
  const bNbr=gv(M,'node_babel_neighbor_total'),bRts=gv(M,'node_babel_route_total');
  const cIn=gv(M,'node_arednlink_connection_incoming_total'),cOut=gv(M,'node_arednlink_connection_outgoing_total');
  const svc=gv(M,'node_arednlink_service_count_total');
  const lqmS=ga(M,'node_lqm_tracker_quality'),sigS=ga(M,'node_lqm_tracker_signal');
  const noiS=ga(M,'node_lqm_tracker_noise'),snrS=ga(M,'node_lqm_tracker_snr');
  const rxS=ga(M,'node_network_receive_bytes_total'),txS=ga(M,'node_network_transmit_bytes_total');
  const rxES=ga(M,'node_network_receive_errs_total'),txES=ga(M,'node_network_transmit_errs_total');

  function rate(mn,labels){
    const k=mn+JSON.stringify(labels),pts=h[k]||[];
    if(pts.length<2)return null;
    const a=pts[pts.length-2],b=pts[pts.length-1],dt=(b.t-a.t)/1000,dv=b.v-a.v;
    return(dt>0&&dv>=0)?dv/dt:null;
  }
  function lbar(lbl,v){
    return'<div class="lbw"><div class="lbv" style="color:'+lc(v)+'">'+fmt.ld(v)+'</div>'
      +'<div class="lbt"><div class="lbf" style="height:'+Math.min(100,v!=null?v/2*100:0)+'%;background:'+lc(v)+'"></div></div>'
      +'<div class="lbl">'+lbl+'</div></div>';
  }
  const mc=pc(mP),fc=pc(fsP),lcls=l1>1.5?'cr':l1>1?'cw':'cg';

  const lqmRows=lqmS.map(s=>{
    const p=s.labels.node||s.labels.hostname||'?',q=s.value;
    const sig=(sigS.find(x=>x.labels.node===p)||{}).value??null;
    const noi=(noiS.find(x=>x.labels.node===p)||{}).value??null;
    const snr=(snrS.find(x=>x.labels.node===p)||{}).value??(sig!=null&&noi!=null?sig-noi:null);
    return'<tr><td><strong>'+esc(p)+'</strong></td><td>'+qb(q)+'</td>'
      +'<td style="color:'+sc(sig)+';font-weight:600">'+(sig!=null?sig.toFixed(0)+' dBm':'&#8212;')+'</td>'
      +'<td style="color:var(--w)">'+(noi!=null?noi.toFixed(0)+' dBm':'&#8212;')+'</td>'
      +'<td style="color:var(--b)">'+(snr!=null?snr.toFixed(0)+' dB':'&#8212;')+'</td></tr>';
  }).join('')||'<tr><td colspan="5" style="text-align:center;color:var(--d);padding:14px">No LQM data</td></tr>';

  const ifMap={};
  [[rxS,'rx'],[txS,'tx'],[rxES,'rxe'],[txES,'txe']].forEach(([arr,k])=>arr.forEach(s=>{const d=s.labels.device||'?';if(!ifMap[d])ifMap[d]={};ifMap[d][k]=s.value;}));
  const ifRows=Object.entries(ifMap).filter(([d])=>d!=='lo').map(([dev,d])=>{
    const rR=rate('node_network_receive_bytes_total',{device:dev}),tR=rate('node_network_transmit_bytes_total',{device:dev}),err=(d.rxe||0)+(d.txe||0);
    return'<tr><td><code style="color:var(--g)">'+esc(dev)+'</code></td>'
      +'<td>'+fmt.b(d.rx??null)+'</td><td>'+fmt.b(d.tx??null)+'</td>'
      +'<td style="color:var(--b)">'+(rR!=null?fmt.bps(rR):'&#8212;')+'</td>'
      +'<td style="color:var(--w)">'+(tR!=null?fmt.bps(tR):'&#8212;')+'</td>'
      +'<td>'+(err>0?'<span class="bdg br">'+fmt.n(err)+'</span>':'<span class="bdg bg">0</span>')+'</td></tr>';
  }).join('')||'<tr><td colspan="6" style="text-align:center;color:var(--d);padding:14px">No interface data</td></tr>';

  ge('main').innerHTML=
    '<div class="bnr">'
    +'<div class="ni"><div class="nl">Node</div><div class="nv hl">'+esc(nn)+'</div></div>'
    +'<div class="ni"><div class="nl">Model</div><div class="nv">'+esc(model)+'</div></div>'
    +'<div class="ni"><div class="nl">Firmware</div><div class="nv">'+esc(fw)+'</div></div>'
    +'<div class="ni"><div class="nl">Band</div><div class="nv">'+esc(band)+'</div></div>'
    +'<div class="ni"><div class="nl">Ch / Width</div><div class="nv">Ch'+esc(ch)+' / '+esc(bw)+'MHz</div></div>'
    +'<div class="ni"><div class="nl">Frequency</div><div class="nv">'+esc(freq)+' MHz</div></div>'
    +'<div class="ni"><div class="nl">SSID</div><div class="nv">'+esc(ssid)+'</div></div>'
    +'<div class="ni"><div class="nl">Grid Square</div><div class="nv">'+esc(grid)+'</div></div>'
    +'<div class="ni"><div class="nl">Location</div><div class="nv">'+(lat&&lon?lat+'&deg; '+lon+'&deg;':'N/A')+'</div></div>'
    +'<div class="ni"><div class="nl">Uptime</div><div class="nv">'+fmt.up(up)+'</div></div>'
    +(desc?'<div class="ni" style="grid-column:span 2"><div class="nl">Description</div><div class="nv">'+esc(desc)+'</div></div>':'')
    +'</div>'
    +'<div class="sh">System Health</div>'
    +'<div class="grid g4">'
    +'<div class="card cg"><div class="ct">Uptime</div><div class="sv" style="font-size:19px">'+fmt.up(up)+'</div><div class="su">Since last boot</div></div>'
    +'<div class="card '+lcls+'"><div class="ct">CPU Load</div><div class="lbs">'+lbar('1m',l1)+lbar('5m',l5)+lbar('15m',l15)+'</div></div>'
    +'<div class="card '+mc[0]+'"><div class="ct">Memory</div><div class="sv">'+fmt.b(mU)+'</div><div class="su">of '+fmt.b(mT)+'</div>'
      +'<div class="pb"><div class="pbr"><span>Used</span><span>'+fmt.pct(mP)+'</span></div>'
      +'<div class="pbt"><div class="pbf '+mc[1]+'" style="width:'+Math.min(100,mP||0)+'%"></div></div></div></div>'
    +'<div class="card '+fc[0]+'"><div class="ct">Storage (rootfs)</div><div class="sv">'+fmt.b(fsU)+'</div><div class="su">of '+fmt.b(fsZ)+'</div>'
      +'<div class="pb"><div class="pbr"><span>Used</span><span>'+fmt.pct(fsP)+'</span></div>'
      +'<div class="pbt"><div class="pbf '+fc[1]+'" style="width:'+Math.min(100,fsP||0)+'%"></div></div></div></div>'
    +'</div>'
    +'<div class="sh">Mesh Connectivity</div>'
    +'<div class="grid g4">'
    +'<div class="card cg"><div class="ct">Neighbors</div><div class="sv">'+fmt.n(nbrs)+'</div>'+(bNbr!=null?'<div class="sx">Babel: <strong>'+fmt.n(bNbr)+'</strong></div>':'')+'</div>'
    +'<div class="card cg"><div class="ct">Routes</div><div class="sv">'+fmt.n(rts)+'</div>'+(bRts!=null?'<div class="sx">Babel: <strong>'+fmt.n(bRts)+'</strong></div>':'')+'</div>'
    +'<div class="card"><div class="ct">Incoming Connections</div><div class="sv">'+fmt.n(cIn)+'</div></div>'
    +'<div class="card"><div class="ct">Outgoing Connections</div><div class="sv">'+fmt.n(cOut)+'</div>'+(svc!=null?'<div class="sx">Services: <strong>'+fmt.n(svc)+'</strong></div>':'')+'</div>'
    +'</div>'
    +'<div class="sh">Network Traffic</div>'
    +'<div class="grid g2">'
    +'<div class="card"><div class="ct">Receive Rate</div><div class="cbox"><canvas id="rxC"></canvas></div></div>'
    +'<div class="card"><div class="ct">Transmit Rate</div><div class="cbox"><canvas id="txC"></canvas></div></div>'
    +'</div>'
    +'<div class="sh">Link Quality (LQM)</div>'
    +'<div class="card" style="padding:0;overflow:hidden;margin-bottom:11px">'
    +'<table class="tbl"><thead><tr><th>Peer Node</th><th>Quality</th><th>Signal</th><th>Noise</th><th>SNR</th></tr></thead>'
    +'<tbody>'+lqmRows+'</tbody></table></div>'
    +'<div class="sh">Network Interfaces</div>'
    +'<div class="card" style="padding:0;overflow:hidden;margin-bottom:11px">'
    +'<table class="tbl"><thead><tr><th>Interface</th><th>Total RX</th><th>Total TX</th><th>RX Rate</th><th>TX Rate</th><th>Errors</th></tr></thead>'
    +'<tbody>'+ifRows+'</tbody></table></div>'
    +'<div class="sh">Raw Prometheus Metrics</div>'
    +'<div style="margin-bottom:28px">'
    +'<div class="raw-hd" onclick="toggleRaw()"><span id="ra">&#9654;</span> Show raw <code style="color:var(--g)">/cgi-bin/metrics</code>'
    +' <button class="btn" style="font-size:10px;padding:2px 7px;margin-left:7px" onclick="cpRaw(event)">&#128203; Copy</button></div>'
    +'<div class="raw-bd" id="rb">'+esc(node.raw||'')+'</div></div>';

  setTimeout(()=>renderCharts(host,M,h),0);
}

function toggleRaw(){const o=ge('rb').classList.toggle('open');ge('ra').textContent=o?'&#9660;':'&#9654;';}
function cpRaw(e){e.stopPropagation();const n=S.nodes[S.active];if(n)navigator.clipboard.writeText(n.raw||'').then(()=>alert('Copied!'));}

function killChart(id){if(S.charts[id]){try{S.charts[id].destroy();}catch(e){}delete S.charts[id];}}
function renderCharts(host,M,h){
  ['rxC','txC'].forEach(killChart);
  const copts={responsive:true,maintainAspectRatio:false,animation:{duration:250},
    plugins:{legend:{position:'bottom',labels:{color:'#8b949e',boxWidth:11,font:{size:10}}},
      tooltip:{mode:'index',intersect:false,callbacks:{label:c=>' '+c.dataset.label+': '+fmt.bps(c.parsed.y)}}},
    scales:{x:{ticks:{color:'#4d5566',maxTicksLimit:5,font:{size:10}},grid:{color:'#1c2333'}},
      y:{ticks:{color:'#4d5566',callback:v=>fmt.bps(v),font:{size:10}},grid:{color:'#1c2333'},min:0}}};

  function buildDs(mn,samples){
    return samples.filter(s=>s.labels.device!=='lo').map((s,i)=>{
      const k=mn+JSON.stringify(s.labels),pts=h[k]||[];
      const data=[];
      for(let j=1;j<pts.length;j++){
        const dt=(pts[j].t-pts[j-1].t)/1000,dv=pts[j].v-pts[j-1].v;
        if(dt>0)data.push({x:new Date(pts[j].t).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'}),y:dv<0?0:dv/dt});
      }
      return{label:s.labels.device||'?',data,borderColor:COLS[i%COLS.length],
        backgroundColor:COLS[i%COLS.length]+'18',borderWidth:1.5,pointRadius:2,tension:.35,fill:true};
    });
  }
  function mk(id,ds){const el=ge(id);if(!el||!ds.length)return;S.charts[id]=new Chart(el.getContext('2d'),{type:'line',data:{datasets:ds},options:copts});}
  mk('rxC',buildDs('node_network_receive_bytes_total',ga(M,'node_network_receive_bytes_total')));
  mk('txC',buildDs('node_network_transmit_bytes_total',ga(M,'node_network_transmit_bytes_total')));
}

function applyIv(){clearInterval(S.timer);const iv=parseInt(ge('ivs').value);if(iv>0)S.timer=setInterval(fetchAll,iv*1000);}

ge('ivs').value=String(DEFAULT_IV||30);loadSaved();renderNodeSel();
if(S.nodes.length){fetchAll();applyIv();}
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, f, *a): print("  %s %s" % (self.command, self.path))
    def _json(self, code, obj):
        b=json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(b)))
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
    def do_GET(self):
        p = urlparse(self.path)
        if p.path in ('/', '', '/index.html'):
            page = getattr(self.server, 'page', PAGE)
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(page)))
            self.end_headers(); self.wfile.write(page)
        elif p.path == '/api/metrics':
            params = parse_qs(p.query)
            node = params.get('node',['localnode.local.mesh'])[0]
            url = node if node.startswith('http') else 'http://'+node+'/cgi-bin/metrics'
            try:
                req = urllib.request.Request(url, headers={'User-Agent':'AREDN-Monitor/2.0'})
                with urllib.request.urlopen(req, timeout=12) as r:
                    raw = r.read().decode('utf-8','replace')
                self._json(200,{'ok':True,'url':url,'raw':raw,'metrics':parse_prom(raw)})
            except urllib.error.URLError as e:
                self._json(502,{'ok':False,'error':str(e.reason),'url':url})
            except Exception as e:
                self._json(500,{'ok':False,'error':str(e),'url':url})
        else:
            self.send_response(404); self.end_headers()

def _load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _clamp_iv(sec):
    # Values must match one of the <select> options in the embedded UI.
    allowed = {0, 15, 30, 60, 120}
    try:
        iv = int(sec)
    except Exception:
        return 30
    return iv if iv in allowed else 30

def _build_page(config):
    dash = (config or {}).get('dashboard', {}) if isinstance(config, dict) else {}
    nodes = dash.get('nodes', []) if isinstance(dash, dict) else []
    cleaned_nodes = []
    if isinstance(nodes, list):
        for n in nodes:
            if not isinstance(n, dict) or 'host' not in n:
                continue
            cleaned_nodes.append({'host': str(n['host']), 'name': str(n.get('name') or n['host'])})

    iv = _clamp_iv(dash.get('refresh_seconds', 30) if isinstance(dash, dict) else 30)
    nodes_json = json.dumps(cleaned_nodes, ensure_ascii=True)
    # Inject as raw JS literals.
    page = PAGE.replace(b'__CONFIG_NODES__', nodes_json.encode('utf-8'))
    page = page.replace(b'__DEFAULT_IV__', str(iv).encode('utf-8'))
    return page

def main():
    ap = argparse.ArgumentParser(description='AREDN Node Monitor')
    ap.add_argument('--config', default=None, help='Path to JSON config file')
    ap.add_argument('--host', default=None)
    ap.add_argument('--port', type=int, default=None)
    a = ap.parse_args()

    config = {}
    if a.config:
        try:
            config = _load_config(a.config)
        except Exception as e:
            print(f'Failed to load config {a.config}: {e}', file=sys.stderr)
            raise SystemExit(2)

    server_cfg = (config or {}).get('server', {}) if isinstance(config, dict) else {}
    host = a.host or server_cfg.get('host', '127.0.0.1')
    port = a.port or server_cfg.get('port', 8765)

    srv = HTTPServer((host, port), H)
    srv.page = _build_page(config)
    url = 'http://{}:{}'.format('localhost' if host=='127.0.0.1' else host, port)
    print('='*45)
    print('  AREDN Node Monitor')
    print('  Open: '+url)
    print('  Ctrl+C to stop')
    print('='*45)
    try: srv.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped. 73!'); srv.server_close()

if __name__=='__main__': main()
