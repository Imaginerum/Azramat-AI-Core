from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, TaskType
import torch

MODEL_NAME = "speakleash/Bielik-11B-v2.3-Instruct"
DATA_PATH = "azramai_dataset.jsonl"

# Tokenizer i dane
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
dataset = load_dataset("json", data_files=DATA_PATH, split="train")

def tokenize(example):
    return tokenizer(f"{example['prompt']}\n{example['completion']}", truncation=True, padding="max_length", max_length=512)

dataset = dataset.map(tokenize)

# Konfiguracja LoRA
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

# Model bazowy
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float32)
model = get_peft_model(model, lora_config)

# Argumenty treningowe
training_args = TrainingArguments(
    output_dir="azramai_bielik_lora",
    num_train_epochs=3,
    per_device_train_batch_size=1,
    logging_steps=10,
    save_strategy="epoch",
    learning_rate=1e-4,
    fp16=False,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

trainer.train()
