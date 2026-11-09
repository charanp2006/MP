from __future__ import annotations
import argparse,json
from configs import load_config
from data.pipeline import run
from rl.train_ppo import train_ppo, save_checkpoint
def main():
 p=argparse.ArgumentParser(); p.add_argument("--config",default=None); p.add_argument("--episodes",type=int,default=None); p.add_argument("--verbose",action="store_true"); a=p.parse_args()
 config=load_config(a.config)
 if a.episodes is not None: config["control"]["rl"]["training"]["episodes"]=a.episodes
 frame,_=run(config=config); model,env,history=train_ppo(frame,config=config,verbose=a.verbose)
 ck=config["control"]["rl"].get("checkpoint_path","models/ppo_policy.pt"); save_checkpoint(model,ck,env.observation_size,env.n_actions)
 print(json.dumps({"checkpoint":ck,"best_mean_reward":history["best_mean_reward"]}, indent=2, default=str))
if __name__=="__main__": main()
