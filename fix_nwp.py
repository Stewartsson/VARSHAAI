import sys
with open('backend/app/ml/nwp_ml_service.py', 'r') as f:
    lines = f.readlines()
with open('backend/app/ml/nwp_ml_service.py', 'w') as f:
    skip = False
    for line in lines:
        if 'All NWP forecast sources failed' in line:
            f.write('    raise RuntimeError("All NWP forecast sources failed or rate limited.")\n')
            skip = True
        elif skip and '# HEM HISTORICAL DATA' in line:
            skip = False
            f.write('# ============================================================\n')
            f.write(line)
        elif not skip:
            f.write(line)
