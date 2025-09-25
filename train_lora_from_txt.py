import os, io, argparse, torch
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer
import torch, os

# wyciszenie ostrzeżenia tokenizers przy forku DataLoadera
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "") 
torch.set_num_threads(60)   
torch.set_num_interop_threads(4) 

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

    # Model (CPU)
    model = AutoModelForCausalLM.from_pretrained(
        model_dir,
        torch_dtype=torch.float32,
        device_map=None
    )
    model = model.to("cpu")    
    # wycisz warning i oszczędzaj RAM
    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    # LoRA
    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    # Trener
    collator = DataCollatorForLanguageModeling(tok, mlm=False)
    trainer = SFTTrainer(
        model=model,
        train_dataset=ds["train"],
        eval_dataset=ds["validation"],
        dataset_text_field="text",
        tokenizer=tok,
        data_collator=collator,
        packing=True,
        max_seq_length=args.max_seq_len,
        args=TrainingArguments(
            output_dir=out_dir,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.grad_accum,
            learning_rate=args.lr,
            lr_scheduler_type="cosine",
            warmup_ratio=0.03,
            logging_steps=1,
            evaluation_strategy="steps",      # w 4.44 działa; w 4.46 zmień na eval_strategy
            eval_steps=50,
            save_steps=50,
            save_total_limit=2,
            gradient_checkpointing=True,
            gradient_checkpointing_kwargs={"use_reentrant": False},  # wycisza warning Torch 2.5
            fp16=False, bf16=False,          # CPU
            optim="adamw_torch",
            report_to="none",
            dataloader_num_workers=0,        # zero, by uniknąć ostrzeżeń forka/parallelism
            dataloader_pin_memory=False, 
        ),
    )
    trainer.train()
    trainer.save_model(out_dir)
    tok.save_pretrained(out_dir)
    print("✅ DONE:", out_dir)

if __name__ == "__main__":
    main()
