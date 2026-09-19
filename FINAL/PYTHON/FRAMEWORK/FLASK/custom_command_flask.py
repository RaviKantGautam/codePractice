import click
from flask import Flask

app = Flask(__name__)

@app.cli.command("custom-command")
def custom_command():
    click.echo("This is a custom command.")
    click.echo("Custom command executed successfully.")
    click.echo("End of custom command.")

# To run this custom command, use the following command in the terminal:
# flask custom-command