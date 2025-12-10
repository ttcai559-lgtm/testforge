import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_file(path: Path) -> None:
    if not path.exists():
        path.write_text("[]", encoding="utf-8")


class PressureStorage:
    """
    轻量级文件存储，用于管理压测场景与执行记录。
    """

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.scenario_file = self.base_path / "scenarios.json"
        self.run_file = self.base_path / "runs.json"
        _ensure_file(self.scenario_file)
        _ensure_file(self.run_file)

    # -------------------- File Helpers --------------------
    def _read(self, path: Path) -> List[Dict[str, Any]]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _write(self, path: Path, data: List[Dict[str, Any]]) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _update_scenario(self, scenarios: List[Dict[str, Any]], scenario: Dict[str, Any]) -> None:
        for idx, item in enumerate(scenarios):
            if item["id"] == scenario["id"]:
                scenarios[idx] = scenario
                break

    # -------------------- Scenario APIs --------------------
    def list_scenarios(self, scenario_type: Optional[str] = None) -> List[Dict[str, Any]]:
        scenarios = self._read(self.scenario_file)
        if scenario_type:
            scenario_type = scenario_type.lower()
            scenarios = [item for item in scenarios if item.get("type") == scenario_type]
        return scenarios

    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        for item in self._read(self.scenario_file):
            if item["id"] == scenario_id:
                return item
        return None

    def create_scenario(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        scenarios = self._read(self.scenario_file)
        scenario = {
            "id": payload.get("id") or f"scn_{int(datetime.now().timestamp() * 1000)}",
            "name": payload["name"],
            "type": payload["type"],
            "environment": payload.get("environment"),
            "description": payload.get("description"),
            "config": payload.get("config") or {},
            "status": "idle",
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "last_run_at": None,
        }
        scenarios.append(scenario)
        self._write(self.scenario_file, scenarios)
        return scenario

    def update_scenario(self, scenario_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        scenarios = self._read(self.scenario_file)
        updated = None
        for item in scenarios:
            if item["id"] == scenario_id:
                item.update({
                    "name": payload.get("name", item["name"]),
                    "environment": payload.get("environment", item.get("environment")),
                    "description": payload.get("description", item.get("description")),
                    "config": payload.get("config", item.get("config", {})),
                    "status": payload.get("status", item.get("status", "idle")),
                    "type": payload.get("type", item["type"]),
                    "updated_at": _utc_now(),
                })
                updated = item
                break
        if updated is None:
            raise ValueError("Scenario not found")
        self._write(self.scenario_file, scenarios)
        return updated

    def delete_scenario(self, scenario_id: str) -> None:
        scenarios = [item for item in self._read(self.scenario_file) if item["id"] != scenario_id]
        runs = [run for run in self._read(self.run_file) if run.get("scenario_id") != scenario_id]
        self._write(self.scenario_file, scenarios)
        self._write(self.run_file, runs)

    def _set_scenario_status(self, scenario_id: str, status: str) -> None:
        scenarios = self._read(self.scenario_file)
        for item in scenarios:
            if item["id"] == scenario_id:
                item["status"] = status
                item["last_run_at"] = _utc_now()
                item["updated_at"] = _utc_now()
                break
        self._write(self.scenario_file, scenarios)

    # -------------------- Run APIs --------------------
    def list_runs(self, scenario_type: Optional[str] = None) -> List[Dict[str, Any]]:
        runs = self._read(self.run_file)
        if scenario_type:
            scenario_type = scenario_type.lower()
            runs = [item for item in runs if item.get("type") == scenario_type]
        return sorted(runs, key=lambda item: item.get("started_at", ""), reverse=True)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        for item in self._read(self.run_file):
            if item["id"] == run_id:
                return item
        return None

    def create_run(
        self,
        scenario: Dict[str, Any],
        note: Optional[str] = None,
        mode: Optional[str] = "manual",
        *,
        iterations: int = 1,
        threads: int = 1,
        run_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        runs = self._read(self.run_file)
        resolved_type = (run_type or scenario.get("type") or "functional").lower()
        run = {
            "id": f"run_{int(datetime.now().timestamp() * 1000)}",
            "scenario_id": scenario["id"],
            "name": scenario["name"],
            "type": resolved_type,
            "environment": scenario.get("environment"),
            "status": "running",
            "note": note,
            "mode": mode or "manual",
            "iterations": iterations,
            "threads": threads,
            "started_at": _utc_now(),
            "completed_at": None,
            "metrics": {},
        }
        runs.append(run)
        self._write(self.run_file, runs)
        self._set_scenario_status(scenario["id"], "running")
        return run

    def complete_run(
        self,
        run_id: str,
        *,
        success: bool,
        metrics: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        runs = self._read(self.run_file)
        target = None
        for item in runs:
            if item["id"] == run_id:
                target = item
                break
        if target is None:
            return None

        target["status"] = "success" if success else "failed"
        target["completed_at"] = _utc_now()
        target["metrics"] = metrics or {}
        if errors:
            target["errors"] = errors

        self._write(self.run_file, runs)
        self._set_scenario_status(target["scenario_id"], target["status"])
        return target

    def summary(self) -> Dict[str, Any]:
        scenarios = self._read(self.scenario_file)
        runs = self._read(self.run_file)
        total_scenarios = len(scenarios)
        functional_count = len([s for s in scenarios if s.get("type") == "functional"])
        performance_count = len([s for s in scenarios if s.get("type") == "performance"])

        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        def parse_time(value: Optional[str]) -> Optional[datetime]:
            if not value:
                return None
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None

        week_runs = [run for run in runs if (parsed := parse_time(run.get("started_at"))) and parsed >= week_ago]
        week_functional = len([run for run in week_runs if run.get("type") == "functional"])
        week_performance = len([run for run in week_runs if run.get("type") == "performance"])
        running_runs = [run for run in runs if run.get("status") == "running"]
        performance_metrics = [run for run in runs if run.get("type") == "performance" and run.get("metrics")]

        peak_rps = max((run["metrics"].get("rps", 0) for run in performance_metrics), default=0)
        avg_latency = (
            sum(run["metrics"].get("latency_p95_ms", 0) for run in performance_metrics) / len(performance_metrics)
            if performance_metrics
            else 0
        )
        avg_error = (
            sum(run["metrics"].get("error_rate", 0) for run in performance_metrics) / len(performance_metrics)
            if performance_metrics
            else 0
        )

        return {
            "total_scenarios": total_scenarios,
            "functional_scenarios": functional_count,
            "performance_scenarios": performance_count,
            "executions_this_week": len(week_runs),
            "functional_executions_this_week": week_functional,
            "performance_executions_this_week": week_performance,
            "running_runs": len(running_runs),
            "metrics_snapshot": {
                "peak_rps": peak_rps,
                "avg_latency_ms": round(avg_latency, 2),
                "error_rate": round(avg_error, 2),
                "clusters": ["性能集群A", "性能集群B"] if performance_metrics else [],
            },
        }
