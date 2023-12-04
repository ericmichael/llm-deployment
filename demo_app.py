import openai

openai.api_base = "https://csci4341-test.azurewebsites.net/chat/api/v1"
openai.api_key = "a365a359c83d04f28d46b2390a2da5730da95d86"

prompt = "You are a helpful assistant"
message = "Hi! Help me make tacos."

messages = [
    {"role": "system", "content": prompt},
    {"role": "user", "content": message}
]

model = "gpt-3.5-turbo"     # use gpt-3.5-turbo model
temperature = 0     # controls randomness
completion = openai.ChatCompletion.create(
    model=model, messages=messages, temperature=temperature
)
ai_reply = completion.choices[0].message.content.strip()
print(ai_reply)