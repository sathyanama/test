
# ✅ Meta-LLaMA: Combined 3 Use Cases + Spinner + Optimized Token Logic + [INST]/<<SYS>> formatting

import time
import threading
from itertools import cycle
import torch

# Spinner state
stop_spinner = threading.Event()

def spinner(estimated_time):
    start_time = time.time()
    for symbol in cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]):
        elapsed_time = time.time() - start_time
        remaining_time = max(estimated_time - elapsed_time, 0)
        if stop_spinner.is_set():
            break
        print(f"\r Processing... {symbol} | Estimated time left: {remaining_time:.1f}s", end="", flush=True)
        time.sleep(0.2)

def clean_output(text):
    lines = text.strip().splitlines()
    cleaned = []
    for line in lines:
        if line.strip():
            cleaned.append(line.strip())
    return "\n".join(cleaned)

def correct_text(input_text, task="rewrite", max_new_tokens=512):
    if task == "rewrite":
        instruction = "Improve clarity, grammar, spelling, and tone. Make the writing suitable for goals or check-ins."
    elif task == "summarize":
        instruction = "Summarize the following into 4 to 5 clear and concise lines."
    elif task == "comms":
        instruction = "Revise this technical message for grammar, clarity, and professionalism."
    else:
        raise ValueError("Invalid task type.")

    prompt = f"[INST] <<SYS>>\n{instruction}\nOnly return the corrected or summarized version.\n<</SYS>>\n\n{input_text}\n[/INST]"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048).to("cpu")

    avg_time_per_token = 0.08
    estimated_time = max_new_tokens * avg_time_per_token

    stop_spinner.clear()
    spinner_thread = threading.Thread(target=spinner, args=(estimated_time,))
    spinner_thread.start()

    try:
        with torch.no_grad():
            start = time.time()
            outputs = model.generate(
                input_ids=inputs["input_ids"],
                max_new_tokens=max_new_tokens,
                do_sample=False,
                repetition_penalty=1.15
            )
            actual_time = time.time() - start

            full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = full_output
            if "]\n" in full_output:
                response = full_output.split("]\n", 1)[-1].strip()

            if outputs[0].size(0) >= inputs["input_ids"].size(1) + max_new_tokens - 5:
                response += "\n\n[Output may be truncated]"

    finally:
        stop_spinner.set()
        spinner_thread.join()

    print(f"\nDone in {actual_time:.1f} seconds.")
    return clean_output(response)

def run_meta_revision():
    print("\n️ Choose generation mode:")
    print("1. Full (slow but detailed)")
    print("2. Fast (quicker, shorter output)")
    mode_choice = input("Choose mode [1/2]: ").strip()
    gen_mode = "full" if mode_choice == "1" else "fast"

    while True:
        print("\n=== Meta-LLaMA Assistant ===")
        print("1. Rewrite / Check-ins / Goals")
        print("2. Summarize (long text to 4-5 lines)")
        print("3. Technical Comms Revision")
        print("4. Back to Main Menu")

        choice = input("Choose an option [1/2/3/4]: ").strip()
        if choice == "4":
            return

        task = {"1": "rewrite", "2": "summarize", "3": "comms"}.get(choice)
        if not task:
            print("❌ Invalid option. Try again.\n")
            continue

        print("\n📋 Paste your text (bullet points or paragraphs). Press Enter twice to process. Type 'quit' to return:\n")
        try:
            while True:
                lines = []
                user_quit = False
                while True:
                    line = input()
                    if line.strip().lower() == "quit":
                        user_quit = True
                        break
                    if line.strip() == "":
                        break
                    lines.append(line)

                if user_quit:
                    break

                input_text = "\n".join(lines).strip()
                if not input_text:
                    continue

                word_count = len(input_text.split())
                if gen_mode == "fast":
                    max_tokens = max(300, min(512, int(word_count * 0.4)))
                else:
                    max_tokens = max(600, min(1024, int(word_count * 0.7)))
                print(f"\n Generating with max_new_tokens={max_tokens} for approx {word_count} words...")

                bullet_points = input_text.strip().split('\n')
                chunks = ["\n".join(bullet_points[i:i+15]) for i in range(0, len(bullet_points), 15)]

                corrected_chunks = []
                for idx, chunk in enumerate(chunks):
                    print(f"\n Processing chunk {idx+1} of {len(chunks)}...")
                    corrected_chunk = correct_text(chunk, task=task, max_new_tokens=max_tokens)
                    corrected_chunks.append(corrected_chunk)

                corrected_text = "\n\n".join(corrected_chunks)
                print("\n Output:\n" + corrected_text + "\n")
                print("\n Paste your next input or type 'quit' to return:\n")

        except KeyboardInterrupt:
            stop_spinner.set()
            print("\nInterrupted. Returning to menu.\n")
