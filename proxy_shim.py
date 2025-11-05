#!/usr/bin/env python3
import asyncio, base64, os, sys
from urllib.parse import urlparse, unquote

UP = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
if not UP:
    print("ERROR: Set HTTPS_PROXY or HTTP_PROXY with credentials (http://user:pass@host:port).", file=sys.stderr); sys.exit(1)
p = urlparse(UP)
if not (p.hostname and p.port and p.username and p.password):
    print("ERROR: Proxy URL must include host, port, username, and password.", file=sys.stderr); sys.exit(1)

UP_HOST, UP_PORT = p.hostname, p.port
UP_AUTH = base64.b64encode(f"{unquote(p.username)}:{unquote(p.password)}".encode()).decode()

LISTEN = os.environ.get("PROXY_SHIM_LISTEN", "127.0.0.1:15080")
LHOST, LPORT = LISTEN.split(":")[0], int(LISTEN.split(":")[1])

HDR_END = b"\r\n\r\n"
CRLF = b"\r\n"

async def pipe(src, dst):
    try:
        while True:
            data = await src.read(65536)
            if not data: break
            dst.write(data); await dst.drain()
    except Exception:
        pass
    finally:
        try: dst.write_eof()
        except Exception: pass

def inject_header(block: bytes, name: bytes, value: bytes) -> bytes:
    # Insert header after request line
    head, sep, rest = block.partition(CRLF)
    return head + CRLF + name + b": " + value + CRLF + rest

async def handle(reader, writer):
    try:
        # Read client request head (start-line + headers)
        data = b""
        while HDR_END not in data and len(data) < 65536:
            chunk = await reader.read(4096)
            if not chunk: break
            data += chunk
        if not data: writer.close(); await writer.wait_closed(); return

        # Parse request line
        line, _, headers = data.partition(CRLF)
        parts = line.decode(errors="ignore").split()
        method = parts[0] if parts else ""
        # CONNECT handling (HTTPS tunneling)
        if method == "CONNECT":
            target = parts[1] if len(parts) > 1 else ""
            # Open upstream proxy
            upr, upw = await asyncio.open_connection(UP_HOST, UP_PORT)
            # Send CONNECT with both Proxy-Authorization and Authorization to placate 401-style proxies.
            # (For CONNECT, these headers are consumed by the proxy and not forwarded to origin.)
            req = (f"CONNECT {target} HTTP/1.1\r\n"
                   f"Host: {target}\r\n"
                   f"Proxy-Authorization: Basic {UP_AUTH}\r\n"
                   f"Authorization: Basic {UP_AUTH}\r\n"
                   f"Proxy-Connection: keep-alive\r\n\r\n").encode()
            upw.write(req); await upw.drain()

            # Read upstream response head
            up_resp = b""
            while HDR_END not in up_resp and len(up_resp) < 65536:
                chunk = await upr.read(4096)
                if not chunk: break
                up_resp += chunk
            status = up_resp.split(b"\r\n",1)[0] if up_resp else b""
            ok = status.startswith(b"HTTP/1.1 200") or status.startswith(b"HTTP/1.0 200")
            if not ok:
                # surface upstream response to client for debugging
                writer.write(up_resp or b"HTTP/1.1 502 Bad Gateway\r\n\r\n"); await writer.drain()
                writer.close(); upw.close();
                try: await upw.wait_closed(); await writer.wait_closed()
                except Exception: pass
                return

            # Tell client the tunnel is up
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n"); await writer.drain()
            # Now tunnel bytes both ways
            await asyncio.gather(pipe(reader, upw), pipe(upr, writer))
            upw.close(); writer.close()
            try: await upw.wait_closed(); await writer.wait_closed()
            except Exception: pass
            return

        # Plain HTTP over proxy (Java sends absolute-form request line)
        # Ensure Proxy-Authorization is present; DO NOT add Authorization here to avoid leaking creds to origin.
        if b"\nProxy-Authorization:" not in headers:
            data = inject_header(data, b"Proxy-Authorization", f"Basic {UP_AUTH}".encode())

        # Open upstream proxy and forward the modified head plus any buffered tail
        upr, upw = await asyncio.open_connection(UP_HOST, UP_PORT)
        upw.write(data); await upw.drain()

        # Stream remaining body (if any) and responses
        await asyncio.gather(pipe(reader, upw), pipe(upr, writer))
        upw.close(); writer.close()
        try: await upw.wait_closed(); await writer.wait_closed()
        except Exception: pass
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        try: writer.close(); await writer.wait_closed()
        except Exception: pass

async def main():
    srv = await asyncio.start_server(handle, LHOST, LPORT)
    print(f"[proxy-shim] listening on {LHOST}:{LPORT} → upstream {UP_HOST}:{UP_PORT} (creds from HTTPS_PROXY/HTTP_PROXY)")
    async with srv: await srv.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
