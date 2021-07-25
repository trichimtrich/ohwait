# ohwait

An **Experiment** in Python to make `sync` function could do `await` for coroutine, using a high level approach without doing intensive modification of intepreter.

[👉 Click here to skip the boring paragraph](#instruction)

## Background

### Sync - Async

Concurrency in Python isn't new. With the `generator` object and `yield` opcode, python subroutine (callable) can suspend its execution, send/receive data with other subroutine. Check out this amazing talk from [David Beazley - Python Concurrency From the Ground Up](https://www.youtube.com/watch?v=MCs5OvhV9S4).

Unsurprisingly, Python also introduced familiar keywords `async/await` (if you from Javascript universe). That inevitablely divide your codebase into 2 separated parts: `async` and `non-async` code:

```python
import asyncio

def sync_func_in_middle():
    # async_wait_io_result() # => create a coroutine, but can't invoke
    # await async_wait_io_result() # => syntax error, no support
    return 1

async def async_wait_io_result():
    await asyncio.sleep(1)
    return 123

async def async_api_xyz():
    result = sync_func_in_middle()
    return result

asyncio.run(async_api_xyz())
```

- `async` function
    - Must run in / attach, to a `sync` event loop (above is `asyncio`)
    - Can call `sync` function and get the return value
    - Can create an `async` function (coroutine), and `await` for return value
- `non-async` function
    - It run bytecode in sequence from start to end (return value)
    - Can create an `async` suspended coroutine
    - But can't `await` that coroutine (unless spawn new event loop)
    - Even it is running in an event loop, `non-async` can't tell current loop to do awaiting.

### Integration

Since from the begining Python wasn't designed for this concurrency concept (inconstrast with Golang), and it's kinda not good at threading (Check out another [David Beazley talk - Understanding the Python GIL](https://www.youtube.com/watch?v=Obt-vMVdM8s)). So after 15++ years, the new specification makes a large number of IO-bound libraries (which designed without the awareness about this concept) hard to intergrate to new `async` code.

Find out more about the [discussion here](https://bugs.python.org/issue22239) when someone trying to run nested asyncio loop for the problem when `sync` couldn't do `await`.

Guys introduced a hacky way to partially get over this by using `greenlet` https://greenlet.readthedocs.io/en/latest/ for context switching (a characteristic of concurrency) between execution frame. But this still requires library developers to create 2 initial point of API via `async` or `non-async` interface.

Here an example to visualize this solution, if you have an api like this

```python
def api(req):
    return api_internal(req)

def api_internal(req):
    data = req.data
    # storage
    send_io_data(ctx.io, data)
    # processing
    data2 = process(data)
    # get from storage
    data3 = recv_io_data(ctx.io)
    # more processing
    data4 = more_process(data3)
    return data4

def send_io_data(io, data):
    io.send(data)

def recv_io_data(io):
    return io.recv()
```

With the `async` joining the play with `io` part, we need to create 2 api like this to support both `async` and `non-async` user.

```python
async def api_async(req):
    greenlet_await(api_internal, req)

def api(req):
    api_internal(req)

def api_internal(req):
    greenlet_await(send_io_data, ...)
    greenlet_await(recv_io_data, ...)

async def send_io_data(): ...
async def recv_io_data(): ...
```

As we can see that `greenlet_await` is a `sync` function. Pretty magic right !

Check out the [implementation here](https://gist.github.com/zzzeek/4e89ce6226826e7a8df13e1b573ad354).

### Motivation

Since my current project is doing a Python library with IO-bound tasks, the separated of `async` and `non-async` codebased caught my eyes because it is hard to support both type of user-usage within the same logic/code organizing.

This drived me into topic: how Python archives concurrency. After reading the implementation in CPython and greenlet, I found it is quite fascinating. Under the hood, there not much different between coroutine and subroutine, the only unlike thing is return value, and `YIELD` bytecode.

So my initial thought is patching/injecting the right bytecode with the right data returned, could turn a subroutine into a coroutine. 

This experiment is trying to archive that in the high level approach (python module), without modifying the intepreter, while still complying the specification.

## Disclaimer

- There is no problem with the original Python spec. Also the API designing (for `async` or `non-async`) is follow developers decision with his/her principles, there no best practice or language specs to answer this.

- This code is NOT production ready, and only work for some use-case. Use as your own risk and don't blame me 😶.

# Instruction

- Install as a normal module

```bash
git clone https://github.com/trichimtrich/ohwait
cd ohwait
python setup.py install
```

- Usage:

```python
import asyncio
from ohwait import ohwait


async def coro(a):
    print("> coroutine is running")
    await asyncio.sleep(0.5)
    return "result-" + a


def sync_func():  # to be called in a async chain
    print("> sync_func enter")
    result = ohwait(coro("from-ohwait-in-sync-func"))
    print("> sync_func exit")
    return result


async def async_func():
    print("> async_func enter")

    print(await coro("from-normal-await-call"))
    print(ohwait(coro("from-ohwait-directly")))
    print(sync_func())

    print("> async_func exit")


print("=" * 50 + " FIRST RUN " + "=" * 50)
asyncio.run(async_func())

print("=" * 50 + " SECOND RUN " + "=" * 50)
asyncio.run(async_func())
```

- By default `ohwait` uses `asyncio` in coroutine wrapper. To use or switch betwen different libraries, eg: [trio](https://trio.readthedocs.io/) and [curio](https://curio.readthedocs.io/en/latest/), check this:

```python
# curio
from ohwait import use_curio
use_curio()
curio.run(ohwait_coroutine())

# trio
from ohwait import use_trio
use_trio()
trio.run(ohwait_coroutine)

# switch back to `asyncio`
from ohwait import use_asyncio
use_asyncio()
asyncio.run(ohwait_coroutine())
```

# Technical details

To be written ...

> Code is only 200 lines, shorter than this README 😜

# Note

It works as expected, but the injection strategy is not perfect. Some of my note for future me/you:

- Check the `ref` count for each object.
- ~~Support multiple `ohwait` call in `async` call chain. Because of the async frame doing `yield_from`, the second call of `ohwait` in child routine will break the parent frame stack. Change injected bytecode combination might work.~~
- ~~Currently `co_code` in code object is changed permanently. So when doing injection, bytecodes need satisfy the revisiting of the routines (How about redo the injection with the new code object for each frame).~~
- Generator wrapper for each subroutine also needs to be collected by GC.
- Heap overflow can happen if your function doesn't have enough room (after `CALL_FUNCTION` bytecode) for replacing bytecode to unpack and yield data. (eg: function with only this line of code `return ohwait(coro)` ). Current payload size is 8 bytes.
- We use `UNPACK_SEQUENCE` in payload, it requires extra stack buffer in frame (in this case +2), otherwise will receive SIGSEGV. [Check this](https://github.com/python/cpython/blob/3.8/Objects/frameobject.c#L665)
- Code object for every functions in call-chain after `ohwait` are changed permanently, because we patch the `co_code` directly, not the `frame` (different between each call to the same function). So if code uses indirect call for mixed `ohwait`, `non-ohwait` functions, unexpected behaviour will happen. Eg:
```python
async def coro(): ...

## ohwait function
def ohwait_func1():
    ohwait(coro())

def ohwait_func2():
    ohwait(coro())

## non-ohwait function
def non_ohwait_func():
    pass # do anything but call `ohwait`


## main - caller
async def async_func_BAD():
    for func in (ohwait_func1, non_ohwait_func):
        func() # indirect call of mixed funcs

async def async_func_GOOD():
    for func in (ohwait_func1, ohwait_func2):
        func() # indirect call of `ohwait` functions

async def async_func_VERY_GOOD():
    # direct call
    non_ohwait_func()
    ohwait_func1()
    non_ohwait_func()
    ohwait_func2()
    non_ohwait_func()
```
- Another approach is create new code object (with injected code) and bind it to `frame` object instead of using the same code object but only replace the `co_code`. Not sure if it can solve the indirect call problem.
- ~~Library like `asyncio` works pretty well, but `curio` and `trio` do not. Haven't checked yet, maybe need to switch some more flags of generator object to fool them 😏.~~
- Also, there are other concurrency's statements need to check, like `await from`, `await for`.

# References/Materials

> How generator, async await works, yield from
- https://stackoverflow.com/questions/49005651/how-does-asyncio-actually-work
- https://towardsdatascience.com/cpython-internals-how-do-generators-work-ba1c4405b4bc
- https://stackoverflow.com/questions/9708902/in-practice-what-are-the-main-uses-for-the-new-yield-from-syntax-in-python-3

> PEP
- Generator: https://www.python.org/dev/peps/pep-0255/
- Coroutines: https://www.python.org/dev/peps/pep-0342/
- Async/Await: https://www.python.org/dev/peps/pep-0492/#abstract
- Async generator: https://www.python.org/dev/peps/pep-0525/

> Greenlet
- https://greenlet.readthedocs.io/en/latest/
