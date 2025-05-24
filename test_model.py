from transformers import AutoTokenizer, AutoModelForCausalLM
import torch, time

model_path = "./models/mistral-7b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token  # prevent warning

model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, trust_remote_code=True).eval()
device = "cpu"
model.to(device)

prompt = "[INST] Hello, how are you? [/INST]"
inputs = tokenizer(prompt, return_tensors="pt").to(device)

print("Generating...")
start = time.time()
outputs = model.generate(**inputs, max_new_tokens=50, do_sample=False)
end = time.time()

print("Generated in", round(end - start, 2), "seconds")
print(tokenizer.decode(outputs[0], skip_special_tokens=True))


try:
    with open("splunk_config.json") as f:
        SPLUNK_CONFIG = json.load(f)
except FileNotFoundError:
    print("ERROR: 'splunk_config.json' file not found. Please check the file.")
    exit(1)
except json.JSONDecodeError:
    print("ERROR: Failed to parse 'splunk_config.json'. Please check JSON format.")
    exit(1)
