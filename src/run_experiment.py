import os
import pickle
import argparse

from src.config import AZURE_MODEL_ENDPOINT, AZURE_MODEL_KEY
from src.prompts import SYSTEM_PROMPT_ZERO_SHOT, SYSTEM_PROMPT_FEW_SHOT
from src.core import (
    setup_azure_openai_client,
    setup_inference_client,
    call_batch,
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-pkl", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--backend", choices=["openai", "inference"], default="openai")
    parser.add_argument("--model-name", default="gpt-4o")
    parser.add_argument("--mode", choices=["zero_shot", "few_shot"], default="few_shot")
    parser.add_argument("--save-suffix", default="_fhx")
    parser.add_argument("--only-datasets", nargs="*", default=None)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.results_dir, exist_ok=True)

    with open(args.input_pkl, "rb") as f:
        dataframes = pickle.load(f)

    prompt = SYSTEM_PROMPT_ZERO_SHOT if args.mode == "zero_shot" else SYSTEM_PROMPT_FEW_SHOT

    if args.backend == "openai":
        client = setup_azure_openai_client(AZURE_MODEL_ENDPOINT, AZURE_MODEL_KEY)
    else:
        client = setup_inference_client(AZURE_MODEL_ENDPOINT, AZURE_MODEL_KEY)

    datasets_to_process = {
        k: v for k, v in dataframes.items()
        if args.only_datasets is None or k in args.only_datasets
    }

    for dataset_name, df in datasets_to_process.items():
        out = call_batch(
            df,
            id_col="file_name",
            text_col="content",
            dataset_label=dataset_name,
            prompt=prompt,
            backend=args.backend,
            client=client,
            model_name=args.model_name,
            save_path=args.save_suffix,
            output_dir=args.output_dir,
        )
        out_path = os.path.join(args.results_dir, f"{dataset_name}{args.save_suffix}.csv")
        out.to_csv(out_path, index=False)
        print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()