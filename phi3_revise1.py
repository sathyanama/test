import transformers
import torch
import time
import threading
from itertools import cycle
import sys
import re  # For cleaning the output

# Choose the model: **Faster Phi-3**
model_id = "Phi-3-mini-128k-instruct"

# Load tokenizer and model explicitly (optimized for CPU/GPU)
tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)
model = transformers.AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float32 if torch.cuda.is_available() else torch.bfloat16,  # Optimized for CPU/GPU
    device_map="auto",
    low_cpu_mem_usage=True  # Prevents offloading to disk if possible
)

# Create a text generation pipeline
pipeline = transformers.pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    config={"use_cache": True, "max_length": 400},  # Supports longer texts
)

# Spinner function to show loading animation
stop_spinner = threading.Event()
def spinner(estimated_time):
    start_time = time.time()
    for symbol in cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]):
        elapsed_time = time.time() - start_time
        remaining_time = max(estimated_time - elapsed_time, 0)
        if stop_spinner.is_set():
            break
        print(f"\r⏳ Processing... {symbol} | Estimated time left: {remaining_time:.1f}s", end="", flush=True)
        time.sleep(0.2)

# Function to clean the output and extract only the corrected text
def clean_output(output_text):
    # Remove `[INST] ... [/INST]` if it appears in output
    output_text = re.sub(r"\[INST\].*?\[/INST\]", "", output_text, flags=re.DOTALL).strip()
    # Remove any unnecessary system instructions
    output_text = re.sub(r"<<SYS>>.*?<</SYS>>", "", output_text, flags=re.DOTALL).strip()
    # Remove trailing system tokens like `[/SYS]`
    output_text = re.sub(r"\[/SYS\]", "", output_text).strip()
    return output_text

# Function to process text correction
def correct_text(input_text):
    prompt = f"[INST] <<SYS>> Correct the mistakes, grammar, and punctuation in the text. Only return the corrected text without any explanations. <</SYS>>\n{input_text} [/INST]"

    # Estimate response time based on text length
    tokens_to_generate = min(300, len(input_text.split()) * 2)  # Allows longer sentences
    avg_time_per_token = 0.04 if torch.cuda.is_available() else 0.08  # Faster on GPU, slower on CPU
    estimated_total_time = tokens_to_generate * avg_time_per_token

    print(f"\n🔍 Estimated response time: {estimated_total_time:.1f} seconds.")

    # Start spinner in a separate thread
    stop_spinner.clear()
    spinner_thread = threading.Thread(target=spinner, args=(estimated_total_time,))
    spinner_thread.start()

    try:
        # Start timing actual response generation
        start_time = time.time()

        # Generate corrected text
        outputs = pipeline(
            prompt,
            max_new_tokens=tokens_to_generate,
            eos_token_id=tokenizer.eos_token_id,
            do_sample=True,  # Enable sampling for better response quality
            temperature=0.7,  # Adjusted for better corrections
            top_p=0.95,  # Sampling diversity
            num_beams=2,  # Enable beam search for better grammar correction
            repetition_penalty=1.2,
            early_stopping=True,
            truncation=True,  # Prevents long inputs from crashing
        )

        # Stop spinner
        stop_spinner.set()
        spinner_thread.join()

        # Calculate actual time taken
        actual_time_taken = time.time() - start_time

        # Extract corrected output
        corrected_text = outputs[0]["generated_text"].strip()
        corrected_text = clean_output(corrected_text)  # Clean output

        print(f"\n✅ Processed in {actual_time_taken:.1f} seconds.")
        return corrected_text

    except KeyboardInterrupt:
        # Stop spinner before exiting
        stop_spinner.set()
        spinner_thread.join()
        print("\n🚨 Process interrupted by user (Ctrl + C). Exiting gracefully.\n")
        sys.exit(0)

# Main loop for user input
print("\n📝 Enter text for correction (Paste multi-line text and press Enter twice to process, type 'quit' to exit):\n")

try:
    while True:
        print("> (Paste your text and press Enter twice to process)")
        
        lines = []
        while True:
            try:
                line = input()
                if line.strip().lower() == "quit":
                    print("\n👋 Exiting. Goodbye!\n")
                    sys.exit(0)
                if line.strip() == "":
                    break
                lines.append(line)
            except EOFError:
                break

        input_text = "\n".join(lines).strip()

        if input_text:
            corrected_text = correct_text(input_text)
            print("\n✏️ Corrected Text:\n" + corrected_text + "\n")

except KeyboardInterrupt:
    stop_spinner.set()
    print("\n🚨 Process interrupted by user (Ctrl + C). Exiting safely.\n")
    sys.exit(0)