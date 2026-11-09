from __future__ import annotations
import argparse,json
from configs import load_config
from data.pipeline import run
from forecasting.train import train_tft, save_checkpoint
def main():
 p=argparse.ArgumentParser(); p.add_argument("--config",default=None); p.add_argument("--epochs",type=int,default=None); p.add_argument("--verbose",action="store_true"); a=p.parse_args()
 config=load_config(a.config)
 if a.epochs is not None: config["forecast"]["training"]["epochs"]=a.epochs
 frame,_=run(config=config); model,data,history=train_tft(frame,config=config,verbose=a.verbose)
 ck=config["forecast"].get("checkpoint_path","models/tft_checkpoint.pt"); save_checkpoint(model,data,ck,config["forecast"]["model"])
 print(json.dumps({"checkpoint":ck,"history":history}, indent=2, default=str))
if __name__=="__main__": main()
