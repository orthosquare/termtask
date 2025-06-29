import click
from click import echo

import os
import sys
from pathlib import Path

import hashlib

from datetime import datetime, timedelta

import tomlkit

from prettytable import PrettyTable

class Task:
    """
    Class to store the task internal state.
    
    Attributes
    ----------
    name : str
        Name of the task.
    priority : int
        Priority of the task. Given a value from 1 to 5 with 1 having the highest priority.
    message : str
        Stores any important details about the task.
    due_datetime : datetime
        Stores the datetime that the task is due.
    hash_id : str
        ID stores a hash of the creation datetime of the original file. The hash uniquely identifies the task.
    path : Path
        Stores the path of the task file.

    Methods
    -------
    to_toml():
        Returns the formatted toml string representing the task file.

    Class Methods
    -------------
    from_toml_file(toml_path):
        Returns a task object read from the toml file at toml_path.
    """
    def __init__(self, name, priority, message, due_datetime, hash_id, path):
        self.name = name
        self.priority = priority
        self.message = message
        self.due_datetime = due_datetime
        self.hash_id = hash_id
        self.path = path

    def to_toml_string(self):
        """
        Formats the internal task data into a toml file.
        """
        doc = tomlkit.document()
        doc.add(tomlkit.comment("This is a task file for termtask. If editing by hand, make sure to preserve all keys."))
        doc.add(tomlkit.nl())
        doc['name'] = self.name
        doc['priority'] = self.priority
        doc['message'] = self.message
        doc['due_datetime'] = self.due_datetime

        return doc.as_string()

    def from_toml_file(toml_path):
        """
        Reads a task file from the given toml path.
        """
        with open(toml_path, 'r') as toml_file:
            toml = tomlkit.load(toml_file)
            task = Task(toml["name"], toml["priority"], toml["message"], toml["due_datetime"], toml_path.stem, toml_path)
            return task

    def __str__(self):
        return f"<Task name: {self.name}, priority: {self.priority}, \
message: {self.message}, due_datetime: {self.due_datetime}, hash_id: {self.hash_id}, \
path: {self.path} >"

class Cfg:
    """
    Stores the internal state_path for consistent reference.
    """
    def __init__(self, state_path):
        self.state_path = state_path

@click.group()
@click.pass_context
def cli(ctx):
    """
    Click entry point, defines the state path variable.
    """
    home = Path.home()
    state_path = home / '.local' / 'state' / 'termtask'

    if not (state_path.exists() and state_path.is_dir()):
        echo(f"Directory not found. Creating directory {state_path}.")
        try:
            os.mkdir(state_path)
        except:
            echo(f"Failed to make state ({state_path}) directory for storing task data.", err=True)
            sys.exit(1)
    ctx.obj = Cfg(state_path)

@cli.command(name="list", help="Show the todo lists, new line separated. If a list is provided, display tasks in that list.")
@click.argument("list_name", metavar="<list>", required=False,)
@click.option("-c", "--complete", is_flag=True, help="Show complete tasks.")
@click.pass_obj
def list(obj, list_name, complete):
    """
    Display a specific list. If no list is given then display available lists.
    """
    if list_name:
        list_path = obj.state_path / list_name
        if complete:
            list_path = list_path / '_complete'
        if not (list_path.exists() and list_path.is_dir()):
            echo("No such list exists. Please create the list before continuing.", err=True)
            sys.exit(1)
        
        table = PrettyTable()
        table.field_names = ["Task ID", "Name", "Priority", "Due Date"]
        for task_path in filter(lambda x: x.is_file(), list_path.iterdir()):
            task = Task.from_toml_file(task_path)
            table.add_row([task.hash_id, task.name, task.priority, task.due_datetime])

        print(table)

    else:
        for task_list in map(lambda x: x.name, filter(lambda x: x.is_dir(), obj.state_path.iterdir())):
            echo(task_list)

@cli.command(name="add", help="Add a task to the provided list")
@click.argument("list_name", metavar="list")
@click.argument("task_name", metavar="<task name>", type=str)
@click.option("-p", "--priority", type=click.IntRange(min=1, max=5), default=5, help="Specify a priority for the given task.")
@click.option("-m", "--message", type=str, default="", help="Specify a message for the task.")
@click.option("-d", "--due", type=click.DateTime(), default=None, help="Specify a due date.")
@click.pass_obj
def add(obj, list_name, task_name, priority, message, due):
    """
    Create and add a task to a list.
    """
    list_path = obj.state_path / list_name

    if not (list_path.exists() and list_path.is_dir()):
        echo("No such list exists. Please create the list before continuing.", err=True)
        sys.exit(1)

    if not due:
        due = datetime.today() + timedelta(days=7)

    task_created_hash = hashlib.shake_256(datetime.now().isoformat().encode()).hexdigest(3)
    task = Task(task_name, priority, message, due, task_created_hash, (list_path / task_created_hash).with_suffix('.toml'))

    try:
        with open(task.path, 'w') as file:
            file.write(task.to_toml_string())
    except Exception as e:
        echo(f"An error occured: {e}")
        sys.exit(1)

