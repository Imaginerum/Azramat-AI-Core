import os, io, argparse, torch, json, shutil

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"  # anty-fragmentacja

from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, DataCollatorForLanguageModeling, Trainer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, PeftModel, prepare_model_for_kbit_training
import math, sys

# próba użycia safetensors (zalecane); jeśli brak, fallback do torch
try:
    from safetensors.torch import load_file as st_load, save_file as st_save
    HAVE_ST = True
except Exception:
    HAVE_ST = False

# wyciszenie ostrzeżenia tokenizers przy forku DataLoadera
torch.set_num_threads(60)   
torch.set_num_interop_threads(4) 

def merge_lora_adapters(lora_a_dir, lora_b_dir, out_dir, w_a=0.5, w_b=0.5):
    """
    Tworzy nowy adapter z uśrednionych wag LoRA (w_a : w_b).
    Oryginały w lora_a_dir i lora_b_dir zostają nietknięte.
    """
    os.makedirs(out_dir, exist_ok=True)

    # wczytaj pliki wag
    st_path_a = os.path.join(lora_a_dir, "adapter_model.safetensors")
    st_path_b = os.path.join(lora_b_dir, "adapter_model.safetensors")
    pt_path_a = os.path.join(lora_a_dir, "adapter_model.bin")
    pt_path_b = os.path.join(lora_b_dir, "adapter_model.bin")

    if HAVE_ST and os.path.exists(st_path_a) and os.path.exists(st_path_b):
        A = st_load(st_path_a)
        B = st_load(st_path_b)
        use_st = True
    else:
        A = torch.load(st_path_a if os.path.exists(st_path_a) else pt_path_a, map_location="cpu")
        B = torch.load(st_path_b if os.path.exists(st_path_b) else pt_path_b, map_location="cpu")
        use_st = False

    # merge przez uśrednianie klucz-po-kluczu
    merged = {}
    keys = set(A.keys()) | set(B.keys())
    for k in keys:
        if k in A and k in B and torch.is_tensor(A[k]) and torch.is_tensor(B[k]):
            # 1:1 → w_a = w_b = 0.5 (domyślnie)
            merged[k] = (A[k] * w_a + B[k] * w_b).to(dtype=A[k].dtype)
        elif k in A:
            merged[k] = A[k]
        else:
            merged[k] = B[k]

    # skopiuj config adaptera (weź z A — zakładamy zgodny target_modules)
    for cfg_name in ["adapter_config.json", "adapter_model.json"]:
        src_cfg = os.path.join(lora_a_dir, cfg_name)
        if os.path.exists(src_cfg):
            shutil.copy2(src_cfg, os.path.join(out_dir, cfg_name))

    # zapisz w preferowanym formacie
    if use_st:
        st_save(merged, os.path.join(out_dir, "adapter_model.safetensors"))
    else:
        torch.save(merged, os.path.join(out_dir, "adapter_model.bin"))

    print(f"✅ MERGE DONE → {out_dir}")

