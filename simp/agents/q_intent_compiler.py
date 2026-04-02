"""
StrategicOptimizer: Decision Engine with Minimax Game Theory

Implements fractal decision trees with minimax optimization for strategic
intent compilation and multi-criteria analysis.

Core Algorithm:
1. Validate and normalize input data streams
2. Build fractal decision tree (branches = analysis traits)
3. Apply minimax game theory optimization
4. Recursively improve decision quality
5. Return optimized strategic intent with reasoning trace

Key Innovation: Uses minimax (like chess engines) to find optimal strategies
by modeling decision-making as adversarial game theory.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import random
import math


@dataclass
class TreeNode:
    """Single node in the fractal decision tree"""
    trait: str                  # Market trait: "momentum", "volume", etc.
    value: float               # Current value of this trait
    foresight: float           # Confidence (0-1)
    drift_risk: float          # Risk of sudden change (0-1)
    depth: int = 0             # Depth in tree
    children: List['TreeNode'] = field(default_factory=list)
    parent: Optional['TreeNode'] = None

    def to_dict(self) -> dict:
        """Convert node to dictionary"""
        return {
            "trait": self.trait,
            "value": self.value,
            "foresight": self.foresight,
            "drift_risk": self.drift_risk,
            "depth": self.depth,
            "children_count": len(self.children)
        }


@dataclass
class DecisionTree:
    """Complete fractal decision tree for market analysis"""
    root_timestamp: str        # When tree was created (ISO 8601)
    branches: List[TreeNode]   # Top-level decision branches
    depth: int                 # Maximum depth of reasoning
    score: float               # MiniMax optimization score
    utility: float             # Overall utility value
    optimal_action: str        # Recommended action: BUY, SELL, HOLD
    confidence: float          # Confidence in recommendation (0-1)
    reasoning_trace: List[str] = field(default_factory=list)  # How we got here
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert tree to dictionary"""
        return {
            "root_timestamp": self.root_timestamp,
            "branches": [b.to_dict() for b in self.branches],
            "depth": self.depth,
            "score": self.score,
            "utility": self.utility,
            "optimal_action": self.optimal_action,
            "confidence": self.confidence,
            "reasoning_trace": self.reasoning_trace,
            "metadata": self.metadata
        }


