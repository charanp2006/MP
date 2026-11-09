from __future__ import annotations
import argparse,json,os
from configs import load_config
from data.pipeline import run
from rl.environment import ServerlessEnv
from rl.train_ppo import load_checkpoint as load_ppo
from orchestrator.decision_loop import run_episode
def main():
 p=argparse.ArgumentParser(); p.add_argument("--config",default=None); p.add_argument("--steps",type=int,default=50); p.add_argument("--use-tft",action="store_true"); p.add_argument("--runtime",choices=["stub","ollama"],default=None); p.add_argument("--out",default="results/proposed.json"); a=p.parse_args()
 config=load_config(a.config)
 if a.runtime: config.setdefault("agent",{})["runtime"]=a.runtime
 frame,_=run(config=config); env=ServerlessEnv(frame,config); policy=None
 ck=config["control"]["rl"].get("checkpoint_path","models/ppo_policy.pt")
 if os.path.exists(ck):
  try: policy=load_ppo(ck)
  except Exception: policy=None
 records=run_episode(env,config,policy=policy,steps=a.steps,use_tft=a.use_tft)
 summary={"mode":"simulation","steps":len(records),"forecast_sources":sorted(set(r.get("forecast_source") for r in records)),"planner_runtime":config.get("agent",{}).get("runtime","stub"),"records_tail":records[-3:] if records else []}
 os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); json.dump({"summary":summary,"records":records}, open(a.out,"w",encoding="utf-8"), indent=2, default=str)
 print(json.dumps(summary, indent=2, default=str))
if __name__=="__main__": main()
