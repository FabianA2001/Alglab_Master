"""
Script to find optimal parameters for Large Neighborhood Search (LNS) algorithm.

This module provides functions to systematically test different parameter combinations
for the LNS solver and find the optimal configuration for a given instance.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from ..inputTypes import instace
from ..parseData import parseTXT
from . import lns


@dataclass
class LNSParameters:
    """Parameters for LNS algorithm"""

    percent_search_time_first_solution: Optional[float] = None
    timeout_seconds: Optional[float] = None
    small_runtime_base: Optional[float] = None
    start_search_window_size: Optional[int] = None
    search_window_size_min: Optional[int] = None
    window_increase_factor: Optional[float] = None
    window_decrease_factor: Optional[float] = None
    strong_improvement_threshold: Optional[float] = None

    def to_dict(self):
        """Convert to dict, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class TestConfig:
    """Configuration for a test run"""

    instance_name: str
    instance_path: str
    parameters: LNSParameters
    timestamp: str
    run_id: int

    def to_dict(self):
        return {
            "instance_name": self.instance_name,
            "instance_path": self.instance_path,
            "parameters": self.parameters.to_dict(),
            "timestamp": self.timestamp,
            "run_id": self.run_id,
        }


@dataclass
class TestResult:
    """Result of a single LNS test run"""

    run_id: int
    instance_name: str
    parameters: dict
    objective_value: float
    solve_status: str
    runtime_seconds: float
    iterations: int
    improvements: int
    timestamp: str
    log_file: str

    def to_dict(self):
        return asdict(self)


