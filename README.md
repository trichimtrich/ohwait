# ohwait

An experiment in Python to make `sync` function could do `await` for coroutine, using a high level approach without doing intensive modification of intepreter.

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

Since from the begining Python wasn't designed for this concurrency concept (inconstrast with Golang), and it's kinda not good at threading (Check out another [David Beazley talk - Understanding the Pythong GIL](https://www.youtube.com/watch?v=Obt-vMVdM8s)). So after 15++ years, the new specification makes a large number of IO-bound libraries (which designed without the awareness about this concept) hard to intergrate to new `async` code.

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

- This code is NOT production ready, and only work for some use-case. Use as your own risk and don't blame me �.

# Instruction

- Install as a normal module

```bash
git clone https://github.com/trichimtrich/ohwait
cd ohwait
python setup.py install
```

- Usage:

```python
from ohwait import ohwait

async def coro():
    print("im a coroutine")
    return 1

def sync_func(): # to be called in a async_func
    print('sync_func enter')
    result = ohwait(coro())
    print('sync_func exit')
    return result

async def async_func():
    print('async_func enter')
    result = 0
    # Three lines below are syntax corect, and return the same value
    # Uncomment one line (not all) to check the result.
    # Currently only 1 `ohwait` call support in the whole `async` call chain.

    # result = ohwait(coro()) 
    # result = await coro()
    # result = sync_func()

    print('async_func exit')
    return result


## Run your event loop. Currently support `asyncio`, I will check `curio` and `trio` later.
import asyncio
loop = asyncio.get_event_loop()
result = loop.run_until_complete(async_func())
print('Finish with result:', result)
```

# Note

It works as expected, but the injection strategy is not perfect. Some of my note for future me/you:

- Check the `ref` count for each object.
- Support multiple `ohwait` call in `async` call chain. Because of the async frame doing `yield_from`, the second call of `ohwait` in child routine will break the parent frame stack. Change injected bytecode combination might work.
- Currently `co_code` in code object is changed permanently. So when doing injection, bytecodes need satisfy the revisiting of the routines (How about redo the injection with the new code object for each frame).
- Generator wrapper for each subroutine also needs to be collected by GC.
- Heap overflow can happen if your function doesn't have enough room (after `CALL_FUNCTION` bytecode) for replacing bytecode to unpack and yield data. (eg: function with only this line of code `return ohwait(coro)` )
