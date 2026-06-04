import os

from vercel.workflow import Workflows, sleep

wf = Workflows()


@wf.workflow
async def greet(name: str) -> str:
    greeting = await say_hello(name)
    await sleep("2s")
    return f"{greeting} Hope you are doing well!"


@wf.step
async def say_hello(name: str) -> str:
    return f"Hello, {name}!"
