"""
Script to find optimal parameters for Large Neighborhood Search (LNS) algorithm.

This module provides functions to systematically test different parameter combinations
for the LNS solver and find the optimal configuration for a given instance.
"""

import itertools
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..inputTypes import instace
from ..solution import Solution
from . import lns


def setup_run_logger(
    run_index: int, log_dir: Path, instance_name: str
) -> logging.Logger:
    """
    Create a separate logger for each run with its own log file.

    Args:
        run_index: Index of the current run
        log_dir: Directory to save log files
        instance_name: Name of the instance being solved

    Returns:
        Configured logger for this run
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"run_{run_index:04d}_{instance_name}.log"

    # Create a unique logger for this run
    logger = logging.getLogger(f"lns_run_{run_index}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Don't propagate to root logger

    # Remove any existing handlers
    logger.handlers.clear()

    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler for important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


@dataclass
class ParameterConfig:
    """Configuration for LNS parameters to test."""

    percent_search_time_first_solution: float = 0.1
    timeout_seconds: float = 180
    small_runtime_base: float = 0.01
    start_search_window_size: int = 7
    search_window_size_min: int = 3
    window_increase_factor: float = 1.5
    window_decrease_factor: float = 0.8
    strong_improvement_threshold: float = 0.01

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "percent_search_time_first_solution": self.percent_search_time_first_solution,
            "timeout_seconds": self.timeout_seconds,
            "small_runtime_base": self.small_runtime_base,
            "start_search_window_size": self.start_search_window_size,
            "search_window_size_min": self.search_window_size_min,
            "window_increase_factor": self.window_increase_factor,
            "window_decrease_factor": self.window_decrease_factor,
            "strong_improvement_threshold": self.strong_improvement_threshold,
        }


@dataclass
class TestResult:
    """Result of a parameter test run."""

    config: ParameterConfig
    objective_value: float
    runtime_seconds: float
    solve_status: str
    instance_name: str
    run_index: int = -1
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "run_index": self.run_index,
            "config": self.config.to_dict(),
            "objective_value": self.objective_value,
            "runtime_seconds": self.runtime_seconds,
            "solve_status": self.solve_status,
            "instance_name": self.instance_name,
            "timestamp": self.timestamp,
        }


def test_parameter_config(
    instance: instace.Instance,
    config: ParameterConfig,
    run_index: int = -1,
    log_dir: Path | None = None,
    logger: logging.Logger | None = None,
) -> tuple[TestResult, Solution]:
    """
    Test a single parameter configuration on the given instance.

    Args:
        instance: The scheduling instance to solve
        config: The parameter configuration to test
        run_index: Index of this run (for logging purposes)
        log_dir: Directory to save log files (if None, uses provided logger)
        logger: Optional logger for detailed output (ignored if log_dir is provided)

    Returns:
        Tuple of (TestResult, solution) containing the outcome of the test and the solution
    """
    # Create run-specific logger if log_dir is provided
    if log_dir is not None:
        logger = setup_run_logger(run_index, log_dir, instance.name)
    elif logger is None:
        logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info(f"RUN INDEX: {run_index}")
    logger.info(f"Instance: {instance.name}")
    logger.info(f"Testing configuration: {config.to_dict()}")
    logger.info("=" * 80)

    start_time = time.time()

    try:
        lns_solver = lns.LNS(
            instance,
            percent_search_time_first_solution=config.percent_search_time_first_solution,
            timeout_seconds=config.timeout_seconds,
            small_runtime_base=config.small_runtime_base,
            start_search_window_size=config.start_search_window_size,
            search_window_size_min=config.search_window_size_min,
            window_increase_factor=config.window_increase_factor,
            window_decrease_factor=config.window_decrease_factor,
            strong_improvement_threshold=config.strong_improvement_threshold,
            logger=logger,
            log_level=logging.INFO,
        )

        solution = lns_solver.solve()
        runtime = time.time() - start_time

        result = TestResult(
            config=config,
            objective_value=solution.objective_value,
            runtime_seconds=runtime,
            solve_status=str(solution.solve_status),
            instance_name=instance.name,
            run_index=run_index,
        )

        logger.info("=" * 80)
        logger.info(f"RUN {run_index} COMPLETED")
        logger.info(
            f"Test completed: objective={result.objective_value}, "
            f"runtime={result.runtime_seconds:.2f}s"
        )
        logger.info("=" * 80)

        return result, solution

    except Exception as e:
        logger.error(f"Error testing configuration: {e}")
        raise
    finally:
        # Clean up handlers if we created a run-specific logger
        if log_dir is not None and logger:
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()


def save_intermediate_results(
    instance_name: str,
    results: list[TestResult],
    config_mapping: dict,
    best_result: TestResult | None,
    output_file: Path | None,
    log_dir: Path | None,
) -> None:
    """Save intermediate results after each run."""
    # Save full results if output file specified
    if output_file:
        output_data = {
            "instance_name": instance_name,
            "total_configurations_tested": len(results),
            "best_result": best_result.to_dict() if best_result else None,
            "best_run_index": best_result.run_index if best_result else None,
            "all_results": [r.to_dict() for r in results],
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

    # Save configuration mapping
    if log_dir is not None:
        mapping_file = log_dir / "run_config_mapping.json"
        mapping_data = {
            "instance_name": instance_name,
            "total_runs": len(config_mapping),
            "best_run_index": best_result.run_index if best_result else None,
            "best_objective_value": best_result.objective_value
            if best_result
            else None,
            "configurations": config_mapping,
        }
        with open(mapping_file, "w") as f:
            json.dump(mapping_data, f, indent=2)


def find_best_parameters(
    instance: instace.Instance,
    parameter_ranges: dict[str, list],
    timeout_per_config: float = 180,
    output_file: Path | None = None,
    log_dir: Path | None = None,
    logger: logging.Logger | None = None,
) -> tuple[ParameterConfig, TestResult]:
    """
    Find the best parameter configuration by testing multiple combinations.

    Args:
        instance: The scheduling instance to solve
        parameter_ranges: Dictionary specifying parameter ranges to test.
                         Keys are parameter names, values are lists of values to try.
                         If None, uses default ranges.
        timeout_per_config: Timeout for each configuration test in seconds
        output_file: Optional file path to save results JSON
        log_dir: Optional directory to save individual run logs
        logger: Optional logger for detailed output (used for summary only if log_dir is provided)

    Returns:
        Tuple of (best_config, best_result)

    Example:
        >>> parameter_ranges = {
        ...     'start_search_window_size': [5, 7, 10],
        ...     'window_increase_factor': [1.3, 1.5, 1.7],
        ...     'window_decrease_factor': [0.7, 0.8, 0.9],
        ... }
        >>> best_config, best_result = find_best_parameters(instance, parameter_ranges)
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

    # Generate all parameter combinations
    param_names = list(parameter_ranges.keys())
    param_values = [parameter_ranges[name] for name in param_names]
    combinations = list(itertools.product(*param_values))

    logger.info(
        f"Testing {len(combinations)} parameter combinations on instance '{instance.name}' in {len(combinations) * timeout_per_config} seconds total."
    )

    # Setup log directory if provided
    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Logs will be saved to: {log_dir}")

    results = []
    best_result = None
    best_solution = None
    config_mapping = {}  # Maps run_index to configuration

    for i, combo in enumerate(combinations, 1):
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Configuration {i}/{len(combinations)}")
        logger.info(f"{'=' * 80}")

        # Create config with current combination
        config_dict = dict(zip(param_names, combo))
        config_dict["timeout_seconds"] = timeout_per_config

        # Fill in any missing parameters with defaults
        default_config = ParameterConfig()
        for key in vars(default_config):
            if key not in config_dict:
                config_dict[key] = getattr(default_config, key)

        config = ParameterConfig(**config_dict)

        # Store configuration mapping
        config_mapping[i] = {
            "run_index": i,
            "config": config.to_dict(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            result, solution = test_parameter_config(
                instance, config, run_index=i, log_dir=log_dir, logger=logger
            )
            results.append(result)

            best_solution = None

            # Update mapping with result
            config_mapping[i]["objective_value"] = result.objective_value
            config_mapping[i]["runtime_seconds"] = result.runtime_seconds
            config_mapping[i]["solve_status"] = result.solve_status

            if (
                best_result is None
                or result.objective_value < best_result.objective_value
            ):
                best_result = result
                best_solution = solution
                logger.info(
                    f"🎯 New best configuration found! Objective: {result.objective_value}"
                )

            # Save results after each successful run
            save_intermediate_results(
                instance.name,
                results,
                config_mapping,
                best_result,
                output_file,
                log_dir,
            )

        except Exception as e:
            logger.error(f"Failed to test configuration: {e}")
            # Mark as failed in mapping
            config_mapping[i]["status"] = "failed"
            config_mapping[i]["error"] = str(e)

            # Save even after failure
            save_intermediate_results(
                instance.name,
                results,
                config_mapping,
                best_result,
                output_file,
                log_dir,
            )
            continue

    if best_result is None:
        raise RuntimeError("No successful configuration tests completed")

    # Final save already done after last run, just log summary
    if output_file:
        logger.info(f"Final results saved to {output_file}")
    if log_dir is not None:
        logger.info(f"Final mapping saved to {log_dir / 'run_config_mapping.json'}")

    logger.info(f"\n{'=' * 80}")
    logger.info("BEST CONFIGURATION FOUND:")
    logger.info(f"{'=' * 80}")
    logger.info(f"Objective value: {best_result.objective_value}")
    logger.info(f"Runtime: {best_result.runtime_seconds:.2f}s")
    logger.info(f"Parameters: {best_result.config.to_dict()}")

    return best_result.config, best_result


def compare_with_default(
    instance: instace.Instance,
    custom_config: ParameterConfig,
    timeout_seconds: float = 180,
    logger: logging.Logger | None = None,
) -> tuple[TestResult, TestResult]:
    """
    Compare a custom parameter configuration with the default configuration.

    Args:
        instance: The scheduling instance to solve
        custom_config: Custom parameter configuration to test
        timeout_seconds: Timeout for each test in seconds
        logger: Optional logger for detailed output

    Returns:
        Tuple of (default_result, custom_result)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info("Testing default configuration...")
    default_config = ParameterConfig(timeout_seconds=timeout_seconds)
    default_result, _ = test_parameter_config(
        instance, default_config, run_index=1, logger=logger
    )

    logger.info("\nTesting custom configuration...")
    custom_config.timeout_seconds = timeout_seconds
    custom_result, _ = test_parameter_config(
        instance, custom_config, run_index=2, logger=logger
    )

    logger.info(f"\n{'=' * 80}")
    logger.info("COMPARISON RESULTS:")
    logger.info(f"{'=' * 80}")
    logger.info(
        f"Default objective: {default_result.objective_value} "
        f"(runtime: {default_result.runtime_seconds:.2f}s)"
    )
    logger.info(
        f"Custom objective:  {custom_result.objective_value} "
        f"(runtime: {custom_result.runtime_seconds:.2f}s)"
    )

    improvement = default_result.objective_value - custom_result.objective_value
    if improvement > 0:
        percent = (improvement / default_result.objective_value) * 100
        logger.info(f"✅ Custom config is better by {improvement} ({percent:.2f}%)")
    elif improvement < 0:
        percent = (abs(improvement) / default_result.objective_value) * 100
        logger.info(
            f"❌ Default config is better by {abs(improvement)} ({percent:.2f}%)"
        )
    else:
        logger.info("Both configurations achieved the same objective value")

    return default_result, custom_result


def main():
    """Main entry point for finding LNS parameters."""
    from ..parseData import parseTXT

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Load an instance
    instance_path = (
        Path(__file__).parent.parent.parent / "data" / "instance_raw" / "Instance9.txt"
    )
    instance = parseTXT.parse_txt(instance_path)

    # Define parameter ranges to test
    parameter_ranges = {
        "start_search_window_size": [7],
        "window_increase_factor": [1.3, 1.5, 1.7],
        "window_decrease_factor": [0.7, 0.8],
        "strong_improvement_threshold": [0.01, 0.05, 0.1],
    }

    # Find best parameters
    output_path = (
        Path(__file__).parent.parent.parent / "data" / "lns_parameter_results.json"
    )
    log_dir_path = Path(__file__).parent.parent.parent / "data" / "lns_logs"

    best_config, best_result = find_best_parameters(
        instance,
        parameter_ranges=parameter_ranges,
        timeout_per_config=60,  # 60 seconds per configuration
        output_file=output_path,
        log_dir=log_dir_path,
    )


if __name__ == "__main__":
    main()
