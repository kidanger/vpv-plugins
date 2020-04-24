import sys
import json
import threading

class Connection:
    lastid = 0

    def __init__(self, fin, fout, evaluator):
        self.fout = open(fout, 'w')
        self.fin = open(fin, 'r')
        self.evaluator = evaluator

    def call(self, func, *args):
        assert threading.current_thread() is threading.main_thread()
        self.lastid += 1
        msg = {'type': 'request', 'func': func, 'args': args}
        id = self.send(self.lastid, msg)
        nn, r = self.receive()

        while nn != id:
            msg = {'type': 'reply', 'response': self.evaluator(r['func'], *r['args'])}
            self.send(nn, msg)
            nn, r = self.receive()

        self.lastid -= 1
        return r['response']

    def send(self, n, msg):
        dat = json.dumps(msg)
        self.fout.write(str(n) + ' ' + dat + '\n')
        self.fout.flush()
        return n

    def receive(self):
        line = self.fin.readline()
        if not line:
            # let's assume vpv was closed
            sys.exit(0)
        n, line = line.split(' ', 1)
        return int(n), json.loads(line)

    def serve(self):
        while True:
            n, line = self.receive()
            msg = {'type': 'reply', 'response': self.evaluator(line['func'], *line['args'])}
            self.send(n, msg)


if __name__ == '__main__':
    fin, fout = sys.argv[1:]
    c = Connection(fin, fout, None)
    Connection.instance = c
    print('python serving...')
    c.serve()

