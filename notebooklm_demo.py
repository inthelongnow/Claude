#!/usr/bin/env python3
"""Demo script showing how to use notebooklm-py to create and interact with notebooks.

Before running:
    1. pip install notebooklm-py
    2. notebooklm login          # authenticate via browser
    3. python notebooklm_demo.py # run this script

Usage examples:
    # List existing notebooks
    python notebooklm_demo.py list

    # Create a notebook from a URL and ask questions
    python notebooklm_demo.py create "My Research" --url "https://en.wikipedia.org/wiki/Python_(programming_language)"

    # Ask a question to the current notebook
    python notebooklm_demo.py ask "What are the key points?"

    # Generate an audio overview (podcast-style)
    python notebooklm_demo.py audio

    # Generate a quiz from notebook sources
    python notebooklm_demo.py quiz
"""

import argparse
import asyncio
import sys

from notebooklm import NotebookLMClient


async def list_notebooks():
    """List all notebooks in the account."""
    async with await NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        if not notebooks:
            print("No notebooks found. Create one with: python notebooklm_demo.py create \"My Notebook\"")
            return
        for nb in notebooks:
            print(f"  {nb.id[:12]}...  {nb.title}")


async def create_notebook(title: str, url: str | None = None):
    """Create a new notebook, optionally adding a URL source."""
    async with await NotebookLMClient.from_storage() as client:
        nb = await client.notebooks.create(title)
        print(f"Created notebook: {nb.title} ({nb.id})")

        if url:
            print(f"Adding source: {url}")
            source = await client.sources.add_url(nb.id, url, wait=True)
            print(f"Source added: {source.title}")

        print(f"\nSet as active notebook with:\n  notebooklm use {nb.id[:12]}")


async def ask_question(question: str, notebook_id: str | None = None):
    """Ask a question to a notebook."""
    async with await NotebookLMClient.from_storage() as client:
        if not notebook_id:
            notebooks = await client.notebooks.list()
            if not notebooks:
                print("No notebooks found. Create one first.")
                return
            notebook_id = notebooks[0].id
            print(f"Using notebook: {notebooks[0].title}")

        result = await client.chat.ask(notebook_id, question)
        print(f"\nQ: {question}")
        print(f"A: {result.answer}")


async def generate_audio(notebook_id: str | None = None):
    """Generate an audio overview (podcast-style) from notebook sources."""
    async with await NotebookLMClient.from_storage() as client:
        if not notebook_id:
            notebooks = await client.notebooks.list()
            if not notebooks:
                print("No notebooks found. Create one first.")
                return
            notebook_id = notebooks[0].id
            print(f"Using notebook: {notebooks[0].title}")

        print("Generating audio overview (this may take a few minutes)...")
        status = await client.artifacts.generate_audio(notebook_id)
        await client.artifacts.wait_for_completion(notebook_id, status.task_id)
        await client.artifacts.download_audio(notebook_id, "notebook_audio.mp3")
        print("Audio saved to: notebook_audio.mp3")


async def generate_quiz(notebook_id: str | None = None):
    """Generate a quiz from notebook sources."""
    async with await NotebookLMClient.from_storage() as client:
        if not notebook_id:
            notebooks = await client.notebooks.list()
            if not notebooks:
                print("No notebooks found. Create one first.")
                return
            notebook_id = notebooks[0].id
            print(f"Using notebook: {notebooks[0].title}")

        print("Generating quiz...")
        status = await client.artifacts.generate_quiz(notebook_id)
        await client.artifacts.wait_for_completion(notebook_id, status.task_id)
        await client.artifacts.download_quiz(notebook_id, "notebook_quiz.json", fmt="json")
        print("Quiz saved to: notebook_quiz.json")


def main():
    parser = argparse.ArgumentParser(description="NotebookLM demo script")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("list", help="List all notebooks")

    create_p = subparsers.add_parser("create", help="Create a notebook")
    create_p.add_argument("title", help="Notebook title")
    create_p.add_argument("--url", help="URL to add as a source")

    ask_p = subparsers.add_parser("ask", help="Ask a question")
    ask_p.add_argument("question", help="Question to ask")
    ask_p.add_argument("--notebook", help="Notebook ID (uses first notebook if omitted)")

    audio_p = subparsers.add_parser("audio", help="Generate audio overview")
    audio_p.add_argument("--notebook", help="Notebook ID (uses first notebook if omitted)")

    quiz_p = subparsers.add_parser("quiz", help="Generate a quiz")
    quiz_p.add_argument("--notebook", help="Notebook ID (uses first notebook if omitted)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "list": lambda: list_notebooks(),
        "create": lambda: create_notebook(args.title, getattr(args, "url", None)),
        "ask": lambda: ask_question(args.question, getattr(args, "notebook", None)),
        "audio": lambda: generate_audio(getattr(args, "notebook", None)),
        "quiz": lambda: generate_quiz(getattr(args, "notebook", None)),
    }

    asyncio.run(commands[args.command]())


if __name__ == "__main__":
    main()
