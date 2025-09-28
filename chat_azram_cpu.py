import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
from peft import PeftModel

def build_prompt(tok, messages):
    try:
        return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except Exception:
        prompt = ""
        for m in messages:
            role = m["role"]
            content = m["content"]
            if role == "system":
                prompt += f"<<SYS>>\n{content}\n<</SYS>>\n"
            elif role == "user":
                prompt += f"[User]: {content}\n"
            else:
                prompt += f"[Assistant]: {content}\n"
        prompt += "[Assistant]: "
        return prompt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model", required=True)  # np. "mistralai/Mistral-7B-Instruct-v0.3"
    ap.add_argument("--lora_path", required=True)   # folder z adapter_model.safetensors
    ap.add_argument("--max_new_tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--top_p", type=float, default=0.9)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    base = AutoModelForCausalLM.from_pretrained(args.base_model)  # CPU domyślnie
    model = PeftModel.from_pretrained(base, args.lora_path)
    model = model.to("cpu").eval()

    system = "Jesteś Azram — asystent po azramacku. Myśl fraktalnie (Kręgi, Nitki). Odpowiadaj zwięźle."
    history = []
    print("🔮 Azram LoRA (CPU). 'exit' aby zakończyć.")
    while True:
        user_msg = input("\nTy: ").strip()
        if user_msg.lower() in {"exit", "quit"}:
            break
        messages = [{"role":"system","content":system}]
        for u,a in history:
            messages += [{"role":"user","content":u},{"role":"assistant","content":a}]
        messages.append({"role":"user","content":user_msg})

        prompt = build_prompt(tok, messages)
        inputs = tok(prompt, return_tensors="pt")
        streamer = TextStreamer(tok, skip_prompt=True, skip_special_tokens=True)

        output_ids = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            do_sample=True,
            temperature=args.temperature,
            top_p=args.top_p,
            eos_token_id=tok.eos_token_id,
            streamer=streamer,
        )
        text = tok.decode(output_ids[0], skip_special_tokens=True)
        reply = text[len(prompt):].strip()
        print("Azram:", reply)
        history.append((user_msg, reply))

if __name__ == "__main__":
    main()
