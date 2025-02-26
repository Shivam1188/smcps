import openai
import random
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

class AIFunctions:
    @staticmethod
    def generate_script(content_theme, video_format, tone, target_audience, keywords):
        prompt = f"Generate a {tone} script for a {video_format} video on {content_theme}. Target audience: {target_audience}. Use keywords: {', '.join(keywords)}."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a content generation AI that writes engaging video scripts."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']

    @staticmethod
    def suggest_visual_style(content_theme, target_platform):
        styles = {
            "Instagram": ["Minimalistic", "Aesthetic", "Vibrant"],
            "YouTube": ["Cinematic", "Informative", "Influencer-style"],
            "TikTok": ["Trendy", "Fast-paced", "Engaging"]
        }
        return random.choice(styles.get(target_platform, ["Standard"]))

    @staticmethod
    def analyze_sentiment(script):
        prompt = f"Analyze the sentiment of the following script and categorize it as Positive, Neutral, or Negative: {script}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You analyze text sentiment."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']

    @staticmethod
    def suggest_posting_time(target_platform):
        optimal_times = {
            "Instagram": "6 PM - 9 PM",
            "YouTube": "12 PM - 3 PM",
            "TikTok": "5 PM - 8 PM"
        }
        return optimal_times.get(target_platform, "Anytime between 10 AM - 6 PM")

    @staticmethod
    def generate_qc_feedback(script, video_style):
        prompt = f"Review the following script and provide constructive feedback based on the {video_style} style: {script}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You provide QC feedback on video scripts."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']