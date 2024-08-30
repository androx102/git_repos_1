


import asyncio
import time
import mqttools



class test_class():
    def __init__(self) -> None:
        pass

    def connect_to_broker(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asc_broker_connect())
        

    def add_sub(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asc_add_sub())
        

    def send_message(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asc_send_message())


    def read_message(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asc_read_message())


    #############################################################
    async def asc_broker_connect(self):
        self.client = mqttools.Client('localhost', 1883)
        await self.client.start()

    async def asc_add_sub(self):
        await self.client.subscribe('/foo')

    async def asc_send_message(self):
        self.client.publish(mqttools.Message('/foo', b'publish_to_self message'))
    
    async def asc_read_message(self):
        message = await self.client.messages.get()

        if message is None:
            print('Broker connection lost!')
        else:
            print(f'Topic:   {message.topic}')
            print(f'Message: {message.message}')
    #############################################################


#loop = asyncio.get_event_loop()
#loop.run_until_complete(main())


if __name__ == "__main__":
    x = test_class()
    x.connect_to_broker()
    x.add_sub()
    for y in range(20):
        x.send_message()
    x.read_message()
    print()