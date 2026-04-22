from stataflow.stata_runner import StataRunner
import os

runner = StataRunner()
do = '''
clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/panel/wooldridge/wagepan.csv", clear
areg lwage educ exper expersq union, absorb(nr)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

matrix list e(b)

exit
'''
result = runner.run_do_file(do, output_dir='stata/output')
with open('stata/output/wagepan_meta.txt', 'w', encoding='utf-8') as f:
    f.write(f'exit_code: {result.exit_code}\n')
    f.write(f'log_file: {result.log_file}\n')
    f.write(f'error: {repr(result.error_message)}\n')

if result.log_file and os.path.exists(result.log_file):
    with open(result.log_file, 'r', encoding='utf-8', errors='replace') as f:
        txt = f.read()
    with open('stata/output/wagepan_log.txt', 'w', encoding='utf-8') as out:
        out.write(txt)
else:
    logs = [f for f in os.listdir('stata/output') if f.endswith('.log')]
    latest = sorted(logs, key=lambda f: os.path.getmtime('stata/output/' + f))[-1]
    with open('stata/output/' + latest, 'r', encoding='utf-8', errors='replace') as f:
        txt = f.read()
    with open('stata/output/wagepan_log.txt', 'w', encoding='utf-8') as out:
        out.write(txt)
