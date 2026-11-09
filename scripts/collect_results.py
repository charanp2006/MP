from __future__ import annotations
import json,glob,os
def main():
 files=sorted(glob.glob("results/*.json")); out={}
 for fp in files:
  try: out[os.path.basename(fp)]=json.load(open(fp,"r",encoding="utf-8"))
  except Exception as e: out[os.path.basename(fp)]={"error":str(e)}
 os.makedirs("results",exist_ok=True); json.dump(out, open("results/collected.json","w",encoding="utf-8"), indent=2, default=str)
 print(json.dumps({"collected":list(out.keys())}, indent=2))
if __name__=="__main__": main()
