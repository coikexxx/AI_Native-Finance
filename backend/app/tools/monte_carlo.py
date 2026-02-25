"""Monte Carlo simulation for investment scenario analysis."""
import numpy as np
from typing import List
from dataclasses import dataclass
from app.tools.financial_model import DCFInputs, DCFModel


@dataclass
class ScenarioAssumptions:
    name: str
    probability: float
    growth_rate_yr1_5: float
    growth_rate_yr6_10: float
    terminal_growth_rate: float
    wacc: float


@dataclass
class SimulationResult:
    scenario_name: str
    probability_pct: float
    intrinsic_value: float
    return_pct: float
    upside_downside: str


class MonteCarloSimulator:
    def __init__(self):
        self.dcf = DCFModel()

    def run_scenarios(
        self,
        base_inputs: DCFInputs,
        current_price: float,
        n_simulations: int = 1000,
    ) -> List[SimulationResult]:
        """Run bull/base/bear scenarios and MC simulation."""
        # Define three scenarios
        scenarios = [
            ScenarioAssumptions(
                name="Bull",
                probability=0.25,
                growth_rate_yr1_5=base_inputs.growth_rate_yr1_5 * 1.5,
                growth_rate_yr6_10=base_inputs.growth_rate_yr6_10 * 1.3,
                terminal_growth_rate=min(base_inputs.terminal_growth_rate * 1.2, 0.04),
                wacc=base_inputs.wacc - 0.01,
            ),
            ScenarioAssumptions(
                name="Base",
                probability=0.50,
                growth_rate_yr1_5=base_inputs.growth_rate_yr1_5,
                growth_rate_yr6_10=base_inputs.growth_rate_yr6_10,
                terminal_growth_rate=base_inputs.terminal_growth_rate,
                wacc=base_inputs.wacc,
            ),
            ScenarioAssumptions(
                name="Bear",
                probability=0.25,
                growth_rate_yr1_5=base_inputs.growth_rate_yr1_5 * 0.5,
                growth_rate_yr6_10=base_inputs.growth_rate_yr6_10 * 0.6,
                terminal_growth_rate=max(base_inputs.terminal_growth_rate * 0.5, 0.01),
                wacc=base_inputs.wacc + 0.02,
            ),
        ]

        results = []
        for s in scenarios:
            inputs = DCFInputs(
                current_fcf=base_inputs.current_fcf,
                growth_rate_yr1_5=s.growth_rate_yr1_5,
                growth_rate_yr6_10=s.growth_rate_yr6_10,
                terminal_growth_rate=s.terminal_growth_rate,
                wacc=s.wacc,
                shares_outstanding=base_inputs.shares_outstanding,
                net_cash=base_inputs.net_cash,
            )
            dcf_out = self.dcf.calculate(inputs, current_price)
            iv = dcf_out.intrinsic_value_per_share
            ret = (iv - current_price) / current_price * 100

            results.append(SimulationResult(
                scenario_name=s.name,
                probability_pct=s.probability * 100,
                intrinsic_value=iv,
                return_pct=round(ret, 1),
                upside_downside="Upside" if ret > 0 else "Downside",
            ))

        return results

    def run_monte_carlo(
        self,
        base_inputs: DCFInputs,
        current_price: float,
        n_simulations: int = 1000,
    ) -> dict:
        """Full Monte Carlo simulation with random parameter draws."""
        np.random.seed(42)
        values = []

        for _ in range(n_simulations):
            # Randomly vary growth and WACC within reasonable bounds
            g5 = np.random.normal(base_inputs.growth_rate_yr1_5, base_inputs.growth_rate_yr1_5 * 0.3)
            g10 = np.random.normal(base_inputs.growth_rate_yr6_10, base_inputs.growth_rate_yr6_10 * 0.3)
            tg = np.random.normal(base_inputs.terminal_growth_rate, 0.005)
            wacc = np.random.normal(base_inputs.wacc, 0.01)

            # Clamp values to reasonable ranges
            g5 = np.clip(g5, -0.3, 0.6)
            g10 = np.clip(g10, -0.2, 0.4)
            tg = np.clip(tg, 0.005, 0.05)
            wacc = np.clip(wacc, 0.04, 0.20)
            if wacc <= tg:
                wacc = tg + 0.02

            inputs = DCFInputs(
                current_fcf=base_inputs.current_fcf,
                growth_rate_yr1_5=g5,
                growth_rate_yr6_10=g10,
                terminal_growth_rate=tg,
                wacc=wacc,
                shares_outstanding=base_inputs.shares_outstanding,
                net_cash=base_inputs.net_cash,
            )
            try:
                out = self.dcf.calculate(inputs, current_price)
                values.append(out.intrinsic_value_per_share)
            except Exception:
                pass

        if not values:
            return {}

        arr = np.array(values)
        return {
            "p10": round(float(np.percentile(arr, 10)), 2),
            "p25": round(float(np.percentile(arr, 25)), 2),
            "p50": round(float(np.percentile(arr, 50)), 2),
            "p75": round(float(np.percentile(arr, 75)), 2),
            "p90": round(float(np.percentile(arr, 90)), 2),
            "mean": round(float(np.mean(arr)), 2),
            "std": round(float(np.std(arr)), 2),
            "n_simulations": len(values),
        }


monte_carlo = MonteCarloSimulator()