def build_ds(txt_path, tok, max_seq_len=1024, val_ratio=0.02):
    with io.open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    enc = tok(text, add_special_tokens=False)
    ids = enc["input_ids"]
    eos = tok.eos_token_id or tok.convert_tokens_to_ids("</s>")
    blocks = []
    for i in range(0, len(ids), max_seq_len):
        chunk = ids[i:i+max_seq_len]
        # domknij sekwencję tokenem EOS (opcjonalnie, bezpieczne)
        if len(chunk) == max_seq_len and eos is not None:
            chunk[-1] = eos
        blocks.append(chunk[:max_seq_len])
    # odfiltruj bardzo krótkie
    blocks = [b for b in blocks if len(b) >= max_seq_len // 4]
    n = len(blocks); n_val = max(1, int(n * val_ratio))
    train = blocks[:-n_val] if n_val < n else blocks
    val   = blocks[-n_val:] if n_val < n else blocks[:1]
    to_text = lambda arr: [tok.decode(b, skip_special_tokens=False) for b in arr]
    return DatasetDict({
        "train": Dataset.from_dict({"text": to_text(train)}),
        "validation": Dataset.from_dict({"text": to_text(val)})
    })

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", required=True)
    ap.add_argument("--data_txt",  required=True)
    ap.add_argument("--out_dir",   default="~/outputs/bielik11b-lora")
    ap.add_argument("--max_seq_len", type=int, default=1024)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch_size", type=int, default=1)
    ap.add_argument("--grad_accum", type=int, default=8)
    ap.add_argument("--lora_r", type=int, default=8)
    ap.add_argument("--lora_alpha", type=int, default=16)
    ap.add_argument("--lora_dropout", type=float, default=0.05)
    ap.add_argument("--resume_lora_dir", default=None, help="Opcjonalnie: załaduj istniejący LoRA i KONTYNUUJ trening (oryginał nie jest nadpisany).")
    ap.add_argument("--merge_with_lora", default=None, help="Ścieżka do drugiego LoRA do MERGE po treningu.")
    ap.add_argument("--merge_out_dir", default=None, help="Gdzie zapisać wynik MERGE dwóch LoRA.")
    ap.add_argument("--merge_weights", default="0.5,0.5", help="Wagi MERGE, np. '0.5,0.5' dla 1:1 albo '0.7,0.3'.")

    args = ap.parse_args()

    model_dir = os.path.expanduser(args.model_dir)
    out_dir   = os.path.expanduser(args.out_dir)
    data_txt  = os.path.expanduser(args.data_txt)
    os.makedirs(out_dir, exist_ok=True)

    # Tokenizer
    tok = AutoTokenizer.from_pretrained(model_dir, use_fast=True)
    tok.padding_side = "right"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    # Dataset z jednego TXT
    ds = build_ds(data_txt, tok, args.max_seq_len, 0.02)

    # Model (4-bit + auto device map)
    

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=(
            torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported())
            else torch.float16
        )
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_dir,
        quantization_config=bnb_config,
        device_map="auto"      # ← klucz: pozwól Accelerate rozłożyć, nie wywołuj model.to(...)
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)


    # szybki test (opcjonalnie)
    p = next(iter(model.state_dict().values()))
    print("🧩 device:", p.device, "| dtype:", p.dtype)


    # wycisz warning i oszczędzaj RAM

    # LoRA: start od istniejącego adaptera LUB od nowego
    if args.resume_lora_dir:
        model = PeftModel.from_pretrained(model, os.path.expanduser(args.resume_lora_dir))
        print(f"🔁 Kontynuuję LoRA z: {args.resume_lora_dir}")
    else:
        lora = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]
        )
        model = get_peft_model(model, lora)

    # (1) WYMUSZENIE TRENOWALNOŚCI ADAPTERÓW (na niektórych wersjach bywa potrzebne)
    for n, p in model.named_parameters():
        if ("lora_" in n) or ("adapter_" in n):
            p.requires_grad_(True)

    # (2) Gradient checkpointing WŁAŚNIE TERAZ (po PEFT), nie przed:
    model.config.use_cache = False
    try:
        model.gradient_checkpointing_enable()
    except Exception:
        pass

    model.train()
    model.print_trainable_parameters()



    # Trener
    collator = DataCollatorForLanguageModeling(tok, mlm=False)
    # === TOKENIZACJA DATASETU ===
    def tok_map(batch):
        return tok(
            batch["text"],
            truncation=True,
            max_length=args.max_seq_len,
            padding=False,            # bez paddingu; zrobi to collator
            return_attention_mask=True
        )

    tokenized = ds.map(tok_map, batched=True, remove_columns=["text"])

    use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    fp16_flag = torch.cuda.is_available() and not use_bf16
    bf16_flag = use_bf16

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=out_dir,
            save_safetensors=True,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.grad_accum,
            learning_rate=args.lr,
            lr_scheduler_type="cosine",
            warmup_ratio=0.03,
            logging_steps=1,
            save_steps=50,
            save_total_limit=2,
            gradient_checkpointing=True,
            gradient_checkpointing_kwargs={"use_reentrant": False},
            fp16=fp16_flag,
            bf16=bf16_flag,
            tf32=True,
            group_by_length=True,
            optim="adamw_torch",   # (opcjonalnie: "paged_adamw_8bit" jeśli chcesz jeszcze mniej VRAM)
            report_to="none",
            dataloader_num_workers=0,
            dataloader_pin_memory=False,
        ),
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        data_collator=collator,
        tokenizer=tok,
    )


    trainer.train()
    trainer.save_model(out_dir)
    # Opcjonalny MERGE dwóch LoRA po treningu (1:1 domyślnie)
    if args.merge_with_lora and args.merge_out_dir:
        w = [float(x) for x in args.merge_weights.split(",")]
        assert len(w) == 2 and abs(sum(w) - 1.0) < 1e-6, "merge_weights powinno mieć dwie liczby sumujące się do 1.0, np. '0.5,0.5'."
        merge_lora_adapters(
            lora_a_dir=os.path.expanduser(args.merge_with_lora),
            lora_b_dir=out_dir,
            out_dir=os.path.expanduser(args.merge_out_dir),
            w_a=w[0], w_b=w[1]
        )

    tok.save_pretrained(out_dir)
    print("✅ DONE:", out_dir)

if __name__ == "__main__":
    main()
