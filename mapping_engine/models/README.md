# Local model artifacts

This directory holds locally-trained model weights. **Nothing in here is
committed to git** (see the top-level `.gitignore`) — the safetensors
files are too large for the repository and they are reproducible from
the committed code + data.

## Do you need to download or regenerate anything to run the project?

**No.** The default pipeline uses the base embedding model
`BAAI/bge-large-en-v1.5`, which `sentence-transformers` downloads
automatically from the Hugging Face Hub on first use (cached under
`~/.cache/huggingface/`). Every script and test in `mapping_engine/`
loads the model via that name as configured in
`mapping_engine/config/defaults.yaml`.

You only need the contents of this directory if you want to **reproduce
Session 5's contrastive fine-tuning experiment**. The Session 5
benchmark (committed at `data/processed/finetune_benchmark.json`) shows
the fine-tuned model did not improve held-out NIST precision@5 over the
base model, so the project default is unchanged.

## How to regenerate `finetuned-crosswalk-v1/`

Two commands, ~2 minutes on a GPU machine (Jetson AGX Orin or similar):

```bash
# Optional — the JSON files are already committed under data/processed/
python -m mapping_engine.scripts.build_finetune_data

# Trains BAAI/bge-large-en-v1.5 with MultipleNegativesRankingLoss
# on 198 (anchor, positive, negative) triplets, fp16, 2 epochs.
python -m mapping_engine.scripts.finetune_embedding --epochs 2 --batch_size 8
```

The script writes the model to
`mapping_engine/models/finetuned-crosswalk-v1/` and a metric summary to
`final_eval.json`.

## How to use the fine-tuned model in the pipeline

After regenerating, point `defaults.yaml` (or a per-pair override) at
the local path:

```yaml
semantic:
  model: mapping_engine/models/finetuned-crosswalk-v1
```

`mapping_engine.engine.semantic._load_model` passes any string straight
to `SentenceTransformer(...)`, which natively accepts both Hugging Face
model IDs and local directory paths.
