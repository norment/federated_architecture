#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

from common import make_result_summary
from nvflare.app_common.np.recipes import NumpyFedAvgRecipe
from nvflare.app_common.np.constants import NPConstants
from nvflare.app_common.aggregators.model_aggregator import ModelAggregator
from nvflare.apis.fl_constant import FLContextKey
from nvflare.apis.fl_context import FLContext
from nvflare.client import FLModel
from nvflare.recipe import ProdEnv, SimEnv


def _get_run_dir(fl_ctx: FLContext):
    job_id = fl_ctx.get_job_id()
    workspace = fl_ctx.get_prop(FLContextKey.WORKSPACE_OBJECT)
    return workspace.get_run_dir(job_id)


class RegressionAggregator(ModelAggregator):
    def __init__(self, output_folder="server_results"):
        super().__init__()
        self.output_folder = output_folder
        self.local_stats = []
        self.received_params_type = None

    def accept_model(self, model: FLModel):
        if self.received_params_type is None:
            self.received_params_type = model.params_type

        params = model.params or {}
        if params.get("SUCCESS") is False:
            site_name = model.meta.get("site_name", "unknown_site")
            error_message = model.meta.get("error_message", "unknown error")
            print(f"ERROR: site {site_name} failed: {error_message}")
            return

        stats = model.meta.get("local_stats")
        if not stats:
            site_name = model.meta.get("site_name", "unknown_site")
            print(f"WARNING: no local_stats received from {site_name}")
            return

        self.local_stats.append(stats)
        print(f"Accepted statistics from {stats['site_name']} with n={stats['n']}")

    def aggregate_model(self) -> FLModel:
        summary = make_result_summary(self.local_stats)
        output_dir = None

        try:
            job_dir = _get_run_dir(self.fl_ctx)
            output_dir = Path(job_dir) / self.output_folder
            output_dir.mkdir(parents=True, exist_ok=True)
            summary_path = output_dir / "hello_regression_summary.json"
            summary_path.write_text(json.dumps(summary, indent=2))
            print(f"Wrote summary to {summary_path}")
        except Exception as exc:
            print(f"WARNING: failed to write summary file: {exc}")

        print("Estimated coefficients:")
        for name, value, se in zip(
            summary["feature_names"], summary["estimated_beta"], summary["standard_error"]
        ):
            print(f"  {name}: beta={value:.4f}, se={se:.4f}")

        return FLModel(
            params={
                NPConstants.NUMPY_KEY: summary["estimated_beta"],
            },
            params_type=self.received_params_type,
            meta={
                "summary": summary,
                "output_folder": str(output_dir) if output_dir else None,
                "standard_error": summary["standard_error"],
                "total_samples": summary["total_samples"],
            },
        )

    def reset_stats(self):
        self.local_stats = []
        self.received_params_type = None


def parse_args():
    parser = argparse.ArgumentParser(description="Run the hello_regression federated example.")
    parser.add_argument("--env", choices=["sim", "prod"], default="sim")
    parser.add_argument("--n_clients", type=int, default=2, help="Minimum clients required for the job.")
    parser.add_argument("--num_rounds", type=int, default=1, help="Regression example uses one round by default.")
    parser.add_argument(
        "--startup_kit",
        type=str,
        default=None,
        help="Admin startup kit location for prod runs.",
    )
    parser.add_argument(
        "--username",
        type=str,
        default="admin@demo.org",
        help="Admin username for prod runs.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    work_dir = Path(__file__).resolve().parent
    os.chdir(work_dir)

    recipe = NumpyFedAvgRecipe(
        name="hello_regression",
        model=[0.0, 0.0, 0.0, 0.0],
        min_clients=args.n_clients,
        num_rounds=args.num_rounds,
        train_script="client.py",
        aggregator=RegressionAggregator(),
    )
    recipe.job.to_clients("site_runner.py")
    recipe.job.to_clients("common.py")

    if args.env == "sim":
        env = SimEnv(num_clients=args.n_clients)
    else:
        if not args.startup_kit:
            raise ValueError("--startup_kit is required for --env prod")
        env = ProdEnv(
            startup_kit_location=args.startup_kit,
            username=args.username,
            login_timeout=300,
        )

    run = recipe.execute(env)
    print(f"Job status: {run.get_status()}")
    print(f"Job result: {run.get_result()}")


if __name__ == "__main__":
    main()