class LNSParameterTester:
    """Main class for testing LNS parameters"""

    def __init__(
        self,
        output_base_dir: Path = Path("lns_parameter_tests"),
        log_level: int = logging.INFO,
    ):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        self.log_level = log_level
        self.run_counter = 0
        self.batch_dir = None  # Will be set in run_parameter_grid

    def _create_batch_directory(self) -> Path:
        """Create a directory for a batch of parameter tests"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = self.output_base_dir / f"batch_{timestamp}"
        batch_dir.mkdir(parents=True, exist_ok=True)
        return batch_dir

    def _setup_logger(self, run_dir: Path, run_id: int) -> tuple[logging.Logger, str]:
        """Setup logger for a specific run"""
        log_file = run_dir / f"run_{run_id}.log"

        logger = logging.getLogger(f"LNS_Test_{run_id}")
        logger.setLevel(self.log_level)
        logger.handlers = []  # Clear existing handlers
        logger.propagate = False  # Don't propagate to parent loggers

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # No console handler - only file logging

        return logger, str(log_file)

    def _save_config(self, config: TestConfig, batch_dir: Path):
        """Save test configuration to JSON file"""
        config_file = batch_dir / f"config_run_{config.run_id}.json"
        with open(config_file, "w") as f:
            json.dump(config.to_dict(), f, indent=2)

    def _save_result(self, result: TestResult, batch_dir: Path):
        """Save test result to JSON file"""
        result_file = batch_dir / f"result_run_{result.run_id}.json"
        with open(result_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

    def _load_instance(self, instance_path: Path) -> instace.Instance:
        """Load instance from file"""
        if instance_path.suffix == ".txt":
            return parseTXT.parse_txt(instance_path)
        else:
            raise ValueError(f"Unsupported instance format: {instance_path.suffix}")

    def run_single_test(
        self,
        instance_path: Path,
        parameters: LNSParameters,
        batch_dir: Optional[Path] = None,
    ) -> TestResult:
        """Run a single LNS test with given parameters"""
        import time

        if batch_dir is None:
            batch_dir = self._create_batch_directory()

        run_id = self.run_counter
        self.run_counter += 1
        instance_name = instance_path.stem
        timestamp = datetime.now().isoformat()

        # Setup logger
        logger, log_file = self._setup_logger(batch_dir, run_id)

        # Create and save config
        config = TestConfig(
            instance_name=instance_name,
            instance_path=str(instance_path),
            parameters=parameters,
            timestamp=timestamp,
            run_id=run_id,
        )
        self._save_config(config, batch_dir)

        logger.info(f"Starting LNS test run {run_id}")
        logger.info(f"Instance: {instance_name}")
        logger.info(f"Parameters: {parameters.to_dict()}")

        # Load instance
        logger.info("Loading instance...")
        instance = self._load_instance(instance_path)

        # Create LNS with parameters (only pass non-None values)
        logger.info("Creating LNS solver...")
        lns_kwargs = parameters.to_dict()
        lns_kwargs["logger"] = logger
        lns_kwargs["log_level"] = logging.DEBUG

        # Disable all console output from root logger
        logging.getLogger().handlers = []

        start_time = time.time()
        lns_solver = lns.LNS(instance, **lns_kwargs)

        # Solve
        logger.info("Starting LNS solve...")
        solution = lns_solver.solve()
        runtime = time.time() - start_time

        logger.info(f"LNS solve completed in {runtime:.2f} seconds")
        logger.info(f"Final objective value: {solution.objective_value}")

        # Create result
        result = TestResult(
            run_id=run_id,
            instance_name=instance_name,
            parameters=parameters.to_dict(),
            objective_value=solution.objective_value,
            solve_status=str(solution.solve_status),
            runtime_seconds=runtime,
            iterations=0,  # Would need to be tracked in LNS
            improvements=0,  # Would need to be tracked in LNS
            timestamp=timestamp,
            log_file=str(log_file),
        )

        # Save result
        self._save_result(result, batch_dir)
        logger.info(f"Results saved to {batch_dir}")

        return result

    def run_parameter_grid(
        self,
        instances: list[Path],
        parameter_grid: dict[str, list],
    ) -> list[TestResult]:
        """
        Run tests for all combinations of parameters and instances

        Args:
            instances: List of instance file paths
            parameter_grid: Dict mapping parameter names to lists of values to test
                Example: {
                    'timeout_seconds': [60, 120, 180],
                    'start_search_window_size': [5, 7, 10],
                    'window_increase_factor': [1.2, 1.3, 1.5]
                }

        Returns:
            List of TestResult objects
        """
        results = []

        # Create one batch directory for all tests in this grid
        batch_dir = self._create_batch_directory()

        # Setup batch logger (file only, no console)
        batch_logger = logging.getLogger(f"LNS_Batch_{batch_dir.name}")
        batch_logger.setLevel(self.log_level)
        batch_logger.handlers = []
        batch_logger.propagate = False  # Don't propagate to parent loggers

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Batch log file only
        batch_log_file = batch_dir / "batch.log"
        file_handler = logging.FileHandler(batch_log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        batch_logger.addHandler(file_handler)

        # Save parameter grid info
        grid_info = {
            "parameter_grid": parameter_grid,
            "instances": [str(p) for p in instances],
            "timestamp": datetime.now().isoformat(),
        }
        with open(batch_dir / "parameter_grid.json", "w") as f:
            json.dump(grid_info, f, indent=2)

        # Generate all parameter combinations
        param_names = list(parameter_grid.keys())
        param_values = list(parameter_grid.values())

        total_combinations = len(list(product(*param_values))) * len(instances)
        batch_logger.info("=" * 80)
        batch_logger.info(f"Starting new batch: {batch_dir.name}")
        batch_logger.info(
            f"Testing {total_combinations} combinations "
            f"({len(instances)} instances × {len(list(product(*param_values)))} parameter sets)"
        )
        batch_logger.info("=" * 80)

        # Calculate maximum possible time
        max_timeout = max(parameter_grid.get("timeout_seconds", [180]))
        max_time_seconds = total_combinations * max_timeout
        max_hours = int(max_time_seconds // 3600)
        max_minutes = int((max_time_seconds % 3600) // 60)

        print(f"\n🚀 Starting batch: {batch_dir.name}")
        print(f"📊 Total tests: {total_combinations}")
        print(f"⏱️  Max time per test: {max_timeout}s")
        print(f"⏰ Estimated max duration: {max_hours}h {max_minutes}m")
        print()

        # Create tqdm progress bar
        pbar = tqdm(
            total=total_combinations,
            desc="Testing LNS parameters",
            unit="test",
            ncols=100,
        )

        combination_count = 0
        for instance_path in instances:
            for param_combination in product(*param_values):
                combination_count += 1
                batch_logger.info("=" * 80)
                batch_logger.info(
                    f"Running test {combination_count}/{total_combinations}: "
                    f"{instance_path.name}"
                )
                batch_logger.info("=" * 80)

                # Update progress bar description
                pbar.set_description(f"Testing {instance_path.stem}")

                # Create parameter object
                param_dict = dict(zip(param_names, param_combination))
                parameters = LNSParameters(**param_dict)

                # Run test (all in same batch directory)
                try:
                    result = self.run_single_test(instance_path, parameters, batch_dir)
                    results.append(result)
                    pbar.set_postfix(
                        {"objective": f"{result.objective_value:.1f}", "status": "✓"},
                        refresh=False,
                    )
                except Exception as e:
                    batch_logger.error(f"Error in test run: {e}")
                    import traceback

                    batch_logger.error(traceback.format_exc())
                    pbar.set_postfix({"status": "✗ ERROR"}, refresh=False)

                pbar.update(1)

        pbar.close()

        batch_logger.info("=" * 80)
        batch_logger.info(f"All tests completed! Total runs: {len(results)}")
        batch_logger.info(f"Results saved to: {batch_dir}")
        batch_logger.info("=" * 80)

        # Print summary to console
        print(f"\n✅ Completed {len(results)}/{total_combinations} test runs")
        print(f"📁 Results saved to: {batch_dir}")

        return results


def main():
    """Example usage of the parameter tester"""

    # Define instances to test
    instance_dir = Path("data/instance_raw")
    instances = [
        instance_dir / "Instance9.txt",
    ]

    # Define parameter grid
    parameter_grid = {
        "timeout_seconds": [120],
        "strong_improvement_threshold": [0.01, 0.05, 0.005],
        "small_runtime_base": [0.01, 0.02, 0.005],
    }

    # Create tester
    tester = LNSParameterTester(
        output_base_dir=Path("lns_parameter_tests"), log_level=logging.INFO
    )

    # Setup logger for main
    logger = logging.getLogger("LNS_Main")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    logger.addHandler(handler)

    # Run all tests
    results = tester.run_parameter_grid(instances, parameter_grid)

    logger.info(f"Completed {len(results)} test runs")


if __name__ == "__main__":
    main()
