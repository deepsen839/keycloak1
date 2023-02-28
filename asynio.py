import asyncio
async def fetch_data():
    print('start fetching')
    await asyncio.sleep(2)
    print('done fetching')
    return {'data':1}
async def print_number():
    for i in range(10):
        print(i)
        await asyncio.sleep(0.25)
async def main():
    # task1 = asyncio.create_task(fetch_data())
    value = await fetch_data()
    print(value)
    task2 = asyncio.create_task(print_number())
    # await task1
    await task2
asyncio.run(main())    