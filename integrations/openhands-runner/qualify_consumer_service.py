"""Disposable systemd lifecycle qualification; never installs a production unit."""
import json
from pathlib import Path
import subprocess
import time
import uuid


def run_service(config_file,*,on_report):
    config=json.loads(Path(config_file).read_text())
    unit='oria-hq-qualification-'+uuid.uuid4().hex+'.service'
    runtime=Path('/run')/unit.removesuffix('.service')
    def command(*args,check=True):
        return subprocess.run(args,capture_output=True,text=True,timeout=120,check=check)
    def state():
        data=command('systemctl','show',unit,'--property=ActiveState,SubState,ExecMainStatus,Restart,NoNewPrivileges,ProtectSystem,PrivateTmp').stdout
        return dict(line.split('=',1) for line in data.splitlines() if '=' in line)
    def wait_for(predicate,seconds=90):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            observed=state()
            if predicate(observed):return observed
            time.sleep(.25)
        raise RuntimeError('Service state not observed before qualification deadline')
    properties=['User=root','UMask=0077','Restart=no','KillMode=mixed','TimeoutStopSec=2100',
                'NoNewPrivileges=yes','PrivateTmp=yes','ProtectSystem=strict',
                'RuntimeDirectory='+runtime.name,'RuntimeDirectoryMode=0755','RuntimeDirectoryPreserve=yes',
                'ReadWritePaths='+' '.join(str(config[k]) for k in ('hostConfigRoot','jobsRoot','controlRoot'))]
    try:
        argv=['systemd-run','--quiet','--unit='+unit,'--property=Type=simple']
        for prop in properties:argv+=['--property='+prop]
        argv+=['/usr/bin/python3',str(Path(__file__).with_name('consume_pending.py')),'--config',str(config_file),'--watch']
        command(*argv)
        failed=wait_for(lambda s:s.get('ActiveState')=='failed')
        assert runtime.is_dir() and runtime.stat().st_mode&0o777==0o755
        journal=command('journalctl','--unit='+unit,'--output=cat','--no-pager').stdout
        reports=[]
        for line in journal.splitlines():
            if line.startswith('{'):
                value=json.loads(line)
                if 'outcome' in value:reports.append(value)
        if len(reports)!=1:raise AssertionError('Expected one retained execution report')
        report=reports[0];on_report(report)
        assert failed['ExecMainStatus']=='3',failed
        assert failed['Restart']=='no' and failed['NoNewPrivileges']=='yes' and failed['ProtectSystem']=='strict' and failed['PrivateTmp']=='yes',failed
        # A finished canonical claim must not be replayed after service restart.
        command('systemctl','restart',unit)
        wait_for(lambda s:s.get('ActiveState')=='active',10)
        started=time.monotonic();time.sleep(7)
        assert state()['ActiveState']=='active'
        contender=command('/usr/bin/python3',str(Path(__file__).with_name('consume_pending.py')),'--config',str(config_file),check=False)
        assert contender.returncode==2,'Second consumer acquired the same host root'
        command('systemctl','stop',unit)
        stopped=wait_for(lambda s:s.get('ActiveState')=='inactive',10)
        assert stopped['ExecMainStatus']=='0',stopped
        assert runtime.is_dir(),'Runtime directory unexpectedly removed on stop'
        journal=command('journalctl','--unit='+unit,'--output=cat','--no-pager').stdout
        assert sum(line.startswith('{') and '"outcome"' in line for line in journal.splitlines())==1,'Service replayed a completed job'
        print(json.dumps({'actualSystemdConsumer':True,'failureVisible':True,'restartNoReplay':True,
                          'secondConsumerRefused':True,'idleWatchSeconds':round(time.monotonic()-started,2),'gracefulIdleStop':True}))
        return report
    finally:
        command('systemctl','stop',unit,check=False)
        command('systemctl','reset-failed',unit,check=False)
        if runtime.exists():runtime.rmdir()
