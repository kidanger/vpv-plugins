import api

plugins = []

def load(name):
    p = __import__(name)
    plugins.append(p)
    if hasattr(p, 'init'):
        p.init(*args)
    print(f'plugin {name} loaded as {p}')

def init():
    pass

def on_tick(*args):
    for p in plugins:
        if hasattr(p, 'on_tick'):
            p.on_tick(*args)

def on_window_tick(*args):
    for p in plugins:
        if hasattr(p, 'on_window_tick'):
            p.on_window_tick(*args)

def rpc_evaluator(func, *args):
    return eval(func)(*args)

if __name__ == '__main__':
    import sys
    from rpc import Connection
    fin, fout = sys.argv[1:]
    c = Connection(fin, fout, rpc_evaluator)
    api.con = c
    print('python serving...')
    c.serve()

