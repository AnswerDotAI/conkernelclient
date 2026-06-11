import asyncio, time, sys
from jupyter_client import AsyncKernelManager
import conkernelclient.core

async def main():
    km = AsyncKernelManager()
    await km.start_kernel()
    kc = km.client()
    kc.start_channels()
    await kc.wait_for_ready()

    # 1. Park the recv first, so it's actually waiting in poll(None)
    fut = asyncio.create_task(kc.get_shell_msg(timeout=None))
    await asyncio.sleep(0.1)

    # 2. Send A; loop is frozen, so the reply buffers and sets the FD edge
    mid = kc.execute('1+1')
    time.sleep(0.4)

    # 3. Sync send B consumes the edge via process_commands
    kc.execute('2+2')

    # 4. With getsockopt: parked poll never wakes → watchdog fires
    try: reply = await asyncio.wait_for(fut, 3)
    except asyncio.TimeoutError:
        print("FAIL: shell recv hung (edge consumed without reschedule)")
        kc.stop_channels(); await km.shutdown_kernel(now=True)
        return 1

    ok = reply['parent_header']['msg_id'] == mid
    print("PASS" if ok else f"FAIL: got {reply['parent_header']['msg_id']}, wanted {mid}")
    kc.stop_channels()
    await km.shutdown_kernel(now=True)
    return 0 if ok else 1

if __name__ == '__main__': sys.exit(asyncio.run(main()))
