OBSERVATION_FIELD_5_FORMULA=mean_{i in A_t}(abs(g_i-x_i)/4)
OBSERVATION_FIELD_5_RANGE=[0,1]
C_FIELD_5_POLICY=MASK_TO_ZERO
RATIONALE=This field is the active-member mean normalized absolute tracking error, so D retains current demand-mismatch information while C masks it to preserve the calendar/static information null.