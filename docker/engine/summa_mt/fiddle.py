#!/usr/bin/env python

import asyncio
import signal


async def pending_doom():
    await asyncio.sleep(2)
    print(">> Cancelling tasks now")
    for task in asyncio.Task.all_tasks():
        task.cancel()

    print(">> Done cancelling tasks")
    asyncio.get_event_loop().stop()


def ask_exit():
    for task in asyncio.Task.all_tasks():
        task.cancel()


async def looping_coro():
    print("Executing coroutine")
    while True:
        try:
            await asyncio.sleep(0.25)
        except asyncio.CancelledError:
            print("Got CancelledError")
            break

        print("Done waiting")

    print("Done executing coroutine")
    asyncio.get_event_loop().stop()


def main():
    asyncio.async(pending_doom())
    asyncio.async(looping_coro())

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, ask_exit)

    loop.run_forever()

    # I had to manually remove the handlers to
    # avoid an exception on BaseEventLoop.__del__
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.remove_signal_handler(sig)


if __name__ == '__main__':
    main()
