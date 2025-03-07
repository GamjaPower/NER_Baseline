import os
import random
import torch

from utils.metric import Metric
from utils.dataset import Loader
from utils.preprocessor import Preprocessor

import numpy as np
from transformers import (
    AutoConfig,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
)

import yaml
from dotenv import load_dotenv
from easydict import EasyDict
from model import RobertaWithLinearHead

def main() :
    # Read config.yaml file
    with open("config.yaml") as infile:
        SAVED_CFG = yaml.load(infile, Loader=yaml.FullLoader)
        CFG = EasyDict(SAVED_CFG["CFG"])

    # Seed
    seed_everything(CFG.seed)

    # Loading Datasets
    loader = Loader("config.yaml", CFG.max_token_length)
    datasets = loader.load()

    # Preprocessing Datasets
    preprocessor = Preprocessor()
    datasets = datasets.map(preprocessor, batched=True)

    # Config & Model
    config = AutoConfig.from_pretrained(CFG.PLM)
    config.num_labels = CFG.num_labels

    model = RobertaWithLinearHead.from_pretrained(CFG.PLM, config=config)

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(CFG.PLM)
    
    # Data Collator
    data_collator = DataCollatorForTokenClassification(tokenizer)

    # Wandb
    model_name = CFG.PLM.replace("/", "_")


    run_name = f"{model_name}-finetuned-ner"

    # Train & Eval configs
    training_args = TrainingArguments(
        run_name,
        num_train_epochs=CFG.num_epochs,
        per_device_train_batch_size=CFG.train_batch_size,
        per_device_eval_batch_size=CFG.valid_batch_size,
        gradient_accumulation_steps=CFG.gradient_accumulation_steps,
        learning_rate=CFG.learning_rate,
        weight_decay=CFG.weight_decay,
        warmup_ratio=CFG.warmup_ratio,
        fp16=CFG.fp16,
        evaluation_strategy=CFG.evaluation_strategy,
        save_steps=CFG.save_steps,
        eval_steps=CFG.eval_steps,
        logging_steps=CFG.logging_steps,
        save_strategy=CFG.save_strategy,
        save_total_limit=CFG.num_checkpoints,
        load_best_model_at_end=CFG.load_best_model_at_end,
        metric_for_best_model=CFG.metric_for_best_model,
    )

    # Metrics
    metrics = Metric()

    # Trainer
    trainer = Trainer(
        model,
        training_args,
        train_dataset=datasets["train"],
        eval_dataset=datasets["validation"],
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=metrics.compute_metrics,
    )

    # Training
    trainer.train()
    # Evaluating
    trainer.evaluate()

def seed_everything(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(seed)
    random.seed(seed)

if __name__ == '__main__':
    main()