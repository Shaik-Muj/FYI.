import cohere
import os

# Initialize Cohere client
cohere_api_key = os.getenv("COHERE_API_KEY", "vN4iBHgfi3AbVN4bMy3aWsNoFpem7x60CmY8oRAD")
co = cohere.Client(cohere_api_key)

def check_news(user_input: str) -> str:
    prompt = f"{user_input}. Check whether this news is real or fake. If not, give me the correct news."
    try:
        try:
            response = co.generate(
                model='command',
                prompt=prompt,  # It's good practice to use the 'prompt' variable you defined
                max_tokens=100
            )

            return response.generations[0].text.strip()
        except Exception as e:
            return f"Error contacting Cohere API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}" # It's good to have a broader catch as well