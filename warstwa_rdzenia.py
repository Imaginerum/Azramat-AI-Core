# warstwa_rdzenia.py
import torch
from dataclasses import dataclass, field
from typing import Iterable, List, Dict, Optional, Generator
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, StoppingCriteriaList
)
from peft import PeftModel

# ——— Interfejsy danych ———

@dataclass
class CoreConfig:
    base_model: str
    lora_path: Optional[str] = None
    load_4bit: bool = False
    load_8bit: bool = False
    int8_cpu_offload: bool = False
    trust_remote_code: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    max_new_tokens: int = 2048
    min_new_tokens: int = 16
    repetition_penalty: float = 1.02
    no_repeat_ngram_size: int = 3

@dataclass
class CoreRequest:
    # gotowy prompt (już po adaptacji)
    prompt_text: str
    # ograniczenia kontekstu
    ctx_budget: int
    # opcjonalny StoppingCriteria – np. stop na Ctrl+C
    stopping: Optional[StoppingCriteriaList] = None

@dataclass
class CoreReply:
    text: str
    tokens_used: int
    truncated: bool = False
    meta: Dict = field(default_factory=dict)

# ——— Silnik ———

class CoreEngine:
    def __init__(self, cfg: CoreConfig):
        self.cfg = cfg
        self.model, self.tok = self._load()

    def _load(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        import torch

        # UWAGA: żadnych llm_int8_enable_fp32_cpu_offload w kwargs!
        kwargs = dict(
            trust_remote_code=self.cfg.trust_remote_code,
            device_map="auto",
            dtype=torch.float16,          # zamiast torch_dtype
            low_cpu_mem_usage=True,
        )

        quant = None
        if self.cfg.load_4bit:
            quant = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.float16,
            )
        elif self.cfg.load_8bit:
            quant = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_enable_fp32_cpu_offload=bool(self.cfg.int8_cpu_offload),
            )

        if quant is not None:
            kwargs["quantization_config"] = quant

        # 👇 Bez żadnych dodatkowych kluczy w kwargs
        model = AutoModelForCausalLM.from_pretrained(self.cfg.base_model, **kwargs)

        try:
            tok = AutoTokenizer.from_pretrained(self.cfg.base_model, use_fast=True)
        except Exception:
            tok = AutoTokenizer.from_pretrained(self.cfg.base_model, use_fast=False)

        # Jeśli PODAJESZ adapter LoRA – tylko wtedy:
        if self.cfg.lora_path:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, self.cfg.lora_path)

        if tok.pad_token_id is None:
            tok.pad_token = tok.eos_token

        return model.eval(), tok


    def _device(self):
        return next(self.model.parameters()).device

    def _calc_avail(self, input_len: int, ctx_budget: int) -> int:
        return max(96, ctx_budget - input_len - 128)

    # ——— jednorazowa generacja (bez streamu) ———
    def think(self, req: CoreRequest) -> CoreReply:
        device = self._device()
        inputs = self.tok(req.prompt_text, return_tensors="pt", truncation=True, max_length=req.ctx_budget)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        prompt_len = inputs["input_ids"].shape[1]
        this_max_new = min(self.cfg.max_new_tokens, self._calc_avail(prompt_len, req.ctx_budget))

        with torch.inference_mode():
            out = self.model.generate(
                **inputs,
                max_new_tokens=this_max_new,
                min_new_tokens=self.cfg.min_new_tokens,
                do_sample=True,
                temperature=max(0.4, min(0.9, self.cfg.temperature)),
                top_p=self.cfg.top_p,
                repetition_penalty=self.cfg.repetition_penalty,
                no_repeat_ngram_size=self.cfg.no_repeat_ngram_size,
                eos_token_id=self.tok.eos_token_id,
                pad_token_id=self.tok.pad_token_id,
                stopping_criteria=req.stopping or StoppingCriteriaList([]),
            )
        text = self.tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return CoreReply(text=text.strip(), tokens_used=int(out.shape[1]), truncated=False)

    # ——— streaming tokenów ———
    def think_stream(self, req: CoreRequest) -> Generator[str, None, None]:
        device = self._device()
        inputs = self.tok(req.prompt_text, return_tensors="pt", truncation=True, max_length=req.ctx_budget)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        prompt_len = inputs["input_ids"].shape[1]
        this_max_new = min(self.cfg.max_new_tokens, self._calc_avail(prompt_len, req.ctx_budget))

        streamer = TextIteratorStreamer(self.tok, skip_prompt=True, skip_special_tokens=True)

        import threading
        def _worker():
            try:
                with torch.inference_mode():
                    self.model.generate(
                        **inputs,
                        max_new_tokens=this_max_new,
                        min_new_tokens=self.cfg.min_new_tokens,
                        do_sample=True,
                        temperature=max(0.4, min(0.9, self.cfg.temperature)),
                        top_p=self.cfg.top_p,
                        repetition_penalty=self.cfg.repetition_penalty,
                        no_repeat_ngram_size=self.cfg.no_repeat_ngram_size,
                        eos_token_id=self.tok.eos_token_id,
                        pad_token_id=self.tok.pad_token_id,
                        streamer=streamer,
                        stopping_criteria=req.stopping or StoppingCriteriaList([]),
                    )
            except Exception:
                try:
                    streamer.end()
                except Exception:
                    pass

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        for piece in streamer:
            yield piece
