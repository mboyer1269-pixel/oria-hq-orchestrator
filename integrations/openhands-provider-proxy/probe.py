"""Real socket/TLS qualification. No account, credential, HTTP payload or model call."""
import json
import socket
import ssl
import subprocess
import time


def connect_line(target, method='CONNECT', *, local_relay=False):
    if local_relay:
        stream=socket.create_connection(('127.0.0.1',3129),timeout=15)
    else:
        stream=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        stream.settimeout(15)
        stream.connect('/provider/provider.sock')
    stream.sendall(f'{method} {target} HTTP/1.1\r\nHost: {target}\r\n\r\n'.encode('ascii'))
    header=bytearray()
    while not header.endswith(b'\r\n\r\n'):
        chunk=stream.recv(1)
        if not chunk or len(header)>16384:
            stream.close();raise RuntimeError('Invalid proxy response')
        header.extend(chunk)
    return stream,header.split(b'\r\n',1)[0].decode('ascii')


def main():
    results=[]
    for target,method in [('example.com:443','CONNECT'),('127.0.0.1:443','CONNECT'),
                          ('169.254.169.254:443','CONNECT'),('api.anthropic.com:80','CONNECT'),
                          ('api.anthropic.com.evil.example:443','CONNECT'),
                          ('http://api.anthropic.com/','GET')]:
        stream,line=connect_line(target,method)
        stream.close()
        assert ' 403 ' in line,(target,line)
        results.append({'case':target,'method':method,'denied':True})
    # No HTTP request is sent through this authorized TLS tunnel.
    for hostname in ('api.anthropic.com','claude.ai','claude.com','platform.claude.com'):
        start=time.monotonic()
        stream,line=connect_line(hostname+':443')
        assert ' 200 ' in line,line
        with ssl.create_default_context().wrap_socket(stream,server_hostname=hostname) as tls:
            assert tls.getpeercert()
            protocol=tls.version()
        results.append({'case':'allowed-provider-tls','host':hostname,'verified':True,'protocol':protocol,
                        'elapsedMs':round((time.monotonic()-start)*1000)})
    for target in ('1.1.1.1','169.254.169.254'):
        try:
            with socket.create_connection((target,443),timeout=2):pass
        except OSError:
            results.append({'case':'direct-'+target,'blocked':True})
        else:raise AssertionError('Direct network unexpectedly available')
    relay=subprocess.Popen(['node','/relay.mjs'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    try:
        for _ in range(40):
            if relay.poll() is not None:raise AssertionError('Relay exited before readiness')
            try:
                with socket.create_connection(('127.0.0.1',3129),timeout=0.1):pass
                break
            except OSError:time.sleep(0.1)
        else:raise AssertionError('Relay unavailable')
        stream,line=connect_line('api.anthropic.com:443',local_relay=True)
        assert ' 200 ' in line,line
        with ssl.create_default_context().wrap_socket(stream,server_hostname='api.anthropic.com') as tls:
            assert tls.getpeercert()
        stream,line=connect_line('example.com:443',local_relay=True);stream.close()
        assert ' 403 ' in line,line
        results.append({'case':'cli-loopback-relay','allowedTlsVerified':True,'foreignHostDenied':True})
    finally:
        relay.terminate()
        try:relay.wait(timeout=3)
        except subprocess.TimeoutExpired:relay.kill();relay.wait(timeout=3)
    print(json.dumps({'passed':True,'checks':results,'modelRequests':0}))


if __name__=='__main__':main()
