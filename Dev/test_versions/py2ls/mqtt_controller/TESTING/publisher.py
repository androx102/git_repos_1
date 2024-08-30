import asyncio

import mqttools


async def client_main():
    client = mqttools.Client('localhost', 1883)

    await client.start()
    await client.subscribe('/foo')
    message = "xyz".encode('ascii')

    while True:
        print()
        print(f'client: Publishing {message} on /foo.')
        client.publish(mqttools.Message('/foo', message))
        await asyncio.sleep(1)


async def main():
    await asyncio.gather(
        client_main()
    )


asyncio.run(main())