@cli.command(name="addlist", help="Create a new list.")
@click.argument("list_name", metavar="list", required=True, type=str)
@click.pass_obj
def add_list(obj, list_name):
    """
    Add a list.
    """
    list_path = obj.state_path / list_name

    if list_path.exists() and list_path.is_dir():
        echo("List already exists.", err=True)
        sys.exit(1)

    try:
        os.mkdir(list_path)
        os.mkdir(list_path / '_complete')
    except Exception as e:
        echo(f"Error creating list. {e}")

@cli.command(name="complete", help="Complete a task")
@click.argument("task_id", metavar="id", required=True, type=str)
@click.pass_obj
def complete(obj, task_id):
    """
    Complete a task.
    """
    for list_dir in filter(lambda x: x.is_dir(), obj.state_path.iterdir()):
        file_path = (list_dir / task_id).with_suffix('.toml')
        if file_path.exists():
            complete_path = file_path.parent / '_complete' / file_path.name
            file_path.rename(complete_path)
            break
            
@cli.command(name="show", help="Show a task with a given ID.")
@click.argument("task_id", metavar="id")
@click.pass_obj
def show(obj, task_id):
    """
    Show a task with a given ID.
    """
    for list_dir in filter(lambda x: x.is_dir(), obj.state_path.iterdir()):
        file_path = (list_dir / task_id).with_suffix('.toml')
        if file_path.exists():
            task = Task.from_toml_file(file_path)
            echo(f"\nID: {task.hash_id}")
            echo(f"List: {list_dir.name}")
            echo(f"Name: {task.name}")
            echo(f"Due Date: {task.due_datetime}")
            echo(f"Priority: {task.priority}")
            echo(f"Message:\n{task.message}")
            break

@cli.command(name="move", help="Change the list for the specific task.")
@click.argument("task_id", metavar="id")
@click.argument("list_name", metavar="list")
@click.pass_obj
def move(obj, task_id, list_name):
    """
    Change the list of the specified task_id.
    """
    list_path = obj.state_path / list_name
    if not (list_path.exists() and list_path.is_dir()):
        echo("No such list exists. Please create the list before continuing.", err=True)
        sys.exit(1)

    for list_dir in filter(lambda x: x.is_dir(), obj.state_path.iterdir()):
        file_path = (list_dir / task_id).with_suffix('.toml')
        if file_path.exists():
            file_path.rename((list_path / task_id).with_suffix('.toml'))
            break

@cli.command(name="all", help="Show all tasks from all lists.")
@click.option("-t", "--total", is_flag=True, help="Show the completed tasks.")
@click.pass_obj
def all(obj, total):
    """
    Show all tasks from all lists.
    """
    table = PrettyTable()
    table.field_names = ["List", "Task ID", "Name", "Priority", "Due Date"]
    
    for list_path in filter(lambda x: x.is_dir(), obj.state_path.iterdir()):

        for task_path in filter(lambda x: x.is_file(), list_path.iterdir()):
            task = Task.from_toml_file(task_path)
            table.add_row([list_path.name, task.hash_id, task.name, task.priority, task.due_datetime])

    print(table)

    if total:
        echo("\n\n---Complete---")

        table = PrettyTable()
        table.field_names = ["List", "Task ID", "Name", "Priority", "Due Date"]
    
        for list_path in filter(lambda x: x.is_dir(), obj.state_path.iterdir()):

            for task_path in filter(lambda x: x.is_file(), (list_path / '_complete').iterdir()):
                task = Task.from_toml_file(task_path)
                table.add_row([list_path.name, task.hash_id, task.name, task.priority, task.due_datetime])

        print(table)

@cli.command(name="update", help="Updates a task")
@click.argument("task_id", metavar="id")
@click.option("-n", "--name", type=str)
@click.option("-p", "--priority", type=click.IntRange(min=0, max=5))
@click.option("-m", "--message", type=str)
@click.option("-d", "--due", type=click.DateTime())
@click.pass_obj
def update(obj, task_id, name, priority, message, due):
    """
    Updates a the given task.
    """
    for list_dir in filter(lambda x: x.is_dir(), obj.state_path.iterdir()):
        file_path = (list_dir / task_id).with_suffix('.toml')
        if file_path.exists():
            task = Task.from_toml_file(file_path)
            if name:
                task.name = name
            if priority:
                task.priority = priority
            if message:
                task.message = message
            if due:
                task.due_datetime = due

    try:
        with open(task.path, 'w') as file:
            file.write(task.to_toml_string())
    except Exception as e:
        echo(f"An error occured: {e}")
        sys.exit(1)


