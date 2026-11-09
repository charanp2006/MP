from __future__ import annotations
import json,os
def main():
 try: import matplotlib.pyplot as plt
 except Exception as e: print(f"matplotlib not available: {e}. Skipping plots."); return
 os.makedirs("results/plots", exist_ok=True)
 bpath="results/baseline.json"; ppath="results/proposed.json"
 if os.path.exists(bpath) and os.path.exists(ppath):
  b=json.load(open(bpath)); p=json.load(open(ppath)); bm=b.get("metrics",{}); recs=p.get("records",[])
  pm={}
  if recs:
   lat=[r["info"].get("p95_latency",0) for r in recs]; en=[r["info"].get("energy",0) for r in recs]; sla=[1 if r["info"].get("sla_violated") else 0 for r in recs]
   pm={"mean_p95_latency_ms":sum(lat)/len(lat),"mean_energy_w":sum(en)/len(en),"sla_violation_rate":sum(sla)/len(sla)}
  keys=["mean_p95_latency_ms","mean_energy_w","sla_violation_rate"]; labels=[k for k in keys if k in bm and k in pm]
  if labels:
   fig,ax=plt.subplots(); x=list(range(len(labels)))
   ax.bar([i-0.2 for i in x],[bm[k] for k in labels],width=0.4,label="baseline"); ax.bar([i+0.2 for i in x],[pm[k] for k in labels],width=0.4,label="proposed(sim)")
   ax.set_xticks(x); ax.set_xticklabels(labels,rotation=20); ax.legend(); fig.tight_layout(); fig.savefig("results/plots/comparison.png"); plt.close(fig); print("wrote results/plots/comparison.png")
if __name__=="__main__": main()
