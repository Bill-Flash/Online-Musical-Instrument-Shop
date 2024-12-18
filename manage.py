from flask_script import Manager
from app import create_app, socketio
from wsgiref.simple_server import make_server

# if __name__ == '__main__':
#     server = make_server('', 5000, app)
#     server.serve_forever()

app = create_app('production')

# chatManager = Manager(app)
# chatManager.add_command('run', socketio.run(app=app, host='0.0.0.0', port=5010))


def filterDatetime(dt):
    s = str(dt)
    return s[0:19]

env = app.jinja_env
env.filters['datetime'] = filterDatetime

if __name__ == '__main__':
    # server = make_server('', 5000, app)
    app.run()
    # server.serve_forever()
