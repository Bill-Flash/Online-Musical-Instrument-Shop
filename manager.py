from flask_script import Manager
from manage import app
from app import db
from flask_migrate import Migrate, MigrateCommand

manager = Manager(app)
migrate = Migrate(app, db, render_as_batch=True)
manager.add_command("db", MigrateCommand)

if __name__ == "__main__":
    manager.run()

