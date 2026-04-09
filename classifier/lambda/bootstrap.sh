#!/bin/bash
# classifier/lambda/bootstrap.sh
# Run on Lambda instance after SSH connection established.
# Expects WANDB_API_KEY and HF_TOKEN as environment variables.
set -euo pipefail

echo "=== Lambda Bootstrap: crosswalk-v2 ==="

# Clone repo (or pull if already present from rsync)
if [ -d ~/crosswalk/.git ]; then
    echo "Repo exists, pulling latest..."
    cd ~/crosswalk && git pull
else
    echo "Cloning repo..."
    git clone https://github.com/rocklambros/ai-security-framework-crosswalk.git ~/crosswalk
    cd ~/crosswalk
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --quiet -r classifier/lambda/requirements-lambda.txt

# Login to WANDB
echo "Logging in to WANDB..."
wandb login "$WANDB_API_KEY"

# Login to HuggingFace
echo "Logging in to HuggingFace..."
huggingface-cli login --token "$HF_TOKEN" --add-to-git-credential

# Pre-download transformer models (so training doesn't stall on download)
echo "Pre-downloading transformer models..."
python -c "
from transformers import AutoTokenizer, AutoModel
models = [
    'microsoft/deberta-v3-large',
    'roberta-large',
    'google/electra-large-discriminator',
]
for m in models:
    print(f'  Downloading {m}...')
    AutoTokenizer.from_pretrained(m)
    AutoModel.from_pretrained(m)
print('All models downloaded.')
"

echo "=== Bootstrap complete ==="
