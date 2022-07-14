import numpy as np
from transformers import AutoTokenizer
from datasets import load_dataset
from easydict import EasyDict
import yaml

# Read config.yaml file
with open("config.yaml") as infile:
    SAVED_CFG = yaml.load(infile, Loader=yaml.FullLoader)
    CFG = EasyDict(SAVED_CFG["CFG"])

dataset = load_dataset(CFG.dset_name, CFG.task)

# total 13 labels
label_list = [
    "B-PS",
    "I-PS",
    "B-LC",
    "I-LC",
    "B-OG",
    "I-OG",
    "B-DT",
    "I-DT",
    "B-TI",
    "I-TI",
    "B-QT",
    "I-QT",
    "O",
]

print(dataset["train"].features["ner_tags"])

tokenizer = AutoTokenizer.from_pretrained(CFG.PLM)


def label_tokens_ner(examples):
    sentence = "".join(examples["tokens"])
    tokenized_output = tokenizer(
        sentence,
        return_token_type_ids=False,
        return_offsets_mapping=True,
        max_length=512,
        truncation=True,
    )

    label_token_map = []

    list_label = examples["ner_tags"]
    list_label = [-100] + list_label + [-100]
    # print(list_label)
    for token_idx, offset_map in enumerate(tokenized_output["offset_mapping"]):
        begin_letter_idx, end_letter_idx = offset_map
        label_begin = list_label[begin_letter_idx]
        label_end = list_label[end_letter_idx]
        token_label = np.array([label_begin, label_end])
        if label_begin == 12 and label_end == 12:
            token_label = 12
        elif label_begin == -100 and label_end == -100:
            token_label = -100
        else:
            token_label = label_begin if label_begin != 12 else 12
            token_label = label_end if label_end != 12 else 12

        label_token_map.append(token_label)
        # else:
        #   raise ValueError("label_begin != label_end")

    tokenized_output["labels"] = label_token_map
    return tokenized_output


if CFG.DEBUG:
    sample_idx = 0
    data_seg = "train"
    print(dataset[data_seg][sample_idx]["sentence"])
    print("------Labeled output------")
    output = label_tokens_ner(dataset[data_seg][sample_idx])
    for idx, id in enumerate(output["input_ids"]):
        print(idx, tokenizer.convert_ids_to_tokens(output["input_ids"])[idx], output["labels"][idx])

