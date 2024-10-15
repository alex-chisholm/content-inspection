from shiny import App, ui, render, reactive
import urllib3
import re

app_ui = ui.page_fluid(
    ui.panel_title("GitHub Code Analyzer"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_text("github_link", "GitHub File Link", placeholder="https://github.com/user/repo/blob/main/file.py"),
            ui.input_action_button("analyze", "Analyze"),
        ),
        ui.output_text_verbatim("analysis_result"),
    )
)

def server(input, output, session):
    http = urllib3.PoolManager()

    @reactive.calc
    def fetch_github_content():
        if input.github_link():
            raw_url = input.github_link().replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            response = http.request('GET', raw_url)
            if response.status == 200:
                return response.data.decode('utf-8')
        return None

    @reactive.calc
    def analyze_code():
        content = fetch_github_content()
        if content:
            # Basic analysis without using OpenAI
            if "library(shiny)" in content or "ui <- " in content:
                content_type = "Shiny"
                language = "R"
                dependencies = "manifest.json:\n{\n  \"dependencies\": {\n    \"shiny\": \"*\"\n  }\n}"
            elif "import streamlit" in content:
                content_type = "Streamlit"
                language = "Python"
                dependencies = "requirements.txt:\nstreamlit"
            elif "from shiny import" in content:
                content_type = "Shiny"
                language = "Python"
                dependencies = "requirements.txt:\nshiny"
            else:
                content_type = "Unknown"
                language = "Python" if ".py" in input.github_link() else "R"
                dependencies = "Unable to determine dependencies"

            return {
                "content_type": content_type,
                "language": language,
                "dependencies": dependencies
            }
        return None

    @output
    @render.text
    def analysis_result():
        if input.analyze():
            result = analyze_code()
            if result:
                output = f"Content Type: {result['content_type']}\n"
                output += f"Language: {result['language']}\n\n"
                output += "Dependencies:\n"
                output += result['dependencies']
                return output
            else:
                return "Failed to analyze the code. Please check the GitHub link and try again."
        return "Click 'Analyze' to start the analysis."

app = App(app_ui, server)
