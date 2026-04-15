"""Command-line interface for PrivacyForms AI."""

import json

import click

from .ai import AI


@click.group()
@click.version_option(version="0.1.2", prog_name="privacyforms-ai")
def cli() -> None:
    """PrivacyForms AI - LLM integration CLI."""
    pass


@cli.command()
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def models(json_output: bool) -> None:
    """List all registered LLM models."""
    models_list = AI.get_models()

    if json_output:
        click.echo(json.dumps(models_list, indent=2))
    else:
        if not models_list:
            click.echo("No models found.")
            return

        click.echo(f"Found {len(models_list)} models:\n")
        for model in models_list:
            click.echo(f"  {model['key']:<40} {model['name']}")


@cli.command()
@click.argument("model_key")
@click.argument("prompt")
@click.option("--system", "-s", help="System prompt")
def prompt(model_key: str, prompt: str, system: str | None) -> None:
    """Send a prompt to a model.

    Example:
        privacyforms-ai prompt gpt-4o-mini "Hello, how are you?"
    """
    try:
        model = AI.get_model(model_key)
        response = AI.send_prompt(model, prompt, system=system)
        click.echo(AI.extract_response_text(response))
    except Exception as e:
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument("model_key")
@click.option("--system", "-s", help="System prompt to set the conversation context")
def chat(model_key: str, system: str | None) -> None:
    """Start an interactive chat session with a model.

    Example:
        privacyforms-ai chat gpt-4o-mini
        privacyforms-ai chat claude-sonnet-4-20250514 -s "You are a helpful coding assistant"

    Commands:
        /quit, /exit, /q  - End the chat session
        /clear            - Clear the conversation history
        /model            - Show the current model being used
    """
    try:
        conversation = AI.get_conversation(model_key, system=system)
    except Exception as e:
        raise click.ClickException(str(e)) from e

    click.echo(click.style(f"Starting chat with model: {model_key}", fg="green", bold=True))
    if system:
        click.echo(click.style(f"System prompt: {system}", fg="cyan"))
    click.echo(
        click.style(
            "Type /quit, /exit, or /q to end the session. Type /clear to reset history.",
            fg="bright_black",
        )
    )
    click.echo("-" * 50)

    while True:
        try:
            user_input = click.prompt("\nYou", type=str)
        except click.Abort:
            click.echo()
            break

        user_input = user_input.strip()

        if not user_input:
            continue

        # Handle special commands
        if user_input in ("/quit", "/exit", "/q"):
            click.echo(click.style("\nGoodbye!", fg="green"))
            break

        if user_input == "/clear":
            conversation = AI.get_conversation(model_key, system=system)
            click.echo(click.style("Conversation history cleared.", fg="yellow"))
            continue

        if user_input == "/model":
            click.echo(click.style(f"Current model: {model_key}", fg="cyan"))
            continue

        # Send message to the model
        try:
            response = AI.send_conversation_prompt(conversation, user_input)
            click.echo(
                click.style("\nAI: ", fg="blue", bold=True) + AI.extract_response_text(response)
            )
        except Exception as e:
            click.echo(click.style(f"\nError: {e}", fg="red"), err=True)


if __name__ == "__main__":
    cli()
