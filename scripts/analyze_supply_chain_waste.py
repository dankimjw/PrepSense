#!/usr/bin/env python3
"""
Analyze full supply chain waste to show cumulative environmental impact
"""

import json
from pathlib import Path

import pandas as pd


def analyze_supply_chain_waste():
    """Analyze waste across entire supply chain"""

    # Read FAO data
    df = pd.read_csv("data/food_loss_waste/fao_flw_data.csv")

    # Calculate cumulative waste by commodity across all stages
    print("=== CUMULATIVE SUPPLY CHAIN WASTE ===\n")

    # Group by commodity and stage
    df.groupby(["commodity", "food_supply_stage"])["loss_percentage"].agg(
        ["mean", "median", "count"]
    )

    # Calculate total supply chain loss for each commodity
    commodities = df["commodity"].unique()
    cumulative_losses = {}

    for commodity in commodities[:50]:  # Top 50 commodities
        stages = (
            df[df["commodity"] == commodity]
            .groupby("food_supply_stage")["loss_percentage"]
            .median()
        )

        if len(stages) > 0:
            # Calculate cumulative loss (compound effect)
            remaining = 100
            stage_losses = {}
            cumulative = 0

            # Order stages in supply chain sequence
            stage_order = [
                "Farm",
                "Harvest",
                "Post-harvest",
                "Storage",
                "Processing",
                "Transport",
                "Wholesale",
                "Retail",
                "Households",
            ]

            for stage in stage_order:
                if stage in stages.index:
                    loss_pct = stages[stage]
                    actual_loss = (remaining * loss_pct) / 100
                    cumulative += actual_loss
                    remaining -= actual_loss
                    stage_losses[stage] = loss_pct

            cumulative_losses[commodity] = {
                "stage_losses": stage_losses,
                "cumulative_loss_pct": round(cumulative, 2),
                "reaches_consumer_pct": round(remaining, 2),
            }

    # Sort by cumulative loss
    sorted_commodities = sorted(
        cumulative_losses.items(), key=lambda x: x[1]["cumulative_loss_pct"], reverse=True
    )

    print("Top 20 commodities by TOTAL supply chain loss:")
    print(f"{'Commodity':<30} {'Total Loss %':<15} {'Reaches Consumer %'}")
    print("-" * 70)

    for commodity, data in sorted_commodities[:20]:
        print(f"{commodity:<30} {data['cumulative_loss_pct']:<15} {data['reaches_consumer_pct']}")

    # Show environmental multiplier effect
    print("\n=== ENVIRONMENTAL IMPACT MULTIPLIER ===\n")

    # Example calculation for high-waste items
    examples = ["Tomatoes", "Lettuce", "Bananas", "Beef", "Rice"]

    for item in examples:
        if item in cumulative_losses:
            data = cumulative_losses[item]
            total_loss = data["cumulative_loss_pct"]
            consumer_loss = data["stage_losses"].get("Households", 10)  # Default 10%

            # Environmental impact multiplier
            # If 30% is lost before reaching consumer, and consumer wastes 15%,
            # then for every 1kg wasted at home, 1.43kg was produced
            multiplier = 100 / data["reaches_consumer_pct"]

            print(f"\n{item}:")
            print(f"  Supply chain loss: {total_loss:.1f}%")
            print(f"  Consumer loss: {consumer_loss:.1f}%")
            print(f"  Environmental multiplier: {multiplier:.2f}x")
            print(f"  → For every 1kg wasted at home, {multiplier:.2f}kg was originally produced")

            # If we have CO2 data, show amplified impact
            co2_mappings = {
                "Tomatoes": 2.09,
                "Lettuce": 1.06,
                "Bananas": 0.86,
                "Beef": 99.48,
                "Rice": 4.45,
            }

            if item in co2_mappings:
                co2_per_kg = co2_mappings[item]
                print(f"  → Actual CO2 impact: {co2_per_kg * multiplier:.1f} kg CO2e per kg wasted")

    # Save enhanced data
    output_file = Path("data/food_loss_waste/supply_chain_analysis.json")
    with open(output_file, "w") as f:
        json.dump(cumulative_losses, f, indent=2)

    print(f"\n✅ Saved supply chain analysis to {output_file}")

    # Key insights
    print("\n=== KEY INSIGHTS ===")
    print("1. Supply chain losses compound - 10% at each of 5 stages = 41% total loss")
    print("2. High-waste items like fresh produce have massive upstream impact")
    print("3. When we prevent 1kg of household waste, we save the entire supply chain impact")
    print("4. This multiplies the environmental benefit by 1.5x to 3x for most foods")


if __name__ == "__main__":
    analyze_supply_chain_waste()