class StrategicOptimizer:
    """
    Strategic Optimizer: Decision engine using minimax game theory

    Compiles complex decision scenarios into optimized strategic intents using
    fractal decision trees and minimax optimization. Works with any domain:
    trading, scheduling, resource allocation, multi-agent coordination, etc.
    """

    def __init__(self):
        """Initialize compiler"""
        self.iteration_count = 0
        self.improvement_history = []
        self.max_iterations = 3
        self.minimax_depth = 5

    async def compile_intent(
        self,
        foresight_streams: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None
    ) -> DecisionTree:
        """
        Main entry point: Compile input streams into optimal strategic intent

        Args:
            foresight_streams: Data streams with signals, confidence, deltas, etc.
            market_data: Additional context for decision making (optional)

        Returns:
            DecisionTree: Complete optimized strategy with reasoning trace
        """
        try:
            # Step 1: Fetch and validate streams
            streams = self._validate_streams(foresight_streams)

            # Step 2: Build initial fractal tree
            tree = self._build_fractal_tree(streams)

            # Step 3: Apply minimax optimization
            tree = self._apply_minimax(tree)

            # Step 4: Recursive improvement (self-learning)
            tree = await self._recursive_improve(tree)

            # Step 5: Add reasoning trace
            tree.reasoning_trace.append("StrategicOptimizer compilation completed")

            return tree

        except Exception as e:
            # Return error tree
            return DecisionTree(
                root_timestamp=datetime.utcnow().isoformat(),
                branches=[],
                depth=0,
                score=0.0,
                utility=0.0,
                optimal_action="HOLD",  # Safe default
                confidence=0.0,
                reasoning_trace=[f"Error in StrategicOptimizer: {str(e)}"]
            )

    def _validate_streams(self, streams: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize input streams"""
        if not streams:
            raise ValueError("Empty streams provided to StrategicOptimizer")

        # Ensure required fields
        required_fields = ["timestamp", "deltas"]
        for field in required_fields:
            if field not in streams:
                streams[field] = streams.get(field, None)

        # Ensure foresight structure
        if "foresight" not in streams:
            streams["foresight"] = {
                "affinity": 0.5,      # Neutral baseline
                "drift_risk": 0.1     # Low risk baseline
            }

        return streams

    def _build_fractal_tree(self, streams: Dict[str, Any]) -> DecisionTree:
        """
        Build initial fractal decision tree from input data

        Fractal structure: each branch represents a decision trait (momentum, volume, etc.)
        with values representing current state of that trait for analysis.
        """
        deltas = streams.get("deltas", {})
        foresight = streams.get("foresight", {})
        timestamp = streams.get("timestamp", datetime.utcnow().isoformat())

        # Create branch nodes from market deltas
        branches = []
        for trait, value in deltas.items():
            node = TreeNode(
                trait=str(trait),
                value=float(value) if isinstance(value, (int, float)) else 0.5,
                foresight=foresight.get("affinity", 0.5),
                drift_risk=foresight.get("drift_risk", 0.1),
                depth=1
            )
            branches.append(node)

        # If no deltas, create default nodes
        if not branches:
            default_traits = ["momentum", "volume", "sentiment", "volatility"]
            for trait in default_traits:
                node = TreeNode(
                    trait=trait,
                    value=random.uniform(0.4, 0.6),
                    foresight=0.5,
                    drift_risk=0.1,
                    depth=1
                )
                branches.append(node)

        # Calculate tree depth based on risk
        depth = max(1, min(10, int(foresight.get("drift_risk", 0.1) * 10)))

        tree = DecisionTree(
            root_timestamp=timestamp,
            branches=branches,
            depth=depth,
            score=0.0,
            utility=0.0,
            optimal_action="HOLD",
            confidence=0.0
        )

        tree.reasoning_trace.append(f"Fractal tree built: {len(branches)} branches, depth {depth}")
        return tree

    def _apply_minimax(self, tree: DecisionTree) -> DecisionTree:
        """
        Apply minimax optimization using game theory

        Minimax models decision space as two-player game:
        - MAX (Optimizer): Tries to maximize utility
        - MIN (Adversary): Tries to minimize our utility

        Result: Conservative but optimal decisions considering worst-case scenarios
        """
        MAX = 1
        MIN = -1
        ADJUSTMENT_CHOICES = [0.05, 0.10, 0.15, 0.20]

        def minimax(
            branches: List[TreeNode],
            player: int,
            depth_remaining: int
        ) -> Tuple[float, Optional[float]]:
            """
            Recursive minimax algorithm

            Returns: (best_score, best_move)
            """
            if depth_remaining <= 0 or not branches:
                score = self._evaluate(branches, player)
                return score, None

            available_moves = []

            for choice in ADJUSTMENT_CHOICES:
                # Simulate adjusted branches
                adjusted = [
                    TreeNode(
                        trait=b.trait,
                        value=b.value + (choice if player == MAX else -choice),
                        foresight=b.foresight,
                        drift_risk=b.drift_risk,
                        depth=b.depth
                    )
                    for b in branches
                ]

                score, _ = minimax(adjusted, -player, depth_remaining - 1)
                available_moves.append({"score": score, "move": choice})

            # Select best move
            if player == MAX:
                best = max(available_moves, key=lambda x: x["score"])
            else:
                best = min(available_moves, key=lambda x: x["score"])

            return best["score"], best["move"]

        # Run minimax
        best_score, best_move = minimax(tree.branches, MAX, tree.depth)

        # Apply best move to all branches
        if best_move is not None:
            for branch in tree.branches:
                branch.value += best_move

        # Determine action based on average branch value
        avg_value = sum(b.value for b in tree.branches) / len(tree.branches) if tree.branches else 0.5
        if avg_value > 0.65:
            tree.optimal_action = "BUY"
        elif avg_value < 0.35:
            tree.optimal_action = "SELL"
        else:
            tree.optimal_action = "HOLD"

        # Calculate confidence
        avg_foresight = sum(b.foresight for b in tree.branches) / len(tree.branches) if tree.branches else 0.5
        tree.confidence = avg_foresight

        # Store results
        tree.score = best_score
        tree.utility = self._calculate_utility(tree)

        tree.reasoning_trace.append(
            f"Minimax optimization: action={tree.optimal_action}, "
            f"score={best_score:.2f}, confidence={tree.confidence:.2f}"
        )

        return tree

    def _evaluate(self, branches: List[TreeNode], player: int) -> float:
        """
        Evaluate board state for minimax scoring

        Score = (Affinity * 100) - (Drift * 50)
        """
        MAX = 1
        avg_affinity = sum(b.foresight for b in branches) / len(branches) if branches else 0.5
        avg_drift = sum(b.drift_risk for b in branches) / len(branches) if branches else 0.1

        if player == MAX:
            return (avg_affinity * 100) - (avg_drift * 50)
        else:
            return -(avg_affinity * 100) + (avg_drift * 50)

    def _calculate_utility(self, tree: DecisionTree) -> float:
        """
        Calculate overall utility of the decision tree

        Utility = Sum of (branch_value * branch_foresight)
        Normalized by number of branches
        """
        if not tree.branches:
            return 0.0

        total_utility = sum(b.value * b.foresight for b in tree.branches)
        normalized_utility = total_utility / len(tree.branches)

        return normalized_utility

    async def _recursive_improve(
        self,
        tree: DecisionTree,
        iterations: Optional[int] = None
    ) -> DecisionTree:
        """
        Recursively improve the decision tree through self-refinement

        Each iteration:
        1. Evaluate current tree utility
        2. Generate alternative branch configurations
        3. Select highest utility configuration
        4. Optimize for efficiency
        """
        if iterations is None:
            iterations = self.max_iterations

        for i in range(iterations):
            # Evaluate current utility
            current_utility = self._calculate_utility(tree)
            self.improvement_history.append(current_utility)

            # Generate alternatives
            alternatives = self._generate_alternatives(tree, count=3)

            # Select best alternative
            best_alt = max(alternatives, key=lambda t: self._calculate_utility(t))

            # Apply optimization
            tree = self._optimize_tree(best_alt)

            tree.reasoning_trace.append(
                f"Improvement iteration {i + 1}/{iterations}: "
                f"utility={self._calculate_utility(tree):.2f}"
            )

            # Small delay to allow other operations
            await asyncio.sleep(0.01)

        return tree

    def _generate_alternatives(self, tree: DecisionTree, count: int = 3) -> List[DecisionTree]:
        """Generate alternative tree configurations"""
        alternatives = []

        for _ in range(count):
            # Create variation by adjusting branch values
            new_tree = DecisionTree(
                root_timestamp=tree.root_timestamp,
                branches=[],
                depth=tree.depth,
                score=tree.score,
                utility=0.0,
                optimal_action=tree.optimal_action,
                confidence=tree.confidence,
                reasoning_trace=tree.reasoning_trace.copy()
            )

            # Adjust branches randomly
            for branch in tree.branches:
                new_node = TreeNode(
                    trait=branch.trait,
                    value=branch.value + random.uniform(-0.1, 0.1),
                    foresight=branch.foresight + random.uniform(-0.05, 0.05),
                    drift_risk=branch.drift_risk + random.uniform(-0.03, 0.03),
                    depth=branch.depth
                )
                new_tree.branches.append(new_node)

            # Recalculate metrics
            new_tree.utility = self._calculate_utility(new_tree)
            alternatives.append(new_tree)

        return alternatives + [tree]  # Include current tree as alternative

    def _optimize_tree(self, tree: DecisionTree) -> DecisionTree:
        """
        Optimize tree for efficiency

        Applies penalties for complexity while rewarding confidence
        """
        # Length penalty: prefer simpler trees
        length_penalty = 0.9 if len(tree.branches) > 10 else 1.0

        # Optimize branch values
        for branch in tree.branches:
            original_value = branch.value
            branch.value = original_value * length_penalty * (branch.foresight or 0.5)

        # Adjust depth
        tree.depth = int(tree.depth * length_penalty)

        # Recalculate utility
        tree.utility = self._calculate_utility(tree)

        return tree

    def get_action_params(self, tree: DecisionTree) -> Dict[str, Any]:
        """
        Convert decision tree into actionable execution parameters

        Returns structured output for downstream agents or executors
        """
        if not tree.branches:
            return {
                "action": "HOLD",
                "confidence": 0.0,
                "reason": "No valid decision tree"
            }

        # Calculate confidence-based weighting
        base_weight = 1.0
        execution_weight = base_weight * tree.confidence

        # Determine primary factor based on dominant trait
        dominant_trait = max(tree.branches, key=lambda b: b.value).trait

        return {
            "action": tree.optimal_action,
            "confidence": tree.confidence,
            "execution_weight": execution_weight,
            "primary_factor": dominant_trait,
            "reasoning": "; ".join(tree.reasoning_trace[-2:]),
            "tree_depth": tree.depth,
            "optimization_score": tree.score,
            "timestamp": tree.root_timestamp,
            "utility": tree.utility
        }


# For backward compatibility
QIntentCompiler = StrategicOptimizer  # Alias for existing code

def create_compiler() -> StrategicOptimizer:
    """Factory function to create StrategicOptimizer instance"""
    return StrategicOptimizer()

def create_strategic_optimizer() -> StrategicOptimizer:
    """Factory function to create StrategicOptimizer instance (preferred name)"""
    return StrategicOptimizer()
