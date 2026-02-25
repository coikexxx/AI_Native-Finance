"""DCF financial modeling engine."""
import numpy as np
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class DCFInputs:
    current_fcf: float          # Most recent annual FCF
    growth_rate_yr1_5: float    # Annual FCF growth rate, years 1-5 (e.g. 0.15 = 15%)
    growth_rate_yr6_10: float   # Annual FCF growth rate, years 6-10
    terminal_growth_rate: float  # Terminal growth rate (e.g. 0.03 = 3%)
    wacc: float                 # Weighted average cost of capital (e.g. 0.09 = 9%)
    shares_outstanding: float   # In shares
    net_cash: float             # Net cash (cash - debt), can be negative
    projection_years: int = 10


@dataclass
class DCFOutput:
    intrinsic_value_per_share: float
    current_price: float
    margin_of_safety_pct: float
    terminal_value: float
    pv_fcf_sum: float
    fcf_projections: List[float]
    sensitivity_table: dict     # grid of values vs. different WACC/growth combos


class DCFModel:
    def calculate(self, inputs: DCFInputs, current_price: float) -> DCFOutput:
        """Calculate DCF intrinsic value."""
        fcf_projections = []
        fcf = inputs.current_fcf

        # Project FCF for each year
        for year in range(1, inputs.projection_years + 1):
            if year <= 5:
                fcf *= (1 + inputs.growth_rate_yr1_5)
            else:
                fcf *= (1 + inputs.growth_rate_yr6_10)
            fcf_projections.append(fcf)

        # Terminal value (Gordon Growth Model)
        terminal_fcf = fcf_projections[-1] * (1 + inputs.terminal_growth_rate)
        terminal_value = terminal_fcf / (inputs.wacc - inputs.terminal_growth_rate)

        # Present value of FCF
        pv_fcfs = []
        for i, proj_fcf in enumerate(fcf_projections, 1):
            pv = proj_fcf / (1 + inputs.wacc) ** i
            pv_fcfs.append(pv)

        pv_fcf_sum = sum(pv_fcfs)
        pv_terminal = terminal_value / (1 + inputs.wacc) ** inputs.projection_years

        total_equity_value = pv_fcf_sum + pv_terminal + inputs.net_cash
        intrinsic_value = total_equity_value / inputs.shares_outstanding

        margin_of_safety = (intrinsic_value - current_price) / intrinsic_value if intrinsic_value > 0 else -1.0

        # Sensitivity table: vary WACC and terminal growth
        sensitivity = self._build_sensitivity(inputs, current_price)

        return DCFOutput(
            intrinsic_value_per_share=round(intrinsic_value, 2),
            current_price=current_price,
            margin_of_safety_pct=round(margin_of_safety * 100, 1),
            terminal_value=round(pv_terminal, 0),
            pv_fcf_sum=round(pv_fcf_sum, 0),
            fcf_projections=[round(f, 0) for f in fcf_projections],
            sensitivity_table=sensitivity,
        )

    def _build_sensitivity(self, inputs: DCFInputs, current_price: float) -> dict:
        """Sensitivity analysis: vary WACC ±2% and terminal growth ±1%."""
        wacc_range = [inputs.wacc - 0.02, inputs.wacc - 0.01, inputs.wacc,
                      inputs.wacc + 0.01, inputs.wacc + 0.02]
        tg_range = [inputs.terminal_growth_rate - 0.01, inputs.terminal_growth_rate,
                    inputs.terminal_growth_rate + 0.01]

        table = {"wacc_values": [round(w * 100, 1) for w in wacc_range],
                 "tg_values": [round(t * 100, 1) for t in tg_range],
                 "grid": []}

        for tg in tg_range:
            row = []
            for wacc in wacc_range:
                if wacc <= tg:
                    row.append(None)
                    continue
                modified = DCFInputs(
                    current_fcf=inputs.current_fcf,
                    growth_rate_yr1_5=inputs.growth_rate_yr1_5,
                    growth_rate_yr6_10=inputs.growth_rate_yr6_10,
                    terminal_growth_rate=tg,
                    wacc=wacc,
                    shares_outstanding=inputs.shares_outstanding,
                    net_cash=inputs.net_cash,
                )
                result = self.calculate(modified, current_price)
                row.append(result.intrinsic_value_per_share)
            table["grid"].append(row)

        return table


dcf_model = DCFModel()
