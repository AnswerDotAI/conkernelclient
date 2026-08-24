"""Race-condition regression tests: adversarial timing on the shell send path.

`LockedSendChannel` serializes shell sends under a lock with a random 10-15ms sleep,
widening the window between the sync zmq send path and the async receive side. The burst
test then keeps many replies pending at once, so the background reader races every send.
The parked-recv test is the minimal repro of the edge-triggered FD bug the Session patch
fixes: a recv parked in poll(None) must still wake after a sync send consumes the FD edge.
"""
import asyncio, functools, random, threading, time
from queue import Empty

from jupyter_client import AsyncKernelManager
from jupyter_client.channels import AsyncZMQSocketChannel
from traitlets import Type

from conkernelclient import ConKernelClient, ConKernelManager
from conkernelclient.core import apply_session_patch
from conkernelclient.ops import run_kernel


def locked_sleep(f):
    @functools.wraps(f)
    def _f(self, *args, **kwargs):
        with self.lock:
            time.sleep(random.uniform(0.01, 0.015))
            return f(self, *args, **kwargs)
    return _f

class LockedSendChannel(AsyncZMQSocketChannel):
    lock = threading.RLock()
    @locked_sleep
    def send(self, msg): return super().send(msg)

class LockedClient(ConKernelClient):
    shell_channel_class = LockedSendChannel

class LockedKernelManager(ConKernelManager):
    client_class,client_factory = LockedClient,Type(LockedClient)

def test_burst_replies_under_send_jitter():
    "20 pending replies at once, every send jittered: the reader must route each reply to its waiter."
    async def _run():
        async with run_kernel("ipymini", ["ipymini", "-f", "{connection_file}"], manager_cls=LockedKernelManager) as (km, kc):
            reps = [kc.reply(f"x{i} = {i}; x{i}", timeout=30) for i in range(20)]
            for i, r in enumerate(await asyncio.gather(*reps)): assert r["content"]["status"] == "ok", (i, r["content"])
    asyncio.run(_run())


def test_parked_recv_survives_sync_send():
    "A recv parked in poll(None) must wake with the right reply after sync sends while the loop was busy."
    async def _run():
        apply_session_patch()
        km = AsyncKernelManager()
        await km.start_kernel()
        kc = km.client()
        kc.start_channels()
        await kc.wait_for_ready()
        try:
            # Drain replies to any extra kernel_info requests from a slow start,
            # so the parked recv below can only receive the execute reply.
            try:
                while True: await kc.get_shell_msg(timeout=0.3)
            except Empty: pass

            fut = asyncio.create_task(kc.get_shell_msg(timeout=None))
            await asyncio.sleep(0.1)
            mid = kc.execute("1+1")  # loop busy below, so the reply buffers and sets the FD edge
            time.sleep(0.4)
            kc.execute("2+2")  # sync send consumes the edge via process_commands
            reply = await asyncio.wait_for(fut, 3)  # TimeoutError here is the regression
            assert reply["parent_header"]["msg_id"] == mid
        finally:
            kc.stop_channels()
            await km.shutdown_kernel(now=True)
    asyncio.run(_run())
