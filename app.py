from shiny import App, ui, render, reactive
import urllib3
import json
import openai
import os 
# Replace with your actual OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

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
            prompt = f"""Analyze the following code and provide:
            1. The type of content (e.g., Streamlit or Shiny)
            2. The main language (R or Python)
            3. If it's R, provide a generated manifest.json dependency file
            4. If it's Python, provide a generated requirements.txt file

            Code:
            {content}

            Please format your response as JSON with keys: 'content_type', 'language', and 'dependencies'.
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a code analysis assistant."},
                    {"role": "user", "content": prompt}
                ]
            )

            return json.loads(response.choices[0].message['content'])
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
