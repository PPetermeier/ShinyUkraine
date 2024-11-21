import os

from shiny import ui, render, reactive


def about_page_ui():
    # Read the markdown content from file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    markdown_path = os.path.join(current_dir, "about.md")
    with open(markdown_path, "r", encoding="utf-8") as f:
        about_content = f.read()

    return ui.page_fluid(ui.panel_title("About this dashboard"), ui.card(ui.markdown(about_content)))


class AboutPageServer:
    """Server logic for the text page (if needed)."""

    # Add any reactive elements or server-side logic here if needed
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
