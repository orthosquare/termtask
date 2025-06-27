import click
from click import echo

import os
from pathlib import Path

import tomlkit

class Cfg:
    def __init__(self, config_path, pref_name=None, database_dir=None, lists=None, current_list=None):
        self.config_path = config_path
        self.pref_name = pref_name if pref_name else os.getlogin()
        self.database_dir = Path(database_dir or config_path / 'data')
        self.lists = lists if lists else ['default']
        self.current_list = current_list if current_list else self.lists[0]

@click.group()
@click.pass_context
def cli(ctx):
    '''

    '''
    home = Path.home()
    config_path = home / '.config' / 'termtask'

    if not (config_path.exists() and config_path.is_dir()):
        echo("Configuration directory not found...\n\nConfiguring application.")
        pref_name = click.prompt("Preferred name", type=str, default=os.getlogin())
        data_dir = click.prompt("Database directory", type=str, default=config_path)
        initial_lists = click.prompt("Initial lists", type=str, default="default").split()

        #os.mkdir(config_path)
        
        doc = tomlkit.document()
        doc.add(tomlkit.comment("Configuration file for termtask."))
        doc.add(tomlkit.nl())

        user = tomlkit.table()
        user.add("username", pref_name)

        doc.add("user", user)

        database = tomlkit.table()
        database["directory"] = data_dir
        database["lists"] = initial_lists

        doc["database"] = database

        echo(doc.as_string())

@cli.command(name="list")
@click.pass_obj
def list(obj):
    echo(f"This command will show available lists. And the output should be updating.")

@cli.command(name="add")
@click.pass_obj
def add(obj):
    echo(f"Adds a task to the current list.")
