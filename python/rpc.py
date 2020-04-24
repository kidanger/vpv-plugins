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
        id = self.lastid
        msg = {'id': id, 'method': func, 'params': args}
        self.send(msg)
        r = self.receive()

        while r['id'] != id:
            msg = {'id': r['id'], 'result': self.evaluator(r['method'], *r['params'])}
            self.send(msg)
            r = self.receive()

        self.lastid -= 1
        return r['result'] if 'result' in r else None

    def send(self, msg):
        dat = json.dumps(msg)
        self.fout.write(dat + '\n')
        self.fout.flush()

    def receive(self):
        line = self.fin.readline()
        if not line:
            # let's assume vpv was closed
            sys.exit(0)
        return json.loads(line)

    def serve(self):
        while True:
            line = self.receive()
            msg = {'id': line['id'], 'result': self.evaluator(line['method'], *line['params'])}
            self.send(msg)


if __name__ == '__main__':
    fin, fout = sys.argv[1:]
    c = Connection(fin, fout, None)
    Connection.instance = c
    print('python serving...')
    c.serve()

