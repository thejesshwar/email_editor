from openai import OpenAI
from dotenv import load_dotenv
import os
import yaml

load_dotenv()

with open("prompts.yaml", "r") as f:
    prompts = yaml.safe_load(f)

class GenerateEmail():    
    def __init__(self, model: str, judge_model: str = "gpt-4.1"):
        # initialize client once
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.judge_deployment_name = judge_model
        self.deployment_name = model

    def _call_api(self, messages, judge_model=None):
        model_name = judge_model if judge_model else self.deployment_name
        response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0
            )
        return response.choices[0].message.content
    
    def get_prompt(self, prompt_name, prompt_type='user', **kwargs):
        template = prompts[prompt_name][prompt_type]
        return template.format(**kwargs)

    def send_prompt(self, user_prompt: str, system_msg="You are a helpful assistant.", model=None):
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt}
        ]
        return self._call_api(messages, judge_model=model)
    def generate(self, action: str, text: str, tone: str = None) -> str:
        prompt_key = action
        args = {"selected_text": text}
        if action == "shorten":
            prompt_key = "shorten"
        if action == "lengthen":
            prompt_key = "lengthen"
        elif action == "tone":
            prompt_key = "tone"
            if tone:
                args["tone"] = tone
        system_prompt = self.get_prompt(prompt_key, prompt_type='system', **args)
        user_prompt = self.get_prompt(prompt_key, **args)
        return self.send_prompt(user_prompt, system_prompt)
    def evaluate(self, original_text: str, generated_text: str, metric_key: str) -> str:
        args = {
            "original_text": original_text,
            "generated_text": generated_text
        }
        system_prompt = self.get_prompt(metric_key, prompt_type='system', **args)
        user_prompt = self.get_prompt(metric_key, **args)
        return self.send_prompt(user_prompt, system_prompt, model=self.judge_deployment_name)
    def generate_synthetic_data(self, topic, persona, tone, length, id_num):
        args = {
            "topic": topic,
            "persona": persona,
            "tone": tone,
            "length": length,
            "id_num": id_num
        }
        system_prompt = self.get_prompt("generate_data", prompt_type="system", **args)
        user_prompt = self.get_prompt("generate_data", prompt_type="user", **args)
        return self.send_prompt(user_prompt, system_prompt)