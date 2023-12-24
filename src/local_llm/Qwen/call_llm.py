import openai
openai.api_base = "http://localhost:5001/v1"
openai.api_key = "none"

# create a request activating streaming response
for chunk in openai.ChatCompletion.create(
    model="Qwen",
    messages=[
        {"role": "user", "content": "你好"}
    ],
    stream=True
    # Specifying stop words in streaming output format is not yet supported and is under development.
):
    if hasattr(chunk.choices[0].delta, "content"):
        print(chunk.choices[0].delta.content, end="", flush=True)

# create a request not activating streaming response
response = openai.ChatCompletion.create(
    model="Qwen",
    messages=[
        {"role": "user", "content": "chunk0: At 00:01 game time, our current StarCraft II situation is as follows:\n\nResources:\n- Game time: 00:01\n- Worker supply: 12\n- Supply left: 2\n- Supply cap: 15\n- Supply used: 13\n\nBuildings:\n- Nexus count: 1\n\nUnits:\n- Probe count: 12\n\nPlanning:\n\nPlanning unit:\n- Planning probe count: 1\n\n\nchunk1: At 00:01 game time, our current StarCraft II situation is as follows:\n\nResources:\n- Game time: 00:01\n- Worker supply: 12\n- Supply left: 2\n- Supply cap: 15\n- Supply used: 13\n\nBuildings:\n- Nexus count: 1\n\nUnits:\n- Probe count: 12\n\nPlanning:\n\nPlanning unit:\n- Planning probe count: 1\n\n\nchunk2: At 00:01 game time, our current StarCraft II situation is as follows:\n\nResources:\n- Game time: 00:01\n- Worker supply: 12\n- Supply left: 2\n- Supply cap: 15\n- Supply used: 13\n\nBuildings:\n- Nexus count: 1\n\nUnits:\n- Probe count: 12\n\nPlanning:\n\nPlanning unit:\n- Planning probe count: 1\n\n\nchunk3: At 00:01 game time, our current StarCraft II situation is as follows:\n\nResources:\n- Game time: 00:01\n- Worker supply: 12\n- Supply left: 2\n- Supply cap: 15\n- Supply used: 13\n\nBuildings:\n- Nexus count: 1\n\nUnits:\n- Probe count: 12\n\nPlanning:\n\nPlanning unit:\n- Planning probe count: 1\n\n\nchunk4: At 00:01 game time, our current StarCraft II situation is as follows:\n\nResources:\n- Game time: 00:01\n- Worker supply: 12\n- Supply left: 2\n- Supply cap: 15\n- Supply used: 13\n\nBuildings:\n- Nexus count: 1\n\nUnits:\n- Probe count: 12\n\nPlanning:\n\nPlanning unit:\n- Planning probe count: 1\n\n"}
    ],
    stream=False,
    stop=[] # You can add custom stop words here, e.g., stop=["Observation:"] for ReAct prompting.
)
print(response.choices[0].message.content)

