# Postprocessing scripts for perf data
## Installation

```shell
# prettytable, paramiko, scp, matplotlib, pandas package is required
pip3 install prettytable pandas
```

## perfeventdumper.py

```console
python3 perfeventdumper.py -d ../SampleData/ -t 1630.5154 1635.5154
Display all events from sched_switch and irq within timeframe from 1630.5154 to 1635.5154.
Files are used from ../SampleData
```