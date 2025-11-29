import google.generativeai as genai

genai.configure(api_key="AIzaSyA0qfGqkIvxBAt4IVoZSDFQTQiSF2X1yCE")

for m in genai.list_models():
    print(m.name)