// Browser-only sample runner. No provider calls or production data.
// Python remains the authoritative live/Zetaris runtime.
export async function investigateSample(sources, question) {
  if (typeof question !== 'string' || question.trim().length < 5 || question.length > 500) throw new Error('Question must contain 5–500 characters.');
  if (!/(order|delay|risk|stock|kb-01|ms-02|hd-03|ord-)/i.test(question)) throw new Error('Ask about orders, delays, stock, a region or an ORD- identifier.');
  const start = performance.now();
  const id = crypto.randomUUID().replaceAll('-', '');
  const scope = {order_id: question.match(/\bORD-\d+\b/i)?.[0].toUpperCase() || null,
    region: question.match(/\b(north|south|east|west)\b/i)?.[0].toLowerCase() || null,
    sku: question.match(/\b(?:KB-01|MS-02|HD-03)\b/i)?.[0].toUpperCase() || null};
  if (scope.region) scope.region = scope.region[0].toUpperCase() + scope.region.slice(1);
  const hash = async value => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(JSON.stringify(value))))].map(x=>x.toString(16).padStart(2,'0')).join('').slice(0,24);
  const keys={orders:'order_id',inventory:'sku',tickets:'ticket_id'};
  const world={};
  for(const source of Object.keys(keys)) {
    world[source]=[];
    for(const record of sources[source]) {
      const key=String(record[keys[source]]);
      const ordered=Object.fromEntries(Object.keys(record).sort().map(k=>[k,record[k]]));
      world[source].push({source,key,record,citation:await hash(['browser-sample',source,key,ordered]),entity_id:await hash(['browser-sample',source,key]),selection_reason:'exact browser sample snapshot'});
    }
  }
  const matches=world.orders.filter(o=>(!scope.order_id||o.key===scope.order_id)&&(!scope.region||o.record.region===scope.region)&&(!scope.sku||o.record.sku===scope.sku));
  const orders=matches.slice(0,200), ids=new Set(orders.map(o=>o.key)), skus=new Set(orders.map(o=>o.record.sku));
  const inventory=world.inventory.filter(i=>skus.has(i.key));
  const tickets=world.tickets.filter(t=>ids.has(t.record.order_id));
  const evidence=[...orders,...inventory,...tickets];
  const findings=[],actions=[];
  let cents=0,units=0;
  for(const item of orders) {
    const o=item.record;
    if(o.status.toLowerCase()!=='delayed')continue;
    const inv=inventory.find(i=>i.key===o.sku), related=tickets.filter(t=>t.record.order_id===o.order_id);
    const categories=new Set(related.map(t=>t.record.category.toLowerCase()));
    const citations=[item.citation,...(inv?[inv.citation]:[]),...related.map(t=>t.citation)];
    let explanation,certainty,text;
    if(inv&&Number(inv.record.available_units)===0) {
      explanation=`${o.order_id} is delayed and ${o.sku} has zero available units at ${inv.record.warehouse}. Stock shortage is a supported explanation; the causal link is inferred.`;
      if(categories.has('carrier')||categories.has('address'))explanation+=' A support ticket also records a different blocker; resolve both before assigning a root cause.';
      certainty=categories.has('stock')?'corroborated':'inferred';
      text=`Confirm replenishment for ${o.sku} with the warehouse and give ${o.customer} a verified dispatch update.`;
    } else if(categories.has('carrier')) {
      explanation=`${o.order_id} is delayed; support records a carrier collection issue.`;certainty='documented';text=`Ask logistics to confirm the next collection for ${o.order_id}.`;
    } else if(categories.has('address')) {
      explanation=`${o.order_id} is delayed; support records an address confirmation blocker.`;certainty='documented';text=`Request address confirmation for ${o.order_id} before dispatch.`;
    } else {
      explanation=`${o.order_id} is delayed, but current records do not establish a cause.`;certainty='unknown';text=`Investigate ${o.order_id} with warehouse and support; do not promise a dispatch date.`;
    }
    const value=Number(o.order_value),quantity=Number(o.quantity);
    if(!Number.isFinite(value)||value<0||!Number.isInteger(quantity)||quantity<0)throw new Error('Invalid sample amount or quantity.');
    cents+=Math.round(value*100);units+=quantity;
    findings.push({order_id:o.order_id,customer:o.customer,sku:o.sku,value,explanation,certainty,citations});
    actions.push({id:'action-'+o.order_id,order_id:o.order_id,text,status:'draft',citations,external_action:false});
  }
  const allowed=new Set(evidence.map(e=>e.citation));
  if(findings.some(f=>f.citations.some(c=>!allowed.has(c))))throw new Error('Citation verification failed.');
  const result={id,question,scope,data_mode:'browser-sample',model_mode:'sample',metrics:{orders_reviewed:orders.length,delayed_orders:findings.length,order_value_at_risk:cents/100,units_affected:units,currency:'USD',value_definition:'Sum of delayed order values; exposure, not forecast loss.'},findings,actions,evidence,
    narrative:{text:'Computed in your browser from fictional datasets. No LLM or Zetaris calls.',usage:{}},
    warnings:['Public sample demo: browser computation and local history only. Live Zetaris/model integration runs in the Python app.'],
    duration_ms:Math.round(performance.now()-start),engine:'Browser sample of minimal Meterless World Model pattern'};
  if(!orders.length)result.warnings.push('No matching orders; no conclusion can be drawn.');
  if(matches.length>200)result.warnings.push('Context truncated to 200 orders; totals apply only to selected rows.');
  const event=(agent,kind,payload)=>({run_id:id,at:new Date().toISOString(),agent,kind,payload});
  result.trace=[event('planner','plan.created',{scope,max_model_calls:0}),event('collector','world.ingested',{mode:'browser-sample',counts:Object.fromEntries(Object.entries(world).map(([k,v])=>[k,v.length])),schema_version:1}),event('context-builder','context.selected',{scope,citations:evidence.map(e=>e.citation)}),event('verifier','findings.verified',{findings:findings.length,citations:evidence.length,method:'exact sample evidence identifiers'}),event('orchestrator','run.completed',{duration_ms:result.duration_ms})];
  return result;
}

let sampleSources;
const key='traceops-browser-sample-v1';
function loadRuns(){try{return JSON.parse(localStorage.getItem(key)||'[]');}catch{return [];}}
export async function browserAPI(path,options){
  if(path==='/api/status')return {data_mode:'browser-sample',model_mode:'sample'};
  if(path==='/api/runs')return loadRuns().map(({id,created_at,question,status})=>({id,created_at,question,status}));
  if(path.startsWith('/api/runs/'))return loadRuns().find(r=>r.id===path.split('/')[3]);
  if(path==='/api/investigate') {
    if(!sampleSources){const response=await fetch('./sample-data.json');if(!response.ok)throw new Error('Cannot load sample datasets.');sampleSources=await response.json();}
    const result=await investigateSample(sampleSources,JSON.parse(options.body).question);
    const rows=loadRuns();rows.unshift({id:result.id,created_at:new Date().toISOString(),question:result.question,status:'complete',result});
    try{localStorage.setItem(key,JSON.stringify(rows.slice(0,30)));}catch{result.warnings.push('Browser storage unavailable; history may not persist.');}
    return result;
  }
  throw new Error('This operation requires the Python runtime.');
}
