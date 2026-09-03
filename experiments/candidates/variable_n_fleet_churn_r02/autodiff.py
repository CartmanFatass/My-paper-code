"""Source-owned scalar reverse DAG for the frozen VNFC R02 law.

The engine is intentionally small and eager.  Leaves are registered first in
their frozen order.  Each primitive is then emitted only after its operands;
``backward`` independently reconstructs the memoized DFS postorder and refuses
any graph whose eager node ids differ from that order.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable, Mapping, Sequence

from .contract import ContractViolation, LOGIT_FLOOR, ScalarTranscendentals
from .optimizer import GradientTensor, ParameterTensor
from .probability import Candidate, ProbabilityObject, clamp_centered_max_adjoint
from .scalar import binary64_bits, rn64


class AutodiffError(ContractViolation):
    """The scalar graph differs from the frozen construction or reverse law."""


@dataclass(frozen=True)
class NodeRecord:
    node_id: int
    semantic_path: str
    primitive: str
    parent_node_ids_in_operand_slot_order: tuple[int, ...]


@dataclass(frozen=True, eq=False)
class Scalar:
    tape: "ScalarTape"
    node_id: int
    value: float
    semantic_path: str


@dataclass(frozen=True)
class StoredCategorical:
    probability: ProbabilityObject
    stored_log_p: tuple[float, ...]
    stored_H: float


@dataclass(frozen=True)
class BackwardResult:
    node_table: tuple[NodeRecord, ...]
    adjoints: tuple[float, ...]
    leaf_gradients: tuple[tuple[str, float], ...]
    parameter_gradients: tuple[GradientTensor, ...]
    tape_identity: int
    construction_to_node_id: tuple[int, ...]

    def gradient(self, scalar: Scalar) -> float:
        if id(scalar.tape) != self.tape_identity or not 0 <= scalar.node_id < len(self.adjoints):
            raise AutodiffError("scalar is absent from this reverse result")
        return self.adjoints[self.construction_to_node_id[scalar.node_id]]


@dataclass
class _Node:
    scalar: Scalar
    primitive: str
    parents: tuple[int, ...]
    data: Any
    differentiable_leaf: bool = False
    parameter: tuple[str, tuple[int, ...], int] | None = None


@dataclass(frozen=True)
class _CenteredGroup:
    group_id: int
    probability: ProbabilityObject
    logit_parent_ids: tuple[int, ...]


def _same_bits(left: float, right: float) -> bool:
    return binary64_bits(left) == binary64_bits(right)


class ScalarTape:
    """One presentation-specific scalar graph and accumulator."""

    def __init__(self, kernel: ScalarTranscendentals) -> None:
        self.kernel = kernel
        self._nodes: list[_Node] = []
        self._paths: set[str] = set()
        self._sealed_leaves = False
        self._last_aux_leaf_path: str | None = None
        self._parameter_specs: tuple[ParameterTensor, ...] = ()
        self._parameter_ids: dict[str, list[int]] = {}
        self._center_group_counter = 0

    @property
    def node_table(self) -> tuple[NodeRecord, ...]:
        """Construction handles only; persisted semantic ids live in BackwardResult."""
        return tuple(
            NodeRecord(node.scalar.node_id, node.scalar.semantic_path, node.primitive, node.parents)
            for node in self._nodes
        )

    def _new_node(
        self,
        path: str,
        primitive: str,
        parents: Sequence[Scalar],
        value: float,
        *,
        data: Any = None,
        differentiable_leaf: bool = False,
        parameter: tuple[str, tuple[int, ...], int] | None = None,
    ) -> Scalar:
        if not isinstance(path, str) or not path or path in self._paths:
            raise AutodiffError("semantic paths must be nonempty and unique")
        parent_tuple = tuple(parents)
        if any(parent.tape is not self for parent in parent_tuple):
            raise AutodiffError("an operand belongs to a different presentation graph")
        if primitive not in {"leaf", "constant"}:
            self._sealed_leaves = True
        elif self._sealed_leaves:
            raise AutodiffError("all leaves and constants must be registered before primitives")
        node_id = len(self._nodes)
        if any(parent.node_id >= node_id for parent in parent_tuple):
            raise AutodiffError("every primitive operand must have a lower node id")
        scalar = Scalar(self, node_id, rn64(value), path)
        self._nodes.append(
            _Node(
                scalar=scalar,
                primitive=primitive,
                parents=tuple(parent.node_id for parent in parent_tuple),
                data=data,
                differentiable_leaf=differentiable_leaf,
                parameter=parameter,
            )
        )
        self._paths.add(path)
        return scalar

    def register_parameters(
        self, parameters: Sequence[ParameterTensor]
    ) -> dict[str, tuple[Scalar, ...]]:
        if self._nodes or self._parameter_specs:
            raise AutodiffError("parameter leaves must be the first registered nodes")
        specs = tuple(parameters)
        names = tuple(parameter.name for parameter in specs)
        if names != tuple(sorted(names)) or len(set(names)) != len(names):
            raise AutodiffError("parameter tensors must be in unique ASCII-name order")
        self._parameter_specs = specs
        result: dict[str, tuple[Scalar, ...]] = {}
        for parameter in specs:
            leaves: list[Scalar] = []
            ids: list[int] = []
            for index, value in enumerate(parameter.values):
                path = f"parameter/{parameter.name}/{index}"
                leaf = self._new_node(
                    path,
                    "leaf",
                    (),
                    value,
                    differentiable_leaf=True,
                    parameter=(parameter.name, parameter.shape, index),
                )
                leaves.append(leaf)
                ids.append(leaf.node_id)
            result[parameter.name] = tuple(leaves)
            self._parameter_ids[parameter.name] = ids
        return result

    def leaf(self, semantic_path: str, value: float) -> Scalar:
        if self._last_aux_leaf_path is not None and semantic_path <= self._last_aux_leaf_path:
            raise AutodiffError("non-parameter differentiable leaves must use ascending semantic paths")
        self._last_aux_leaf_path = semantic_path
        return self._new_node(
            semantic_path, "leaf", (), value, differentiable_leaf=True
        )

    def constant(self, semantic_path: str, value: float) -> Scalar:
        if self._last_aux_leaf_path is not None and semantic_path <= self._last_aux_leaf_path:
            raise AutodiffError("constant leaves must share ascending semantic-path registration")
        self._last_aux_leaf_path = semantic_path
        return self._new_node(semantic_path, "constant", (), value)

    def _emit(
        self,
        path: str,
        primitive: str,
        parents: Sequence[Scalar],
        value: float,
        data: Any = None,
    ) -> Scalar:
        return self._new_node(path, primitive, parents, value, data=data)

    def copy(self, x: Scalar, path: str) -> Scalar:
        return self._emit(path, "copy", (x,), x.value)

    def add(self, x: Scalar, y: Scalar, path: str) -> Scalar:
        return self._emit(path, "add", (x, y), rn64(x.value + y.value))

    def sub(self, x: Scalar, y: Scalar, path: str) -> Scalar:
        return self._emit(path, "sub", (x, y), rn64(x.value - y.value))

    def neg(self, x: Scalar, path: str) -> Scalar:
        return self._emit(path, "neg", (x,), rn64(-x.value))

    def mul(self, x: Scalar, y: Scalar, path: str) -> Scalar:
        return self._emit(path, "mul", (x, y), rn64(x.value * y.value))

    def div(self, x: Scalar, y: Scalar, path: str) -> Scalar:
        if y.value == 0.0:
            raise AutodiffError("division denominator is zero")
        return self._emit(path, "div", (x, y), rn64(x.value / y.value))

    def exp(self, x: Scalar, path: str) -> Scalar:
        return self._emit(path, "exp", (x,), rn64(self.kernel.exp_R02(x.value)))

    def log(self, x: Scalar, path: str) -> Scalar:
        if x.value == 0.0:
            raise AutodiffError("log reverse denominator is zero")
        return self._emit(path, "log", (x,), rn64(self.kernel.log_R02(x.value)))

    def sqrt(self, x: Scalar, path: str) -> Scalar:
        value = rn64(self.kernel.sqrt_R02(x.value))
        if value == 0.0:
            raise AutodiffError("sqrt reverse denominator is zero")
        return self._emit(path, "sqrt", (x,), value)

    def sigmoid(self, x: Scalar, path: str) -> Scalar:
        return self._emit(path, "sigmoid", (x,), rn64(self.kernel.sigmoid_R02(x.value)))

    def silu(self, x: Scalar, path: str) -> Scalar:
        sigmoid = self.sigmoid(x, f"{path}/sigmoid")
        return self.mul(x, sigmoid, f"{path}/multiply")

    def clamp(self, x: Scalar, lower: float, upper: float, path: str) -> Scalar:
        lower_value = rn64(lower)
        upper_value = rn64(upper)
        if lower_value > upper_value:
            raise AutodiffError("clamp lower bound exceeds upper bound")
        value = rn64(min(upper_value, max(lower_value, x.value)))
        return self._emit(path, "clamp", (x,), value, (lower_value, upper_value))

    def minimum(self, x: Scalar, y: Scalar, path: str) -> Scalar:
        winner = 0 if x.value <= y.value else 1
        return self._emit(path, "minimum", (x, y), (x.value, y.value)[winner], winner)

    def identity_join(self, base: Scalar, residual: Scalar, path: str) -> Scalar:
        if residual.value != 0.0 or binary64_bits(residual.value) != binary64_bits(0.0):
            raise AutodiffError("identity join requires canonical structural +0.0 residual")
        return self._emit(path, "identity_join", (base, residual), base.value)

    def affine(
        self,
        inputs: Sequence[Scalar],
        weights: Sequence[Sequence[Scalar]],
        bias: Sequence[Scalar],
        path: str,
    ) -> tuple[Scalar, ...]:
        x = tuple(inputs)
        rows = tuple(tuple(row) for row in weights)
        b = tuple(bias)
        if not x or len(rows) != len(b) or any(len(row) != len(x) for row in rows):
            raise AutodiffError("affine scalar shape drift")
        outputs: list[Scalar] = []
        for j, (row, start) in enumerate(zip(rows, b)):
            accumulator = start
            for k, (weight, value) in enumerate(zip(row, x)):
                product = self.mul(weight, value, f"{path}/j{j}/k{k}/product")
                accumulator = self.add(accumulator, product, f"{path}/j{j}/k{k}/accumulate")
            outputs.append(accumulator)
        return tuple(outputs)

    def affine_with_output_callback(
        self,
        inputs: Sequence[Scalar],
        weights: Sequence[Sequence[Scalar]],
        bias: Sequence[Scalar],
        path: str,
        output_callback: Callable[[Scalar, int], Scalar],
    ) -> tuple[Scalar, ...]:
        """Emit affine ``j`` and its downstream scalar branch before ``j+1``.

        This is the authoritative layer builder when each affine coordinate is
        immediately activated or otherwise transformed independently.  It
        preserves the frozen memoized-DFS postorder that a later canonical
        reduction over the returned outputs will reconstruct.
        """

        x = tuple(inputs)
        rows = tuple(tuple(row) for row in weights)
        b = tuple(bias)
        if not x or len(rows) != len(b) or any(len(row) != len(x) for row in rows):
            raise AutodiffError("affine scalar shape drift")
        if not callable(output_callback):
            raise AutodiffError("affine output callback must be callable")
        outputs: list[Scalar] = []
        for j, (row, start) in enumerate(zip(rows, b)):
            accumulator = start
            for k, (weight, value) in enumerate(zip(row, x)):
                product = self.mul(weight, value, f"{path}/j{j}/k{k}/product")
                accumulator = self.add(
                    accumulator, product, f"{path}/j{j}/k{k}/accumulate"
                )
            transformed = output_callback(accumulator, j)
            if not isinstance(transformed, Scalar) or transformed.tape is not self:
                raise AutodiffError("affine output callback must return a scalar from this tape")
            outputs.append(transformed)
        return tuple(outputs)

    def roster_mean(
        self, rows: Sequence[Sequence[Scalar]], path: str
    ) -> tuple[Scalar, ...]:
        matrix = tuple(tuple(row) for row in rows)
        if not matrix or not matrix[0] or any(len(row) != len(matrix[0]) for row in matrix):
            raise AutodiffError("roster mean shape drift")
        outputs: list[Scalar] = []
        for column in range(len(matrix[0])):
            operands = tuple(row[column] for row in matrix)
            exact = sum((Fraction.from_float(item.value) for item in operands), Fraction(0))
            value = rn64(float(exact / len(matrix)))
            outputs.append(
                self._emit(
                    f"{path}/column{column}",
                    "roster_mean",
                    operands,
                    value,
                    len(matrix),
                )
            )
        return tuple(outputs)

    def strict_max(
        self, values: Sequence[Scalar], path: str, *, primitive: str = "strict_max"
    ) -> Scalar:
        operands = tuple(values)
        if not operands:
            raise AutodiffError("strict maximum requires operands")
        winner = 0
        best = operands[0].value
        for index, operand in enumerate(operands[1:], start=1):
            if operand.value > best:
                best = operand.value
                winner = index
        return self._emit(path, primitive, operands, best, winner)

    def roster_max(
        self, rows: Sequence[Sequence[Scalar]], path: str
    ) -> tuple[Scalar, ...]:
        matrix = tuple(tuple(row) for row in rows)
        if not matrix or not matrix[0] or any(len(row) != len(matrix[0]) for row in matrix):
            raise AutodiffError("roster maximum shape drift")
        return tuple(
            self.strict_max(
                tuple(row[column] for row in matrix),
                f"{path}/column{column}",
                primitive="roster_max",
            )
            for column in range(len(matrix[0]))
        )

    def centered_clamp(
        self,
        logits: Sequence[Scalar],
        probability: ProbabilityObject,
        path: str,
    ) -> tuple[Scalar, ...]:
        operands = tuple(logits)
        if len(operands) != len(probability.logits) or probability.fixed:
            raise AutodiffError("centered categorical support drift")
        if any(not _same_bits(node.value, value) for node, value in zip(operands, probability.logits)):
            raise AutodiffError("stored probability logits differ from graph logits")
        group = _CenteredGroup(
            self._center_group_counter,
            probability,
            tuple(node.node_id for node in operands),
        )
        self._center_group_counter += 1
        hub = self._emit(
            f"{path}/hub",
            "centered_clamp_hub",
            operands,
            0.0,
            group,
        )
        return tuple(
            self._emit(
                f"{path}/candidate{index}",
                "centered_clamp_slot",
                (hub,),
                value,
                (group, index),
            )
            for index, value in enumerate(probability.q)
        )

    def stored_categorical(self, probability: ProbabilityObject) -> StoredCategorical:
        if probability.fixed:
            raise AutodiffError("fixed tokens have no categorical reverse node")
        return StoredCategorical(
            probability,
            probability.stored_log_p,
            probability.stored_H,
        )

    def categorical_log_probability(
        self,
        q: Sequence[Scalar],
        stored: StoredCategorical,
        chosen: Candidate,
        path: str,
    ) -> Scalar:
        operands = tuple(q)
        if len(operands) != len(stored.probability.candidates):
            raise AutodiffError("categorical q/support shape drift")
        try:
            chosen_index = stored.probability.candidates.index(chosen)
        except ValueError as exc:
            raise AutodiffError("chosen candidate is absent from stored support") from exc
        return self._emit(
            path,
            "categorical_log_probability",
            operands,
            stored.stored_log_p[chosen_index],
            (stored, chosen_index),
        )

    def categorical_entropy(
        self, q: Sequence[Scalar], stored: StoredCategorical, path: str
    ) -> Scalar:
        operands = tuple(q)
        if len(operands) != len(stored.probability.candidates):
            raise AutodiffError("categorical entropy q/support shape drift")
        return self._emit(path, "categorical_entropy", operands, stored.stored_H, stored)

    def _dfs_primitive_postorder(self, root_id: int) -> tuple[int, ...]:
        visited: set[int] = set()
        postorder: list[int] = []

        def visit(node_id: int) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            node = self._nodes[node_id]
            for parent_id in node.parents:
                visit(parent_id)
            if node.primitive not in {"leaf", "constant"}:
                postorder.append(node_id)

        visit(root_id)
        return tuple(postorder)

    def _append(self, queues: list[list[float]], parent_id: int, value: float) -> None:
        queues[parent_id].append(rn64(value))

    def backward(self, total: Scalar) -> BackwardResult:
        if total.tape is not self or total.node_id != len(self._nodes) - 1:
            raise AutodiffError("total must be the final emitted scalar root")
        primitive_postorder = self._dfs_primitive_postorder(total.node_id)
        all_primitives = tuple(
            node.scalar.node_id
            for node in self._nodes
            if node.primitive not in {"leaf", "constant"}
        )
        if set(primitive_postorder) != set(all_primitives):
            raise AutodiffError("a primitive was emitted but is unreachable from total")
        leaf_handles = tuple(
            node.scalar.node_id
            for node in self._nodes
            if node.primitive in {"leaf", "constant"}
        )
        compiled_handles = leaf_handles + primitive_postorder
        if len(compiled_handles) != len(self._nodes) or len(set(compiled_handles)) != len(self._nodes):
            raise AutodiffError("memoized DFS compilation did not produce one id per node")
        construction_to_node_id = [0] * len(self._nodes)
        for compiled_id, handle in enumerate(compiled_handles):
            construction_to_node_id[handle] = compiled_id
        compiled_nodes = tuple(self._nodes[handle] for handle in compiled_handles)
        compiled_parents = tuple(
            tuple(construction_to_node_id[parent] for parent in node.parents)
            for node in compiled_nodes
        )
        compiled_table = tuple(
            NodeRecord(
                node_id,
                node.scalar.semantic_path,
                node.primitive,
                compiled_parents[node_id],
            )
            for node_id, node in enumerate(compiled_nodes)
        )

        queues: list[list[float]] = [[] for _ in compiled_nodes]
        root_id = construction_to_node_id[total.node_id]
        queues[root_id].append(1.0)
        adjoints = [0.0] * len(self._nodes)
        centered: dict[int, list[float | None]] = {}

        for node_id in range(len(compiled_nodes) - 1, -1, -1):
            node = compiled_nodes[node_id]
            g = 0.0
            for contribution in queues[node_id]:
                g = rn64(g + contribution)
            adjoints[node_id] = g
            parents = compiled_parents[node_id]
            values = tuple(compiled_nodes[parent].scalar.value for parent in parents)
            primitive = node.primitive

            if primitive in {"leaf", "constant"}:
                continue
            if primitive == "copy":
                self._append(queues, parents[0], rn64(g))
            elif primitive == "add":
                self._append(queues, parents[0], rn64(g))
                self._append(queues, parents[1], rn64(g))
            elif primitive == "sub":
                self._append(queues, parents[0], rn64(g))
                self._append(queues, parents[1], rn64(-g))
            elif primitive == "neg":
                self._append(queues, parents[0], rn64(-g))
            elif primitive == "mul":
                self._append(queues, parents[0], rn64(g * values[1]))
                self._append(queues, parents[1], rn64(g * values[0]))
            elif primitive == "div":
                if values[1] == 0.0:
                    raise AutodiffError("division reverse denominator is zero")
                self._append(queues, parents[0], rn64(g / values[1]))
                yy = rn64(values[1] * values[1])
                if yy == 0.0:
                    raise AutodiffError("squared division denominator is zero")
                gx = rn64(g * values[0])
                qy = rn64(gx / yy)
                self._append(queues, parents[1], rn64(-qy))
            elif primitive == "exp":
                self._append(queues, parents[0], rn64(g * node.scalar.value))
            elif primitive == "log":
                if values[0] == 0.0:
                    raise AutodiffError("log reverse denominator is zero")
                self._append(queues, parents[0], rn64(g / values[0]))
            elif primitive == "sqrt":
                two_z = rn64(2.0 * node.scalar.value)
                if two_z == 0.0:
                    raise AutodiffError("sqrt reverse denominator is zero")
                self._append(queues, parents[0], rn64(g / two_z))
            elif primitive == "sigmoid":
                one_minus = rn64(1.0 - node.scalar.value)
                local = rn64(node.scalar.value * one_minus)
                self._append(queues, parents[0], rn64(g * local))
            elif primitive == "clamp":
                lower, upper = node.data
                contribution = rn64(g) if lower < values[0] < upper else 0.0
                self._append(queues, parents[0], contribution)
            elif primitive in {"minimum", "strict_max", "roster_max"}:
                winner = int(node.data)
                for slot, parent_id in enumerate(parents):
                    self._append(queues, parent_id, rn64(g) if slot == winner else 0.0)
            elif primitive == "roster_mean":
                n64 = rn64(int(node.data))
                contribution = rn64(g / n64)
                for parent_id in parents:
                    self._append(queues, parent_id, contribution)
            elif primitive == "identity_join":
                self._append(queues, parents[0], rn64(g))
                self._append(queues, parents[1], rn64(g))
            elif primitive == "categorical_log_probability":
                stored, chosen_index = node.data
                for slot, (parent_id, p) in enumerate(
                    zip(parents, stored.probability.probabilities)
                ):
                    indicator = 1.0 if slot == chosen_index else 0.0
                    local = rn64(indicator - p)
                    self._append(queues, parent_id, rn64(g * local))
            elif primitive == "categorical_entropy":
                stored = node.data
                for parent_id, p, log_p in zip(
                    parents, stored.probability.probabilities, stored.stored_log_p
                ):
                    lp_plus_h = rn64(log_p + stored.stored_H)
                    p_term = rn64(p * lp_plus_h)
                    local = rn64(-p_term)
                    self._append(queues, parent_id, rn64(g * local))
            elif primitive == "centered_clamp_slot":
                group, slot = node.data
                group_values = centered.setdefault(
                    group.group_id, [None] * len(group.probability.candidates)
                )
                group_values[slot] = g
                # The scalar edge remains explicit and contributes exact zero;
                # the bespoke vector payload is retained until the lower-id hub.
                self._append(queues, parents[0], 0.0)
            elif primitive == "centered_clamp_hub":
                group = node.data
                group_values = centered.get(group.group_id)
                if group_values is None or any(value is None for value in group_values):
                    raise AutodiffError("centered-clamp output adjoints were not complete")
                contributions = clamp_centered_max_adjoint(
                    group.probability,
                    tuple(value for value in group_values if value is not None),
                )
                for parent_id, contribution in zip(
                    group.logit_parent_ids, contributions
                ):
                    self._append(
                        queues,
                        construction_to_node_id[parent_id],
                        contribution,
                    )
            else:
                raise AutodiffError(f"undeclared reverse primitive {primitive}")

        parameter_gradients: list[GradientTensor] = []
        for parameter in self._parameter_specs:
            ids = self._parameter_ids[parameter.name]
            parameter_gradients.append(
                GradientTensor(
                    parameter.name,
                    parameter.shape,
                    tuple(adjoints[construction_to_node_id[node_id]] for node_id in ids),
                )
            )
        leaf_gradients = tuple(
            (
                node.scalar.semantic_path,
                adjoints[construction_to_node_id[node.scalar.node_id]],
            )
            for node in self._nodes
            if node.primitive == "leaf" and node.parameter is None
        )
        return BackwardResult(
            node_table=compiled_table,
            adjoints=tuple(adjoints),
            leaf_gradients=leaf_gradients,
            parameter_gradients=tuple(parameter_gradients),
            tape_identity=id(self),
            construction_to_node_id=tuple(construction_to_node_id),
        )
