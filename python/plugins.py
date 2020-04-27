import api

plugins = []

def load(name):
    try:
        p = __import__(name)
        plugins.append(p)
        if hasattr(p, 'init'):
            p.init()
        print(f'plugin {name} loaded as {p}')
    except Exception as e:
        print('could not load plugin {}: {}'.format(name, e))

def init():
    pass

def on_tick(*args):
    for p in plugins:
        if hasattr(p, 'on_tick'):
            try:
                p.on_tick(*args)
            except Exception as e:
                print('error while calling `on_tick` for plugin {}: {}. Plugin disabled.'.format(p.__name__, e))
                plugins.remove(p)

def on_window_tick(*args):
    for p in plugins:
        if hasattr(p, 'on_window_tick'):
            p.on_window_tick(*args)

def rpc_evaluator(func, *args):
    return globals()[func](*args)

if __name__ == '__main__':
    import sys
    from rpc import Connection
    fin, fout = sys.argv[1:]
    c = Connection(fin, fout, rpc_evaluator)
    api.con = c
    print('python serving...')
    c.serve()

