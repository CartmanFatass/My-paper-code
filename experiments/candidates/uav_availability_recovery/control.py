"""Public observation and persistent commands for the fixed recovery study."""

from __future__ import annotations

import numpy as np

from ha_ctse_process.uav_g0_controllers import G0CurrentInformation, SameInformationController
from ha_ctse_process.uav_g0_geometry import TARGET_LABELS, actions_toward_targets


HORIZON = 500
FEATURE_DIM = 496
COMMANDS = ("own_stage", "vacated_primary", "inward_gate", "hold_current")


class RecoveryControl:
    """Source is used only to obtain registered geometry and issued ownership."""

    def __init__(self, source, env):
        rows = env.current_rows()
        self.shadow = SameInformationController(source, [row.handle for row in rows])
        self.role_by_handle = {
            handle: TARGET_LABELS.index(label)
            for handle, label in self.shadow.original_ownership.items()
        }
        self.user_xy = np.array(source.geometry.users_xy, dtype=np.float32, copy=True)
        self.user_xy.flags.writeable = False
        self.leave_step = None
        self.rejoin_step = None
        self.event_owner = -1
        self.last_view_step = -1
        self.events_seen = []
        self.reserve_targets = None
        self.last_joint_action = None
        self.decision_steps = []
        self.shadow_incumbents = []

    def consume(self, events, rows, physical_step):
        event_clock = False
        for event in events:
            if int(event.physical_step) != physical_step:
                raise ValueError("lifecycle event belongs to a different decision boundary")
            signature = (event.kind, event.physical_step, event.previous_handle)
            if signature in self.events_seen:
                raise ValueError("lifecycle event consumed twice")
            self.events_seen.append(signature)
            if event.kind == "LEAVE":
                if self.leave_step is not None:
                    raise ValueError("the declared host has one leave")
                self.shadow.on_leave(event.previous_handle, rows)
                self.event_owner = self.role_by_handle[event.previous_handle]
                self.leave_step = int(physical_step)
            elif event.kind == "REJOIN":
                self.shadow.on_rejoin(event.previous_handle, event.current_handle, physical_step)
                role = self.role_by_handle.pop(event.previous_handle)
                self.role_by_handle[event.current_handle] = role
                self.rejoin_step = int(physical_step)
            else:
                raise ValueError(f"unknown lifecycle event {event.kind}")
            event_clock = True
        return event_clock

    def view(self, env, events):
        t = int(env.current_step)
        if t != self.last_view_step + 1:
            raise ValueError("shadow S must be observed once on every native step")
        self.last_view_step = t
        storage_rows = env.current_rows()
        event_clock = self.consume(events, storage_rows, t)
        geometry = self.shadow.geometry
        information = G0CurrentInformation(
            rows=storage_rows,
            user_demand_mbps=env._current_user_qos_demand_bps() / 1e6,
            user_delivered_rate_mbps=env.last_user_rates_mbps,
            # G0 presents roster rows in storage order, native association in world order.
            channel_association=np.asarray(env.connections)[env._storage_to_internal],
            base_xy=geometry.base_xy,
            primary_xy=geometry.primary_xy,
            gate_xy=geometry.gate_xy,
            stage_xy=geometry.stage_xy,
        )
        shadow_targets = self.shadow.target_map(information, physical_step=t)
        order = np.asarray(sorted(range(8), key=lambda i: self.role_by_handle[storage_rows[i].handle]))
        rows = tuple(storage_rows[i] for i in order)
        roles = [self.role_by_handle[row.handle] for row in rows]
        if roles != list(range(8)):
            raise ValueError("public original assignment inventory drifted")
        positions = np.stack([row.position for row in rows])
        active = np.asarray([row.active for row in rows], dtype=bool)
        targets = np.stack([shadow_targets[row.handle] for row in rows])
        if self.reserve_targets is None or self.leave_step is None:
            self.reserve_targets = targets[6:].copy()
        issued = targets.copy()
        issued[6:] = self.reserve_targets
        age = 0 if self.leave_step is None else (
            min(t, self.rejoin_step) if self.rejoin_step is not None else t
        ) - self.leave_step
        decision = self.leave_step is not None and (event_clock or t % 10 == 0)
        incumbent = 0
        candidates = None
        if self.leave_step is not None:
            options = []
            for reserve in range(2):
                options.append(np.array([
                    [*geometry.stage_xy[reserve], 50.0],
                    [*geometry.primary_xy[self.event_owner], 50.0],
                    [*geometry.gate_xy[self.event_owner], 50.0],
                    positions[6 + reserve],
                ], dtype=np.float64))
            candidates = np.repeat(targets[None, :, :], 16, axis=0)
            for joint in range(16):
                candidates[joint, 6] = options[0][joint // 4]
                candidates[joint, 7] = options[1][joint % 4]
            incumbent_choices = []
            for reserve in range(2):
                matches = np.flatnonzero(np.all(options[reserve] == targets[6 + reserve], axis=1))
                if not len(matches):
                    raise ValueError("shadow S target is outside the declared command set")
                incumbent_choices.append(int(matches[0]))
            incumbent = 4 * incumbent_choices[0] + incumbent_choices[1]
        event_feature = np.zeros(6, dtype=np.float32)
        if self.event_owner >= 0:
            event_feature[self.event_owner] = 1.0
        incumbent_feature = np.eye(16, dtype=np.float32)[incumbent]
        demand = np.asarray(information.user_demand_mbps)
        feature = np.concatenate([
            positions.ravel() / 8000.0,
            np.stack([row.velocity for row in rows]).ravel() / float(env.max_speed),
            active.astype(np.float32),
            information.channel_association[order].astype(np.float32).ravel(),
            demand,
            np.log1p(information.user_delivered_rate_mbps / demand) / np.log(101.0),
            geometry.base_xy / 8000.0,
            geometry.primary_xy.ravel() / 8000.0,
            geometry.gate_xy.ravel() / 8000.0,
            geometry.stage_xy.ravel() / 8000.0,
            self.user_xy.ravel() / 8000.0,
            issued.ravel() / 8000.0,
            event_feature,
            [age / 100.0, float(self.rejoin_step is not None), t / HORIZON, (HORIZON-t) / HORIZON],
            incumbent_feature,
        ]).astype(np.float32)
        if feature.shape != (FEATURE_DIM,) or not np.isfinite(feature).all():
            raise ValueError(f"public feature shape/finite error: {feature.shape}")
        return {
            "step": t, "decision": decision, "feature": feature,
            "positions": positions, "active": active, "targets": targets,
            "candidate_targets": candidates, "incumbent": incumbent,
            "rows": rows, "storage_rows": storage_rows, "information": information,
            "age": age, "association": information.channel_association[order],
        }

    def snapshot(self, env, view):
        from .predictor import PublicSnapshot

        if not view["decision"]:
            raise ValueError("ordinary planner called outside a decision boundary")
        return PublicSnapshot(
            positions=view["positions"], active=view["active"], user_xy=self.user_xy,
            demand_mbps=view["information"].user_demand_mbps,
            base_xy=self.shadow.geometry.base_xy,
            candidate_targets=view["candidate_targets"],
            incumbent_action=view["incumbent"], physical_step=view["step"],
            absence_age=view["age"], event_owner_index=self.event_owner,
            has_returned=self.rejoin_step is not None, max_speed=float(env.max_speed),
            max_vertical_speed_mps=float(env.max_vertical_speed_mps),
            time_step=float(env.time_step), area_size=float(env.area_size),
            height_range=tuple(float(v) for v in env.height_range),
        )

    def commands(self, env, view, *, arm, joint_action=None):
        targets = view["targets"].copy()
        if arm == "S" or self.leave_step is None:
            self.reserve_targets = targets[6:].copy()
        else:
            if view["decision"]:
                if joint_action is None or not 0 <= int(joint_action) < 16:
                    raise ValueError("missing or invalid joint command")
                self.reserve_targets = view["candidate_targets"][int(joint_action), 6:].copy()
                self.last_joint_action = int(joint_action)
                self.decision_steps.append(view["step"])
                self.shadow_incumbents.append(view["incumbent"])
            elif joint_action is not None:
                raise ValueError("command changed between allowed clocks")
            targets[6:] = self.reserve_targets
        role_actions = actions_toward_targets(
            physical_positions=view["positions"], target_positions=targets,
            active_mask=view["active"], max_speed=env.max_speed,
            max_vertical_speed=env.max_vertical_speed_mps, time_step=env.time_step,
        )
        dense = np.stack([role_actions[self.role_by_handle[row.handle]] for row in view["storage_rows"]])
        return dense, targets
