from statapy.stata_runner import StataRunner
runner = StataRunner()
do = '''
clear all
set more off
capture findfile mpdta.dta
if _rc==0 {
    display "FOUND " r(fn)
}
else {
    display "NOT_FOUND"
}
'''
res = runner.run_do_file(do, output_dir='stata/output', timeout=60)
with open('stata/output/find_mpdta.log', 'w', encoding='utf-8') as f:
    f.write('OUTPUT:\n')
    f.write(str(res.output_content) or '')
    f.write('\nERR:\n')
    f.write(str(res.error_message) or '')
print('done')
