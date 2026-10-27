#!/usr/bin/env python3
"""Report connection readiness without printing secrets or calling providers by default."""
import argparse,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import load_env
from traceops.connectors import ZetarisConnector,ConnectorError
from traceops.agent import LiveGenerator

if __name__=='__main__':
 load_env()
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--live',action='store_true',help='Make real read-only Zetaris calls and one model request using fictional findings')
 args=parser.parse_args()
 requirements={'zetaris':['ZETARIS_BASE_URL','ZETARIS_ORG_ID','ZETARIS_API_KEY'],'model':['MODEL_BASE_URL','MODEL_API_KEY','MODEL_NAME']}
 report={}
 for service,names in requirements.items():
  missing=[name for name in names if not os.getenv(name)]
  report[service]={'configured':not missing,'missing_variables':missing,'live_verified':False}
 if args.live:
  if report['zetaris']['configured']:
   try:
    sources=ZetarisConnector().fetch()
    report['zetaris'].update(live_verified=True,rows={k:len(v) for k,v in sources.items()})
   except (ConnectorError,ValueError) as e:report['zetaris']['error']=str(e)
  if report['model']['configured']:
   try:
    output=LiveGenerator().generate({'scope':{'order_id':'ORD-TEST'}},[{'explanation':'Fictional test order is delayed.','citations':['0'*24]}])
    report['model'].update(live_verified=True,model=output.get('model'),usage=output.get('usage'))
   except (ConnectorError,ValueError) as e:report['model']['error']=str(e)
 print(json.dumps(report,indent=2))
 raise SystemExit(0 if all(s['live_verified'] if args.live else s['configured'] for s in report.values()) else 2)
