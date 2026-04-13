from __future__ import annotations

import argparse
from pathlib import Path

import torch

from models import TransformerModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Count parameters for the current Transformer model")
    parser.add_argument("--checkpoint", type=str, default="", help="Optional checkpoint path to validate against")
    parser.add_argument("--input-size", type=int, default=15)
    parser.add_argument("--d-model", type=int, default=64)
    parser.add_argument("--nhead", type=int, default=2)
    parser.add_argument("--num-layers", type=int, default=1)
    parser.add_argument("--output-size", type=int, default=21)
    parser.add_argument("--dropout", type=float, default=0.3)
    return parser.parse_args()


def count_parameters(model: torch.nn.Module) -> tuple[int, int]:
    total = sum(parameter.numel() for parameter in model.parameters())
    trainable = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    return total, trainable


def load_checkpoint_state(checkpoint_path: Path):
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    if isinstance(checkpoint, dict):
        if "model_state" in checkpoint:
            return checkpoint["model_state"], checkpoint
        if "state_dict" in checkpoint:
            return checkpoint["state_dict"], checkpoint
    return checkpoint, None


def main() -> None:
    args = parse_args()

    model = TransformerModel(
        input_size=args.input_size,
        d_model=args.d_model,
        nhead=args.nhead,
        num_layers=args.num_layers,
        output_size=args.output_size,
        dropout=args.dropout,
    )

    total_params, trainable_params = count_parameters(model)

    print("=" * 80)
    print("Current Transformer Parameter Summary")
    print("=" * 80)
    print(f"input_size: {args.input_size}")
    print(f"d_model: {args.d_model}")
    print(f"nhead: {args.nhead}")
    print(f"num_layers: {args.num_layers}")
    print(f"output_size: {args.output_size}")
    print(f"dropout: {args.dropout}")
    print(f"total_parameters: {total_params:,}")
    print(f"trainable_parameters: {trainable_params:,}")

    embedding_params = sum(parameter.numel() for parameter in model.embedding.parameters())
    pos_encoder_params = sum(parameter.numel() for parameter in model.pos_encoder.parameters())
    transformer_encoder_params = sum(parameter.numel() for parameter in model.transformer_encoder.parameters())
    head_params = sum(parameter.numel() for parameter in model.fc.parameters())

    print("\nBreakdown:")
    print(f"- embedding: {embedding_params:,}")
    print(f"- positional_encoding: {pos_encoder_params:,}")
    print(f"- transformer_encoder: {transformer_encoder_params:,}")
    print(f"- classification_head: {head_params:,}")

    if args.checkpoint:
        checkpoint_path = Path(args.checkpoint)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path.resolve()}")

        state_dict, raw_checkpoint = load_checkpoint_state(checkpoint_path)
        model.load_state_dict(state_dict, strict=False)

        print("\nCheckpoint validation:")
        print(f"- checkpoint_path: {checkpoint_path.resolve()}")
        if raw_checkpoint is not None and isinstance(raw_checkpoint, dict):
            print(f"- checkpoint_epoch: {raw_checkpoint.get('epoch', 'unknown')}")
            print(f"- best_val_loss: {raw_checkpoint.get('best_val_loss', 'unknown')}")
            config = raw_checkpoint.get("config", {})
            if isinstance(config, dict) and config:
                print("- checkpoint_config:")
                for key in ["input_size", "d_model", "nhead", "num_layers", "output_size", "dropout"]:
                    if key in config:
                        print(f"  - {key}: {config[key]}")
        print("- state_dict_loaded: yes")


if __name__ == "__main__":
    main()