# M5 decision replay (simulated)

Each row is one bounded control step with recorded inputs, actions and outcome.

| step | correlation_id | forecast_source | current_workload | forecast_workload | forecast_peak | plan_strategy | plan_code | ppo_action | shield_proposed | shield_allowed | shield_codes | final_action | action_code | guard_code | p95_latency_ms | sla_violated | cold_starts | energy_w | capacity | reward |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | full-0000-138a6965d1ec | tft | 667.5162539880263 | 445.09632857157453 | 470.9257712289557 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 2 | full-0001-aafc1a5b127b | tft | 658.7584050436617 | 445.1014995802523 | 470.9118010284623 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 3 | full-0002-ab70657ab8c1 | tft | 662.9239065498964 | 445.10144871787185 | 470.9118349367159 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 4 | full-0003-6269921e8259 | tft | 669.90251579322 | 445.10144871787185 | 470.9118179825891 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 5 | full-0004-774c15879cd7 | tft | 655.0379815819912 | 445.1015165343791 | 470.9118010284623 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 6 | full-0005-9541049caed4 | tft | 634.3970850863701 | 445.10143176374504 | 470.91185189084274 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 166.4 | False | 0.0 | 35.0 | 2 | -0.6231111111111111 |
| 7 | full-0006-02d914213adf | tft | 667.3618172689486 | 445.10133003898414 | 470.9120044779841 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 8 | full-0007-31ceaaf671c5 | tft | 662.8016441472931 | 445.10153348850594 | 470.91190275322316 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 9 | full-0008-e655f6f8a829 | tft | 631.4531351289514 | 445.1015165343791 | 470.91188579909635 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 166.4 | False | 0.0 | 35.0 | 2 | -0.6231111111111111 |
| 10 | full-0009-e478187c169a | tft | 636.5452569496523 | 445.101346993111 | 470.9120553403645 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 166.4 | False | 0.0 | 35.0 | 2 | -0.6231111111111111 |
| 11 | full-0010-595c56973d95 | tft | 674.3339916489773 | 445.1014148096183 | 470.9121062027449 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 12 | full-0011-1ac90b2ed639 | tft | 674.7779972163257 | 445.10158435088636 | 470.91193666147683 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 13 | full-0012-e2593eaed289 | tft | 666.6775768052571 | 445.10156739675955 | 470.91185189084274 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 14 | full-0013-6c6f0d25987a | tft | 656.4225496676114 | 445.1014995802523 | 470.91185189084274 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 15 | full-0014-b891691fd7db | tft | 659.7407941733504 | 445.10143176374504 | 470.9118688449696 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 16 | full-0015-c8c76255430f | tft | 652.3589334968794 | 445.10144871787185 | 470.91188579909635 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 17 | full-0016-5d785d5fffe4 | tft | 623.844981759943 | 445.1014148096183 | 470.91193666147683 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 166.4 | False | 0.0 | 35.0 | 2 | -0.6231111111111111 |
| 18 | full-0017-622f9572cce2 | tft | 633.0189518640448 | 445.1012622224769 | 470.9121401109985 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 166.4 | False | 0.0 | 35.0 | 2 | -0.6231111111111111 |
| 19 | full-0018-fc88e324bc7d | tft | 616.7580523178218 | 445.10138090136456 | 470.9121570651253 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 166.4 | False | 0.0 | 35.0 | 2 | -0.6231111111111111 |
| 20 | full-0019-c0d35f3facbd | tft | 620.9750327304157 | 445.10131308485734 | 470.9123266063935 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 166.4 | False | 0.0 | 35.0 | 2 | -0.6231111111111111 |
| 21 | full-0020-cbafe45c83af | tft | 652.0554224448031 | 445.1013978554914 | 470.9123774687739 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 176.8 | False | 0.0 | 35.0 | 2 | -0.6551111111111111 |
| 22 | full-0021-934fe99e6779 | tft | 611.9587167770391 | 445.10155044263274 | 470.9122079275058 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 166.4 | False | 0.0 | 35.0 | 2 | -0.6231111111111111 |
| 23 | full-0022-c24b5a2a5641 | tft | 604.6980460259555 | 445.10131308485734 | 470.9124113770275 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 166.4 | False | 0.0 | 35.0 | 2 | -0.6231111111111111 |
| 24 | full-0023-9c46bc127002 | tft | 622.8186210644058 | 445.10131308485734 | 470.91254701004203 | NoOp | ok | PreWarm | PreWarm | True | ok | PreWarm | ok | ok | 166.4 | False | 0.0 | 35.0 | 2 | -0.6231111111111111 |
