import random
from openai import OpenAI
from server.keys import *

# Mode
mode = "openai" # "local" or "openai" or "cloudflare"

# API
local_client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
cloudflare_client = OpenAI(base_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/v1", api_key = CLOUDFLARE_API_KEY)


# Embedding Models
local_embedding_model = "nomic-ai/nomic-embed-text-v1.5-GGUF"
cloudflare_embedding_model = "@cf/baai/bge-base-en-v1.5"
openai_embedding_model = "text-embedding-3-small"

# Notice how this model is not running locally. It uses an OpenAI key.
gpt4o = [
        {
            "model": "gpt-4o", #change this to point to a new model
            "api_key": OPENAI_API_KEY,
            # "cache_seed": random.randint(0, 100000),
        }
]

# Notice how this model is running locally. Uses local server with LMStudio
llama3 = [
        {
            "model": "meta-llama-3-8b-instruct", #change this to point to a new model
            'api_key': 'any string here is fine',
            'api_type': 'openai',
            'base_url': "http://127.0.0.1:1234",
            "cache_seed": random.randint(0, 100000),
        }
]

mistral = [
        {
            "model": "mistral-7b-instruct-v0.2", #change this to point to a new model
            'api_key': 'any string here is fine',
            'api_type': 'openai',
            'base_url': "http://127.0.0.1:1234",
            "cache_seed": random.randint(0, 100000),
        }
]

# This is a cloudflare model
# cloudflare_model = "@cf/meta/llama-4-scout-17b-16e-instruct"
# cloudflare_model = "@cf/qwen/qwq-32b"
cloudflare_model = "@hf/nousresearch/hermes-2-pro-mistral-7b"

# Define what models to use according to chosen "mode"
def api_mode(mode):
    clients = []
    completion_models = []
    embedding_models = []
    if mode == "local":
        # Add all local models you want to run simultaneously
        for model_cfg in [llama3[0], mistral[0]]:
            client = OpenAI(base_url=model_cfg['base_url']+"/v1", api_key=model_cfg['api_key'])
            completion_models.append(model_cfg['model'])
            embedding_models.append(local_embedding_model)
            clients.append(client)
        return clients, completion_models, embedding_models
    

    if mode == "cloudflare":
        # You can add more cloudflare models here if needed
        clients.append(cloudflare_client)
        completion_models.append(cloudflare_model)
        embedding_models.append(cloudflare_embedding_model)
        return clients, completion_models, embedding_models
    
    
    elif mode == "openai":
        clients.append(openai_client)
        completion_models.append(gpt4o[0]['model'])
        embedding_models.append(openai_embedding_model)
        return clients, completion_models, embedding_models
    else:
        raise ValueError("Please specify if you want to run local or openai models")

clients, completion_models, embedding_models = api_mode(mode)

# For backward compatibility, set embedding_model and completion_model to the first in the list
embedding_model = embedding_models[0] if embedding_models else None
completion_model = completion_models[0] if completion_models else None
client = clients[0] if clients else None