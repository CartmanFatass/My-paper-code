"""Public-information C/J/R state machines; no native environment access."""
import hashlib

import numpy as np

from ..control import COMMANDS, OrdinaryController, _Scores, choose_mask, decode_public_state, predict_next
from ..host import mask_bits

COUNT_KEYS = ("requested_candidates", "scored_candidates", "cached_candidates",
              "geometry_rows_computed", "geometry_rows_reused")
KINDS = ("motion", "mask", "joint", "option", "arrival")


def empty_counts():
    return {kind: {key: 0 for key in COUNT_KEYS} for kind in KINDS}


def trace_counts(decision, totals):
    for kind in KINDS:
        if kind in decision:
            value = decision[kind].get("counts", decision[kind])
            for key in COUNT_KEYS:
                totals[kind][key] += int(value[key])


def joint_select(controller, t, state, old_mask):
    if t != controller.next_t or t % 10:
        raise ValueError("joint pass requires next legal boundary")
    base, users = decode_public_state(state, 8)
    controller.users = users
    mask_bits(old_mask, 8)
    chosen, current_mask = controller.commands.copy(), int(old_mask)
    scorer, choices = _Scores(users), []
    masks = list(range(1, 256)) * len(COMMANDS)
    order = [(t+j) % 8 for j in range(8)]
    for member in order:
        entering, entering_mask = chosen[member].copy(), current_mask
        candidates = np.repeat(chosen[None], len(COMMANDS), axis=0)
        candidates[:, member] = COMMANDS
        predicted = predict_next(np.broadcast_to(base, candidates.shape), candidates)
        movement = np.linalg.norm(predicted-base, axis=2).sum(axis=1)
        scores = scorer.score(np.repeat(predicted, 255, axis=0), masks)
        index = max(range(len(scores)), key=lambda k: (scores[k]["J"], scores[k]["served"],
            -float(movement[k//255]), bool(np.array_equal(COMMANDS[k//255], entering)
            and masks[k] == entering_mask), -(k//255), -masks[k]))
        command_index, current_mask = index//255, masks[index]
        readings = np.asarray([[s["J"], s["served"], s["quality"], s["energy_penalty"],
                                movement[k//255]] for k, s in enumerate(scores)], dtype="<f8")
        chosen[member] = COMMANDS[command_index]
        choices.append(dict(member=member, entering=entering.tolist(), entering_mask=entering_mask,
            selected=chosen[member].tolist(), selected_mask=current_mask, selected_score=scores[index],
            movement=float(movement[command_index]), score_digest=hashlib.sha256(readings.tobytes()).hexdigest()))
    controller.commands = chosen.copy()
    controller.positions = predict_next(base, chosen)
    controller.next_t += 1
    trace = dict(scorer.counts, member_order=order, choices=choices,
                 candidate_order="command lexicographic then mask integer; rows J,served,quality,height,movement <f8")
    return chosen, current_mask, trace


class Program:
    def __init__(self, arm, horizon=500):
        if arm not in ("C", "J", "R"):
            raise ValueError("unknown fixed program")
        self.arm, self.horizon = arm, horizon
        self.controller = OrdinaryController(8)
        self.plan = None
        self.option_old_mask = None

    def _forced(self, t, state, command):
        c = self.controller
        if t != c.next_t:
            raise ValueError("forced operation skipped/duplicated the actual clock")
        if t % 10 == 0:
            c.positions, c.users = decode_public_state(state, 8)
        elif state is not None:
            raise ValueError("fresh global state between legal snapshots")
        c.commands = np.asarray(command, dtype=np.float32).copy()
        c.positions = predict_next(c.positions, c.commands)
        c.next_t += 1
        return c.commands.copy()

    def select(self, t, state, old_mask):
        if t != self.controller.next_t or ((state is not None) != (t % 10 == 0)):
            raise ValueError("invalid clock or public snapshot cadence")
        decision = {"t": t, "old_mask": int(old_mask), "phase": "ordinary"}
        if self.arm == "R" and t == 40:
            from .option import plan_option
            positions, users = decode_public_state(state, 8)
            self.plan = plan_option(positions, users, old_mask, t=40, horizon=self.horizon)
            self.option_old_mask = old_mask
            decision["option"] = self.plan
        if self.plan is not None and self.plan["initiated"] and t <= self.plan["arrival_t"]:
            if old_mask != self.option_old_mask:
                raise ValueError("transit changed the old mask")
            if t < self.plan["arrival_t"]:
                command = self._forced(t, state, self.plan["commands"][t-40])
                decision["phase"] = "transit"
            else:
                from .option import arrival_mask
                positions, users = decode_public_state(state, 8)
                command = self._forced(t, state, np.zeros((8, 3), dtype=np.float32))
                old_mask, trace = arrival_mask(users, positions, self.plan["member"])
                decision["arrival"] = trace
                decision["phase"] = "arrival"
                decision["arrival_prediction_error"] = (positions-np.asarray(self.plan["predicted_destination"])).tolist()
        elif self.arm == "J" and t % 10 == 0:
            command, old_mask, trace = joint_select(self.controller, t, state, old_mask)
            decision["joint"] = trace
            decision["phase"] = "joint"
        else:
            command, predicted, trace = self.controller.select(t, state, old_mask)
            decision["motion"] = trace
            if t % 10 == 0:
                old_mask, trace = choose_mask(self.controller.users, predicted, old_mask)
                decision["mask"] = trace
        decision["issued_mask"] = int(old_mask)
        return command, int(old_mask), decision
