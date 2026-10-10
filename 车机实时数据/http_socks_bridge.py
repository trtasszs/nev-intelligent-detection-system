# -*- coding: utf-8 -*-
"""
本地 HTTP CONNECT 代理 -> 转发到 SOCKS5 代理
==================================================================
为什么需要它：
  · git 给 GitHub 配的代理是 socks5h://127.0.0.1:10808，git 自己能用；
  · 但认证由 Git Credential Manager（.NET）负责，而 .NET 的
    ServicePointManager **不支持 socks5 方案**，于是报
    「不支持具有 socks5h 方案的代理」而拿不到凭据。
  · 直连 github.com 又被 RST（墙）。
  所以在本机开一个**标准 HTTP 代理**，它把 CONNECT 转给 socks5，
  GCM 看到的就是普通 HTTP 代理，认证就能走下去。

用法： python http_socks_bridge.py [监听端口] [socks端口]
      默认 18080 / 10808
"""
import select
import socket
import struct
import sys
import threading

LISTEN_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 18080
SOCKS_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 10808
SOCKS_HOST = '127.0.0.1'


def log(*a):
    # 控制台可能是 GBK：任何非 ASCII 字符都会让 print 抛异常，
    # 而异常发生在处理线程里会直接掐断连接 —— 所以这里必须兜住。
    try:
        print(*a, flush=True)
    except Exception:
        try:
            print((' '.join(str(x) for x in a)).encode('ascii', 'replace').decode('ascii'), flush=True)
        except Exception:
            pass


def socks5_connect(host, port, timeout=20):
    """按 SOCKS5 协议连到目标，返回已连通的 socket。"""
    s = socket.create_connection((SOCKS_HOST, SOCKS_PORT), timeout=timeout)
    s.settimeout(timeout)
    # 握手：只支持无认证
    s.sendall(b'\x05\x01\x00')
    resp = s.recv(2)
    if len(resp) < 2 or resp[0] != 0x05 or resp[1] != 0x00:
        s.close()
        raise OSError('SOCKS5 握手失败: %r' % (resp,))
    # CONNECT 请求：用域名（等价于 socks5h，由代理解析 DNS）
    h = host.encode('idna') if any(ord(c) > 127 for c in host) else host.encode()
    req = b'\x05\x01\x00\x03' + bytes([len(h)]) + h + struct.pack('!H', port)
    s.sendall(req)
    head = s.recv(4)
    if len(head) < 4 or head[0] != 0x05 or head[1] != 0x00:
        s.close()
        raise OSError('SOCKS5 CONNECT 被拒: %r' % (head,))
    atyp = head[3]
    if atyp == 0x01:
        s.recv(4)
    elif atyp == 0x03:
        n = s.recv(1)
        s.recv(n[0] if n else 0)
    elif atyp == 0x04:
        s.recv(16)
    s.recv(2)  # 端口
    s.settimeout(None)
    return s


def pipe(a, b):
    try:
        while True:
            r, _, _ = select.select([a, b], [], [], 60)
            if not r:
                break
            for s in r:
                data = s.recv(65536)
                if not data:
                    return
                (b if s is a else a).sendall(data)
    except Exception:
        pass
    finally:
        for s in (a, b):
            try:
                s.close()
            except Exception:
                pass


def handle(conn, addr):
    try:
        conn.settimeout(20)
        buf = b''
        while b'\r\n\r\n' not in buf:
            chunk = conn.recv(4096)
            if not chunk:
                return
            buf += chunk
            if len(buf) > 65536:
                return
        line = buf.split(b'\r\n', 1)[0].decode('latin-1')
        parts = line.split()
        if len(parts) < 2 or parts[0].upper() != 'CONNECT':
            conn.sendall(b'HTTP/1.1 405 Method Not Allowed\r\n\r\n')
            return
        target = parts[1]
        if ':' in target:
            host, port = target.rsplit(':', 1)
            port = int(port)
        else:
            host, port = target, 443
        upstream = socks5_connect(host, port)
        conn.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        conn.settimeout(None)
        log('  CONNECT %s:%d  ✓' % (host, port))
        pipe(conn, upstream)
    except Exception as e:
        log('  ✗ %s: %s' % (addr, e))
        try:
            conn.sendall(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', LISTEN_PORT))
    srv.listen(64)
    log('HTTP->SOCKS5 桥已启动: 127.0.0.1:%d  ->  socks5://%s:%d' % (LISTEN_PORT, SOCKS_HOST, SOCKS_PORT))
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == '__main__':
    main()
