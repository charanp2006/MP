from __future__ import annotations
import subprocess,sys,json,os
def run(cmd): print("+",sys.executable,*cmd); return subprocess.run([sys.executable]+cmd).returncode
def main():
 os.makedirs("results", exist_ok=True)
 print("SIMULATION MODE (default). Live cluster/Prometheus/Grafana/Ollama require explicit setup + flags.")
 codes=[run(["-m","scripts.run_baseline"]), run(["-m","scripts.run_proposed_system","--steps","30","--use-tft"]), run(["-m","scripts.collect_results"]), run(["-m","scripts.plot_results"])]
 print(json.dumps({"mode":"simulation","exit_codes":codes}, indent=2))
if __name__=="__main__": main()
