from __future__ import annotations
import argparse,json,os
from configs import load_config
from data.pipeline import run
from rl.evaluate_ppo import evaluate_reactive
def main():
 p=argparse.ArgumentParser(); p.add_argument("--config",default=None); p.add_argument("--out",default="results/baseline.json"); a=p.parse_args()
 config=load_config(a.config); frame,report=run(config=config); metrics=evaluate_reactive(frame,config)
 os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); json.dump({"mode":"simulation","metrics":metrics,"data_report":report}, open(a.out,"w",encoding="utf-8"), indent=2, default=str); print(json.dumps(metrics, indent=2))
if __name__=="__main__": main()
