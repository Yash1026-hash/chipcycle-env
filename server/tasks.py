"""
ChipCycle - Task definitions with synthetic chip design report data.

Contains three tasks of increasing difficulty:
  Task 1 (Easy): Synthesis QoR Report Review
  Task 2 (Medium): STA Timing Path Debug
  Task 3 (Hard): Multi-Corner Multi-Mode Sign-off Triage
"""

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Task 1 — EASY — Synthesis QoR Report Review
# ---------------------------------------------------------------------------
TASK_1_OVERVIEW = """
============================================================
  SYNTHESIS QUALITY-OF-RESULTS REPORT
  Design:        uart_controller
  Library:       sky130_fd_sc_hd (SkyWater 130nm)
  Clock:         clk_sys — period 10.0ns (100 MHz)
  Tool:          Genus 21.14 / Design Compiler P-2019.03
  Date:          2026-03-28 14:22:07
============================================================

AREA SUMMARY
  Combinational cells:         1,247
  Sequential cells (flip-flops):  89
  Macro cells:                     0
  Total cell area:          8,432 um^2
  Utilization:                   72%

TIMING SUMMARY
  Worst Negative Slack (WNS):    -0.82 ns   ** VIOLATED **
  Total Negative Slack (TNS):    -3.41 ns
  Worst Hold Slack (WHS):        +0.12 ns   (MET)
  Number of violating paths:     7

DESIGN RULE VIOLATIONS
  Max fanout violations:          3
  Max transition violations:      7
  Max capacitance violations:     1
  Total DRV count:               11

CELL MAPPING
  Unmapped cells:                 2   ** WARNING **
  Cells:  behavioral_mux4 (line 142), async_latch_gen (line 87)

POWER ESTIMATE
  Dynamic power:            4.2 mW
  Clock network power:      1.1 mW
  Leakage power:            0.8 mW
  Total power:              6.1 mW
  Power budget:            10.0 mW   (OK)

QoR NOTES
  - Optimization converged in 3 iterations
  - No multibit banking applied
  - Clock gating efficiency: 62%
============================================================
"""

TASK_1_SECTIONS = {
    "timing_summary": """
DETAILED TIMING SUMMARY
============================================================
Path Group: clk_sys
  Worst setup slack:        -0.82 ns (VIOLATED)
  Critical path:            reg_bank/r3[7] -> tx_shift/data_in[7]
  Path delay:               10.82 ns
  Clock period:             10.00 ns
  Clock uncertainty:         0.15 ns
  Library setup time:        0.09 ns

  Path breakdown:
    Source FF clk->Q:        0.31 ns
    Combinational logic:     9.92 ns  (18 levels of logic)
    Destination setup:       0.09 ns
    Clock network delta:     0.50 ns

  ** 18 levels of logic — high combinational depth **
  ** Consider retiming or pipeline insertion **

  Other violating paths:
    Path 2:  reg_bank/r1[3] -> baud_gen/count[3]   slack: -0.54 ns
    Path 3:  ctrl_fsm/state[1] -> tx_shift/load      slack: -0.33 ns
    Path 4:  rx_sample/bit_cnt[2] -> reg_bank/wr[2]  slack: -0.28 ns
    Path 5:  reg_bank/r2[0] -> parity_gen/p_out       slack: -0.15 ns
    Path 6:  ctrl_fsm/state[0] -> ctrl_fsm/next[2]    slack: -0.11 ns
    Path 7:  baud_gen/count[7] -> baud_gen/count[0]   slack: -0.08 ns
============================================================
""",
    "design_rule_violations": """
DESIGN RULE VIOLATION DETAILS
============================================================
MAX FANOUT VIOLATIONS (3):
  Net: ctrl_fsm/state[0]
    Fanout: 42    Max allowed: 32
    Driver: sky130_fd_sc_hd__buf_2

  Net: clk_sys_buf
    Fanout: 38    Max allowed: 32
    Driver: sky130_fd_sc_hd__clkbuf_4

  Net: rst_n_sync
    Fanout: 89    Max allowed: 32
    Driver: sky130_fd_sc_hd__buf_1   ** severely overloaded **

MAX TRANSITION VIOLATIONS (7):
  Net: reg_bank/r3[7]     transition: 2.8ns (max: 1.5ns)
  Net: tx_shift/data_in[5] transition: 2.1ns (max: 1.5ns)
  Net: baud_gen/count[7]   transition: 1.9ns (max: 1.5ns)
  Net: ctrl_fsm/state[1]   transition: 1.8ns (max: 1.5ns)
  Net: rx_sample/data[3]   transition: 1.7ns (max: 1.5ns)
  Net: parity_gen/p_out     transition: 1.6ns (max: 1.5ns)
  Net: reg_bank/r1[0]      transition: 1.55ns (max: 1.5ns)

MAX CAPACITANCE VIOLATIONS (1):
  Net: rst_n_sync
    Cap: 285 fF    Max allowed: 180 fF
    ** correlated with fanout violation on same net **
============================================================
""",
    "unmapped_cells": """
UNMAPPED CELL DETAILS
============================================================
WARNING: 2 cells could not be mapped to target library.

Cell 1: behavioral_mux4 (uart_controller.v, line 142)
  Type: Generic 4:1 multiplexer (behavioral)
  Reason: No direct 4:1 mux cell in sky130_fd_sc_hd library
  Impact: Will cause synthesis failure if not resolved
  Fix: Decompose into 2:1 mux tree or use assign statements

Cell 2: async_latch_gen (uart_controller.v, line 87)
  Type: Inferred latch from incomplete if-else
  Reason: Latch inferred — likely unintentional
  Impact: Latches cause timing analysis complications and
          potential race conditions in synchronous designs
  Fix: Add else clause or default assignment to eliminate latch

NOTE: Unmapped cells will be excluded from timing analysis,
      which may mask additional timing violations.
============================================================
""",
    "power_report": """
POWER ANALYSIS DETAILS
============================================================
Hierarchy Power Breakdown:
  uart_controller (top)        6.1 mW  (100%)
    +-- reg_bank               1.8 mW  (29.5%)
    +-- tx_shift               0.9 mW  (14.8%)
    +-- rx_sample              0.7 mW  (11.5%)
    +-- baud_gen               0.6 mW  (9.8%)
    +-- ctrl_fsm               0.4 mW  (6.6%)
    +-- parity_gen             0.2 mW  (3.3%)
    +-- clock_network          1.1 mW  (18.0%)
    +-- leakage                0.8 mW  (13.1%)

Power budget: 10.0 mW
Status: WITHIN BUDGET (61% utilized)

Clock gating statistics:
  Gatable FFs: 89
  Gated FFs:   55  (62% efficiency)
  Potential savings with higher gating: ~0.4 mW
============================================================
""",
}

TASK_1_ISSUES: List[Dict[str, Any]] = [
    {
        "id": "T1_TIMING",
        "issue_type": "timing_violation",
        "location": "clk_sys path group",
        "severity": "critical",
        "description": "WNS of -0.82ns — 7 paths violate setup timing. Critical path has 18 levels of combinational logic.",
        "root_cause": "Excessive combinational depth between reg_bank and tx_shift",
        "recommended_fix": "Pipeline insertion or logic retiming to reduce combinational depth",
        "keywords": ["timing", "wns", "setup", "violation", "slack", "negative", "critical path", "combinational depth", "pipeline", "retim"],
    },
    {
        "id": "T1_UNMAPPED",
        "issue_type": "unmapped_cells",
        "location": "behavioral_mux4 (line 142), async_latch_gen (line 87)",
        "severity": "critical",
        "description": "2 cells not mapped to target library — behavioral mux4 and inferred latch",
        "root_cause": "RTL coding issues: generic mux not in library, incomplete if-else causing latch inference",
        "recommended_fix": "Decompose mux4 into mux2 tree; add default/else to eliminate latch",
        "keywords": ["unmap", "latch", "behavioral", "infer", "mux", "cell", "library"],
    },
    {
        "id": "T1_FANOUT",
        "issue_type": "fanout_violation",
        "location": "rst_n_sync net (fanout: 89, max: 32)",
        "severity": "major",
        "description": "3 max fanout violations. rst_n_sync severely overloaded (89 vs 32 limit) with buf_1 driver.",
        "root_cause": "Reset net driven by weak buffer with too many loads",
        "recommended_fix": "Insert buffer tree for reset distribution; upsize driver to clkbuf_8 or buf_8",
        "keywords": ["fanout", "overload", "buffer", "rst", "reset", "driver", "upsize", "violation"],
    },
    {
        "id": "T1_TRANSITION",
        "issue_type": "transition_violation",
        "location": "7 nets with transition > 1.5ns max",
        "severity": "major",
        "description": "7 max transition violations indicating signal integrity risk. Worst: reg_bank/r3[7] at 2.8ns (max 1.5ns).",
        "root_cause": "Weak drivers and high capacitive loads causing slow transitions",
        "recommended_fix": "Upsize drivers on violating nets; insert buffers to break long wires",
        "keywords": ["transition", "slew", "signal integrity", "slow", "driver", "upsize", "buffer", "violation"],
    },
]


# ---------------------------------------------------------------------------
# Task 2 — MEDIUM — STA Timing Path Debug
# ---------------------------------------------------------------------------
TASK_2_OVERVIEW = """
============================================================
  STATIC TIMING ANALYSIS REPORT
  Design:        spi_master_top
  Clock domains: clk_core (200 MHz), clk_spi (50 MHz), clk_io (100 MHz)
  Corners:       TT_25C_1v80 (nominal)
  Tool:          PrimeTime PX / OpenSTA
  Date:          2026-03-28 16:45:31
  SDC version:   2.1
============================================================

TIMING SUMMARY BY CLOCK GROUP
  clk_core:  WNS = -0.23 ns   TNS = -0.51 ns   VIOLATED
  clk_spi:   WNS = +3.82 ns   TNS =  0.00 ns   MET
  clk_io:    WNS = +0.02 ns   TNS =  0.00 ns   MET (barely)
  cross_clk: WNS = -1.45 ns   TNS = -1.45 ns   VIOLATED

HOLD TIMING SUMMARY
  clk_core:  WHS = +0.05 ns   MET
  clk_spi:   WHS = +0.28 ns   MET
  clk_io:    WHS = -0.04 ns   VIOLATED (1 path)

UNCONSTRAINED PATHS: 0
FALSE PATH EXCEPTIONS: 3 defined in SDC
MULTICYCLE PATH EXCEPTIONS: 1 defined in SDC

NOTE: 5 paths require detailed review. See section analysis.
============================================================
"""

TASK_2_SECTIONS = {
    "path_1_core_violation": """
TIMING PATH 1 — VIOLATED (clk_core domain)
============================================================
Startpoint:  core/alu/operand_reg[15] (rising FF, clk_core)
Endpoint:    core/reg_file/wr_data[15] (rising FF, clk_core)
Path Group:  clk_core
Path Type:   max (setup check)

Point                                  Incr     Path
---------------------------------------------------------------
clock clk_core (rise edge)             0.000    0.000
core/alu/operand_reg[15]/CLK (DFFR)    0.180    0.180  (clock network)
core/alu/operand_reg[15]/Q (DFFR)      0.320    0.500  (CK->Q)
core/alu/U_add32/sum[15] (ADD32)       0.450    0.950  (32-bit add)
core/alu/U_shift/out[15] (BARREL)      0.380    1.330  (barrel shifter)
core/alu/U_mux_res/Y (MUX4)           0.280    1.610  (result select)
core/bypass/fwd_mux/Y (MUX2)          0.190    1.800  (forwarding)
core/hazard/stall_logic/Y (AND3)      0.150    1.950  (hazard detect)
core/reg_file/wr_mux/Y (MUX2)         0.170    2.120  (write select)
core/reg_file/wr_data[15]/D (DFFR)     0.050    2.170  (data arrival)

clock clk_core (rise edge)             5.000    5.000
core/reg_file/wr_data[15]/CLK (DFFR)   0.160    5.160  (clock network)
library setup time                     -0.090    5.070  (required)
---------------------------------------------------------------
data required time                              5.070
data arrival time                               2.170
---------------------------------------------------------------
slack (MET... wait, recalculating)

** ACTUAL CLOCK PERIOD: 5.0 ns (200 MHz)
** But clock uncertainty = 0.30 ns is applied:
   required time = 5.070 - 0.30 = 4.770
** And CRPR adjustment = +0.08 ns

FINAL:
  data required time:    4.850 ns
  data arrival time:     5.080 ns
  slack:                -0.230 ns  ** VIOLATED **

Bottleneck: core/alu/U_add32/sum[15] — 32-bit adder contributes
            0.450 ns (21% of path delay). Consider carry-lookahead
            or adder decomposition.
============================================================
""",
    "path_2_cross_domain": """
TIMING PATH 2 — VIOLATED (cross-clock: clk_core -> clk_spi)
============================================================
Startpoint:  core/spi_ctrl/tx_data_reg[7] (rising FF, clk_core)
Endpoint:    spi_if/shift_reg[7] (rising FF, clk_spi)
Path Group:  cross_clk
Path Type:   max (setup check)

Point                                  Incr     Path
---------------------------------------------------------------
clock clk_core (rise edge)             0.000    0.000
core/spi_ctrl/tx_data_reg[7]/CLK       0.180    0.180
core/spi_ctrl/tx_data_reg[7]/Q         0.290    0.470
** crosses through async_fifo/wr_ptr **
async_fifo/wr_data[7]                  0.150    0.620
async_fifo/mem[7]                      0.200    0.820
async_fifo/rd_data[7]                  0.180    1.000
spi_if/sync_stage1[7]/D                0.050    1.050

clock clk_spi (rise edge)             20.000   20.000
spi_if/shift_reg[7]/CLK                0.120   20.120
library setup time                    -0.090   20.030
---------------------------------------------------------------
slack:                                -1.450 ns  ** VIOLATED **

** NOTE: This path traverses an ASYNCHRONOUS FIFO (async_fifo)
   with gray-code pointer synchronization. The wr_ptr and rd_ptr
   are synchronized using 2-stage synchronizers.

   SDC contains: set_false_path -from clk_core -to clk_spi
   BUT: this specific path through async_fifo/mem is NOT covered
        by the false path exception as currently written.

   QUESTION: Is this a real violation or a constraint issue?
   >> This is a FALSE PATH. The async FIFO handles CDC by design.
      The SDC false_path should be updated to cover memory paths:
      set_false_path -through async_fifo/mem*
============================================================
""",
    "path_3_hold_violation": """
TIMING PATH 3 — HOLD VIOLATION (clk_io domain)
============================================================
Startpoint:  io_pad/rx_sync_reg[1] (rising FF, clk_io)
Endpoint:    io_pad/rx_sync_reg[2] (rising FF, clk_io)
Path Group:  clk_io
Path Type:   min (hold check)

Point                                  Incr     Path
---------------------------------------------------------------
clock clk_io (rise edge)               0.000    0.000
io_pad/rx_sync_reg[1]/CLK              0.220    0.220  (clock network)
io_pad/rx_sync_reg[1]/Q                0.180    0.400  (CK->Q min)
io_pad/rx_sync_reg[2]/D                0.020    0.420  (data arrival)

clock clk_io (rise edge)               0.000    0.000
io_pad/rx_sync_reg[2]/CLK              0.280    0.280  (clock network)
library hold time                       0.060    0.340  (required)
---------------------------------------------------------------
data required time (hold):              0.340
data arrival time:                      0.420

** Before clock uncertainty:  slack = +0.080 ns (MET)
** Hold uncertainty = 0.12 ns applied:
   required time = 0.340 + 0.12 = 0.460

FINAL:
  data required time:    0.460 ns
  data arrival time:     0.420 ns
  slack:                -0.040 ns  ** HOLD VIOLATED **

Root cause: Clock skew between rx_sync_reg[1] and rx_sync_reg[2]
  reg[1] clock arrival: 0.220 ns
  reg[2] clock arrival: 0.280 ns
  Skew: 0.060 ns (reg[2] clock arrives LATER)

  Combined with hold uncertainty (0.12ns), this creates hold
  violation on a simple synchronizer chain.

Fix: Insert delay buffer on data path or balance clock tree
     locally for synchronizer registers.
============================================================
""",
    "path_4_at_risk": """
TIMING PATH 4 — MET BUT AT RISK (clk_io domain)
============================================================
Startpoint:  io_ctrl/cmd_reg[3] (rising FF, clk_io)
Endpoint:    io_ctrl/resp_reg[3] (rising FF, clk_io)
Path Group:  clk_io
Path Type:   max (setup check)

Point                                  Incr     Path
---------------------------------------------------------------
clock clk_io (rise edge)               0.000    0.000
io_ctrl/cmd_reg[3]/CLK                 0.250    0.250
io_ctrl/cmd_reg[3]/Q                   0.310    0.560
io_ctrl/decode/U12/Y                   0.220    0.780
io_ctrl/exec/U34/Y                     0.340    1.120
io_ctrl/mux_out/Y                      0.180    1.300
io_ctrl/resp_reg[3]/D                  0.040    1.340

clock clk_io (rise edge)              10.000   10.000
io_ctrl/resp_reg[3]/CLK                0.270   10.270
library setup time                    -0.090   10.180
clock uncertainty                     -0.15    10.030
---------------------------------------------------------------
slack:                                +0.020 ns  (MET)

** WARNING: Slack is only 20 ps.
   At SS corner with OCV derates (typically 10-15% derate),
   this path WILL FAIL.

   Estimated slack at SS_125C_0v72 with OCV:
     Additional data path pessimism:  ~0.15 ns
     Estimated slack at worst corner: -0.13 ns (FAIL)

   This path is a TICKING BOMB — it passes at nominal but will
   fail at sign-off corners.

   Recommendation: Upsize io_ctrl/exec/U34 (largest delay contributor
   at 0.340 ns = 25% of path delay) or insert pipeline stage.
============================================================
""",
    "path_5_bottleneck": """
TIMING PATH 5 — VIOLATED (clk_core domain)
============================================================
Startpoint:  core/mul/multiplicand_reg[15] (rising FF, clk_core)
Endpoint:    core/mul/product_reg[31] (rising FF, clk_core)
Path Group:  clk_core
Path Type:   max (setup check)

Point                                  Incr     Path
---------------------------------------------------------------
clock clk_core (rise edge)             0.000    0.000
core/mul/multiplicand_reg[15]/CLK      0.180    0.180
core/mul/multiplicand_reg[15]/Q        0.310    0.490
core/mul/U_wallace_tree/pp_gen         0.280    0.770  (partial products)
core/mul/U_wallace_tree/reduce_s1      0.520    1.290  (Wallace stage 1)
core/mul/U_wallace_tree/reduce_s2      0.480    1.770  (Wallace stage 2)
core/mul/U_wallace_tree/reduce_s3      0.440    2.210  (Wallace stage 3)
core/mul/U_final_add/sum[31]           0.620    2.830  (final CPA)
core/mul/product_reg[31]/D             0.050    2.880

clock clk_core (rise edge)             5.000    5.000
core/mul/product_reg[31]/CLK           0.170    5.170
library setup time                    -0.090    5.080
clock uncertainty                     -0.300    4.780
---------------------------------------------------------------
slack:                                -0.280 ns  ** VIOLATED **

Bottleneck analysis:
  U_final_add/sum[31]:    0.620 ns  (43% of combinational delay) **
  U_wallace_tree total:   1.720 ns  (largest block)

  The final carry-propagate adder (CPA) after the Wallace tree
  is a ripple-carry implementation. This is the PRIMARY bottleneck.

  Fix: Replace ripple-carry CPA with carry-lookahead adder (CLA)
       or Kogge-Stone adder. Expected improvement: ~0.35 ns.
       This alone would fix the violation.
============================================================
""",
}

TASK_2_ISSUES: List[Dict[str, Any]] = [
    {
        "id": "T2_SETUP_ALU",
        "issue_type": "setup_violation",
        "location": "clk_core: core/alu path (path 1)",
        "severity": "major",
        "description": "Setup violation of -0.23ns on ALU datapath. 32-bit adder is the bottleneck (0.45ns, 21% of path).",
        "root_cause": "High combinational depth through ALU: 32-bit add + barrel shift + forwarding + hazard logic",
        "recommended_fix": "Consider carry-lookahead adder or pipeline the ALU operation",
        "keywords": ["setup", "violation", "alu", "adder", "bottleneck", "carry", "pipeline", "path 1", "core"],
    },
    {
        "id": "T2_FALSE_PATH",
        "issue_type": "false_path",
        "location": "cross_clk: clk_core->clk_spi through async_fifo (path 2)",
        "severity": "info",
        "description": "Path through async FIFO memory flagged as violated but is a FALSE PATH. CDC handled by gray-code synchronizers.",
        "root_cause": "SDC false_path exception does not cover async_fifo/mem paths — constraint is incomplete",
        "recommended_fix": "Update SDC: set_false_path -through async_fifo/mem*",
        "is_false_path": True,
        "keywords": ["false path", "async", "fifo", "cdc", "cross domain", "clock domain", "gray", "synchron", "sdc", "constraint", "not real", "path 2"],
    },
    {
        "id": "T2_HOLD",
        "issue_type": "hold_violation",
        "location": "clk_io: io_pad/rx_sync_reg chain (path 3)",
        "severity": "major",
        "description": "Hold violation of -0.04ns on synchronizer chain due to clock skew (60ps) combined with hold uncertainty (120ps).",
        "root_cause": "Clock skew between synchronizer registers — reg[2] clock arrives 60ps later than reg[1]",
        "recommended_fix": "Insert delay cell on data path or locally balance clock tree for synchronizer registers",
        "keywords": ["hold", "violation", "skew", "synchron", "delay", "buffer", "balance", "clock tree", "path 3"],
    },
    {
        "id": "T2_AT_RISK",
        "issue_type": "at_risk_path",
        "location": "clk_io: io_ctrl/cmd_reg to resp_reg (path 4)",
        "severity": "major",
        "description": "Path passes with only 20ps slack at nominal. Will FAIL at SS corner with OCV derates (estimated -0.13ns).",
        "root_cause": "Marginal timing — exec/U34 cell contributes 25% of path delay",
        "recommended_fix": "Upsize io_ctrl/exec/U34 or insert pipeline stage before sign-off corners expose the failure",
        "keywords": ["risk", "margin", "20ps", "slim", "ocv", "corner", "ss", "worst case", "fail", "upsize", "path 4", "barely"],
    },
    {
        "id": "T2_MUL_BOTTLENECK",
        "issue_type": "setup_violation",
        "location": "clk_core: multiplier path (path 5)",
        "severity": "critical",
        "description": "Setup violation of -0.28ns on multiplier. Final CPA (ripple-carry) is the bottleneck at 0.62ns (43% of delay).",
        "root_cause": "Ripple-carry adder used as final CPA after Wallace tree — too slow for 200MHz",
        "recommended_fix": "Replace ripple-carry CPA with carry-lookahead (CLA) or Kogge-Stone adder. Expected ~0.35ns improvement.",
        "keywords": ["multiplier", "wallace", "ripple", "carry", "cpa", "bottleneck", "adder", "kogge", "cla", "path 5", "setup", "violation"],
    },
]


# ---------------------------------------------------------------------------
# Task 3 — HARD — Multi-Corner Multi-Mode Sign-off Triage
# ---------------------------------------------------------------------------
TASK_3_OVERVIEW = """
============================================================
  MULTI-CORNER MULTI-MODE SIGN-OFF REPORT
  Design:        pipelined_dsp_core
  Clock domains: clk_core (250 MHz), clk_io (100 MHz), clk_test (25 MHz)
  Corners:       4 PVT corners (see table)
  Modes:         func (functional), scan (DFT scan mode)
  Tool:          PrimeTime MMMC / Tempus MMMC
  Date:          2026-03-28 22:17:44
============================================================

PVT CORNER TIMING SUMMARY
+-----------------+---------+---------+----------+----------+
| Corner          | Temp    | Voltage | WNS(set) | WHS(hld) |
+-----------------+---------+---------+----------+----------+
| SS_125C_0v72    | 125 C   | 0.72V   | -0.45 ns | +0.08 ns |
| SS_m40C_0v72    | -40 C   |  0.72V  | -0.31 ns | +0.11 ns |
| FF_m40C_0v88    | -40 C   |  0.88V  | +0.82 ns | -0.08 ns |
| TT_25C_0v80     |  25 C   |  0.80V  | +0.15 ns | +0.05 ns |
+-----------------+---------+---------+----------+----------+

OCV DERATES APPLIED:
  Setup analysis: data path 1.10x, clock path 0.90x (10% derate)
  Hold analysis:  data path 0.90x, clock path 1.10x

MODE SUMMARY:
  func mode: Primary functional timing — results above
  scan mode: DFT — all paths MET (relaxed constraints at 25 MHz)

OVERALL STATUS: ** NOT READY FOR TAPEOUT **
  - 2 corners have setup violations
  - 1 corner has hold violation
  - See detailed analysis in sections below
============================================================
"""

TASK_3_SECTIONS = {
    "setup_ss_125c": """
SETUP ANALYSIS — SS_125C_0v72 (Worst Setup Corner)
============================================================
This corner represents worst-case slow transistors at high
temperature and low voltage — the standard worst setup corner.

CRITICAL PATH:
  Startpoint:  pipe_s2/acc_reg[23] (rising FF, clk_core)
  Endpoint:    pipe_s3/result_reg[23] (rising FF, clk_core)

  Point                                  Incr     Path
  ---------------------------------------------------------------
  clock clk_core (rise edge)             0.000    0.000
  pipe_s2/acc_reg[23]/CLK                0.320    0.320  (CTS)
  pipe_s2/acc_reg[23]/Q                  0.480    0.800  (slow Vt)
  dsp_mac/multiply[23]                   0.620    1.420  (MAC unit)
  dsp_mac/accumulate[23]                 0.540    1.960  (addition)
  pipe_s2/sat_logic/Y                    0.380    2.340  (saturation)
  pipe_s2/round/Y                        0.290    2.630  (rounding)
  pipe_s3/result_reg[23]/D               0.050    2.680

  clock clk_core (rise edge)             4.000    4.000
  pipe_s3/result_reg[23]/CLK             0.340    4.340
  library setup time                    -0.150    4.190
  clock uncertainty                     -0.100    4.090
  OCV clock pessimism removal (CPPR)    +0.060    4.150
  ---------------------------------------------------------------
  data required:                                  4.150
  data arrival (w/ OCV 1.10x on data):            4.600
  slack:                                 -0.450 ns  ** VIOLATED **

  NOTE: At TT corner, this path has +0.15 ns slack. The SS corner
        adds ~0.60 ns to the data path due to slow transistors.

  Root cause: MAC unit multiply + accumulate takes 1.16 ns at SS.
  Consider: Higher-Vt to Lower-Vt cell swap on critical multiply
            cells, or re-pipeline the MAC across 2 stages.
============================================================
""",
    "hold_ff_m40c": """
HOLD ANALYSIS — FF_m40C_0v88 (Worst Hold Corner)
============================================================
Fast corner at low temperature and high voltage — worst case
for hold timing (fast data, slow clock with OCV hold derate).

VIOLATED PATH:
  Startpoint:  io_buf/din_reg[0] (rising FF, clk_io)
  Endpoint:    io_buf/din_reg[1] (rising FF, clk_io)

  Point                                  Incr     Path
  ---------------------------------------------------------------
  clock clk_io (rise edge)               0.000    0.000
  io_buf/din_reg[0]/CLK                  0.120    0.120  (fast CTS)
  io_buf/din_reg[0]/Q (min delay)        0.100    0.220

  io_buf/din_reg[1]/D                    0.020    0.240  (data arrival)

  clock clk_io (rise edge)               0.000    0.000
  io_buf/din_reg[1]/CLK                  0.150    0.150  (fast CTS)
  OCV clock derate (1.10x on clock)             0.165
  library hold time                      0.050    0.215
  hold uncertainty                       0.105    0.320
  ---------------------------------------------------------------
  data required:                                  0.320
  data arrival (w/ OCV 0.90x on data):            0.218
  slack:                                 -0.080 ns  ** HOLD VIOLATED **

  Root cause: Short data path (single FF-to-FF with no logic)
              combined with clock skew at FF corner.

  Fix options:
    1. Insert 2 delay cells (~80ps each) on data path
    2. Add hold fix buffer (sky130_fd_sc_hd__dlygate4sd3_1)
    3. ECO-level fix — non-blocking for tapeout if identified
============================================================
""",
    "clock_tree_report": """
CLOCK TREE SYNTHESIS REPORT
============================================================
CLOCK DOMAIN: clk_core (250 MHz, period = 4.0 ns)
  Source:            clk_core_pll/CLKOUT
  Sink count:        1,847 flip-flops
  Buffer levels:     8
  Total buffers:     312
  Insertion delay:   1.24 ns
  Skew (worst):      0.180 ns    ** EXCEEDS TARGET 0.100 ns **
  Skew (average):    0.065 ns
  Duty cycle dist:   48.2% / 51.8%  (target: 50% +/- 3%) — OK
  Clock DRC viol:    0

  ** WARNING: Worst skew 0.180 ns exceeds target of 0.100 ns
     Skew contributors:
       pipe_s2/acc_reg group  <-> pipe_s3/result_reg group: 0.180 ns
       This affects the critical setup path at SS corner.
     Recommendation: Rebalance clock tree for pipeline boundary
                     registers. Use useful skew only if intentional.

CLOCK DOMAIN: clk_io (100 MHz, period = 10.0 ns)
  Source:            clk_io_buf/CLKOUT
  Sink count:        234 flip-flops
  Buffer levels:     5
  Total buffers:     48
  Insertion delay:   0.82 ns
  Skew (worst):      0.045 ns    (target: 0.100 ns) — OK
  Duty cycle dist:   49.6% / 50.4% — OK
  Clock DRC viol:    0

CLOCK DOMAIN: clk_test (25 MHz, period = 40.0 ns)
  Source:            clk_test_mux/CLKOUT
  Sink count:        1,847 flip-flops (shared with clk_core via mux)
  Buffer levels:     3
  Total buffers:     24
  Insertion delay:   2.10 ns    ** UNUSUALLY HIGH **
  Skew (worst):      0.032 ns   — OK (relaxed target for scan)
  Duty cycle dist:   49.1% / 50.9% — OK

  ** NOTE on clk_test: This clock is the scan/test mode clock,
     selected via a clock mux from clk_core. The high insertion
     delay (2.10 ns vs 1.24 ns for clk_core) is due to the
     additional mux stage and separate buffer tree. This is
     EXPECTED and ACCEPTABLE for scan mode operation at 25 MHz.
     Timing is met with large margin (WNS = +14.2 ns at 25 MHz).
============================================================
""",
    "drc_summary": """
DRC / PHYSICAL VERIFICATION SUMMARY
============================================================
TOTAL VIOLATIONS: 147

ANTENNA VIOLATIONS: 142
  Layer M4: 52 violations
  Layer M5: 48 violations
  Layer M6: 42 violations
  ** All antenna violations are on layers M4-M6 which is
     standard for a 6-metal-layer process. These are routinely
     fixed by the router's antenna diode insertion engine. **
  ** Classification: WAIVABLE — standard antenna fix in ECO **
  ** Impact on tapeout: NON-BLOCKING **

MINIMUM SPACING VIOLATIONS: 3
  Via spacing M3-M4:     1 violation @ (145.23, 892.10)
  Metal spacing M2:      1 violation @ (567.89, 234.56)
  Metal spacing M5:      1 violation @ (890.12, 456.78)
  ** Classification: MUST-FIX — real DRC errors **

MINIMUM WIDTH VIOLATIONS: 2
  Metal width M3:        1 violation @ (234.56, 678.90)
  Metal width M1:        1 violation @ (123.45, 345.67)
  ** Classification: MUST-FIX — real DRC errors **

DENSITY VIOLATIONS: 0
LVS STATUS: CLEAN (0 errors)
ERC STATUS: CLEAN (0 errors)
============================================================
""",
    "power_analysis": """
POWER ANALYSIS — ALL CORNERS
============================================================
                    SS_125C    FF_m40C    TT_25C
Dynamic power:      198 mW     312 mW     245 mW
  Switching:        142 mW     224 mW     176 mW
  Internal:          56 mW      88 mW      69 mW
Clock network:       38 mW      52 mW      44 mW
Leakage:             49 mW       8 mW      22 mW
-------------------------------------------------------
Total:              285 mW     372 mW     311 mW
Power budget:       250 mW     350 mW     300 mW
Status:          ** OVER **  ** OVER **  ** OVER **

POWER BUDGET EXCEEDED AT ALL CORNERS

Breakdown by hierarchy (TT_25C):
  pipelined_dsp_core (top)    311 mW  (100%)
    +-- pipe_s1               42 mW   (13.5%)
    +-- pipe_s2               67 mW   (21.5%)
    +-- dsp_mac              112 mW   (36.0%)  ** LARGEST CONSUMER **
    +-- pipe_s3               38 mW   (12.2%)
    +-- io_buf                14 mW   (4.5%)
    +-- clock_network         44 mW   (14.1%)
    +-- leakage               22 mW   (7.1%)

** dsp_mac alone consumes 36% of total power.
   Consider: clock gating for idle MAC cycles, operand
   isolation, or power-aware synthesis re-run.

NOTE: Power budget exceedance is 14% at TT — this is a
      BLOCKING issue for tapeout if thermal/package design
      assumed 300 mW max.
============================================================
""",
    "corner_comparison": """
CROSS-CORNER COMPARISON TABLE
============================================================
Parameter              SS_125C   SS_m40C   FF_m40C   TT_25C
---------------------------------------------------------------
WNS (setup) [ns]      -0.450    -0.310    +0.820    +0.150
TNS (setup) [ns]      -1.230    -0.640    +0.000    +0.000
WHS (hold) [ns]       +0.080    +0.110    -0.080    +0.050
Setup violations       4         2         0         0
Hold violations        0         0         1         0
Critical path [ns]     4.600     4.310     3.180     3.850
Clock skew max [ps]    180       175       95        120
Total power [mW]       285       278       372       311
============================================================

OBSERVATIONS:
  1. Setup is worst at SS_125C (expected — slow + hot)
  2. Hold is worst at FF_m40C (expected — fast + cold)
  3. Clock skew is worst at SS corners (slow buffers)
  4. Power is worst at FF_m40C (fast switching + high voltage)
  5. TT corner passes all timing but exceeds power budget
============================================================
""",
}

TASK_3_ISSUES: List[Dict[str, Any]] = [
    {
        "id": "T3_SETUP_SS",
        "issue_type": "setup_violation",
        "location": "SS_125C_0v72: pipe_s2 -> pipe_s3 MAC path",
        "severity": "critical",
        "description": "Worst setup violation of -0.45ns at SS_125C corner. MAC multiply+accumulate is bottleneck (1.16ns).",
        "root_cause": "MAC unit too slow at SS corner. Saturation and rounding add 0.67ns. Clock skew of 180ps between pipeline stages worsens slack.",
        "recommended_fix": "Re-pipeline MAC into 2 stages; swap critical cells to lower Vt; fix clock skew at pipeline boundary",
        "blocking": True,
        "keywords": ["setup", "violation", "ss", "125", "mac", "multiply", "pipeline", "slow", "corner", "worst"],
    },
    {
        "id": "T3_HOLD_FF",
        "issue_type": "hold_violation",
        "location": "FF_m40C_0v88: io_buf/din_reg chain",
        "severity": "major",
        "description": "Hold violation of -0.08ns at FF corner on input synchronizer chain. Short data path with clock skew.",
        "root_cause": "Single FF-to-FF path with no combinational logic. Fast corner + clock skew + OCV derate = hold failure.",
        "recommended_fix": "Insert delay buffer (dlygate4sd3_1) on data path. ECO-level fix.",
        "blocking": False,
        "keywords": ["hold", "violation", "ff", "fast", "corner", "delay", "buffer", "eco", "synchron", "din"],
    },
    {
        "id": "T3_CLOCK_SKEW",
        "issue_type": "clock_tree_issue",
        "location": "clk_core: pipe_s2 <-> pipe_s3 register groups",
        "severity": "critical",
        "description": "Clock skew of 180ps exceeds 100ps target between pipeline stages. Contributes to the worst setup violation.",
        "root_cause": "Unbalanced clock tree at pipeline stage boundary. CTS did not converge to target skew for these register groups.",
        "recommended_fix": "Re-run CTS with tighter skew target for pipeline boundary registers. Consider useful skew allocation.",
        "blocking": True,
        "keywords": ["skew", "clock", "tree", "cts", "180", "100", "target", "exceed", "balance", "pipeline"],
    },
    {
        "id": "T3_DRC_REAL",
        "issue_type": "drc_violation",
        "location": "3 spacing + 2 width violations (M1-M5)",
        "severity": "major",
        "description": "5 real DRC violations: 3 minimum spacing (M2, M3-M4 via, M5) and 2 minimum width (M1, M3). Must be fixed before tapeout.",
        "root_cause": "Routing congestion in localized areas causing minimum geometry violations",
        "recommended_fix": "ECO reroute in affected areas. May need local placement adjustment to reduce congestion.",
        "blocking": False,
        "keywords": ["drc", "spacing", "width", "minimum", "routing", "violation", "must fix", "physical", "5 ", "real"],
    },
    {
        "id": "T3_POWER",
        "issue_type": "power_budget_violation",
        "location": "All corners — worst at FF_m40C (372mW vs 350mW budget)",
        "severity": "critical",
        "description": "Power exceeds budget at ALL corners. TT: 311/300mW (+3.7%), SS: 285/250mW (+14%), FF: 372/350mW (+6.3%). dsp_mac is 36% of total power.",
        "root_cause": "dsp_mac unit is the largest power consumer. Insufficient clock gating and no operand isolation.",
        "recommended_fix": "Add clock gating to MAC for idle cycles; implement operand isolation; re-run power-aware synthesis targeting dsp_mac",
        "blocking": True,
        "keywords": ["power", "budget", "exceed", "over", "watt", "mw", "mac", "clock gating", "leakage", "thermal", "block"],
    },
    {
        "id": "T3_SETUP_SS_M40",
        "issue_type": "setup_violation",
        "location": "SS_m40C_0v72 corner: 2 setup violations, WNS -0.31ns",
        "severity": "major",
        "description": "Additional setup violations at SS_m40C corner (cold slow). WNS -0.31ns, 2 violating paths. Related to same MAC unit timing.",
        "root_cause": "Same fundamental issue as SS_125C but less severe. Fixing the primary MAC timing issue will resolve both corners.",
        "recommended_fix": "Will be resolved by the same fix applied for SS_125C (MAC re-pipeline or cell swaps)",
        "keywords": ["setup", "violation", "ss", "m40", "cold", "second corner", "0.31"],
    },
    {
        "id": "T3_OCV_PATH",
        "issue_type": "ocv_sensitivity",
        "location": "TT_25C: path with +0.15ns slack passes nominal but marginal under OCV",
        "severity": "major",
        "description": "TT corner shows +0.15ns slack but with 10% OCV derate, the margin evaporates. This path may fail with AOCV/POCV analysis which applies path-specific derates.",
        "root_cause": "Path has high combinational depth making it sensitive to OCV derates. Nominal slack insufficient for manufacturing variation.",
        "recommended_fix": "Fix the primary MAC path violations first; this path shares common logic and should improve as a side effect. Run AOCV analysis to confirm.",
        "keywords": ["ocv", "derate", "margin", "variation", "aocv", "pocv", "manufacturing", "tt", "nominal", "sensitive"],
    },
]

# Red herrings — things that LOOK like issues but are NOT
TASK_3_RED_HERRINGS: List[Dict[str, Any]] = [
    {
        "id": "T3_RH_ANTENNA",
        "description": "142 antenna DRC violations on M4-M6",
        "why_not_issue": "Standard for 6-metal-layer process. Routinely fixed by antenna diode insertion in ECO — automated, non-blocking. The number 142 looks alarming but is normal for a design of this size.",
        "keywords": ["antenna", "142", "drc", "m4", "m5", "m6", "diode"],
    },
    {
        "id": "T3_RH_TEST_CLK",
        "description": "clk_test insertion delay is 2.10ns (much higher than clk_core's 1.24ns)",
        "why_not_issue": "clk_test is the scan/DFT mode clock running at only 25 MHz (40ns period). The high insertion delay is expected because it goes through an additional clock mux stage. Timing is met with 14.2ns slack — no issue.",
        "keywords": ["clk_test", "test", "insertion", "delay", "2.1", "high", "scan", "dft"],
    },
]


# ---------------------------------------------------------------------------
# Task 1 Variation A — EASY — Synthesis Review (AES Core)
# ---------------------------------------------------------------------------
TASK_1_VAR_A = {
    "id": "synthesis_review",
    "name": "Synthesis QoR Report Review (AES Core)",
    "difficulty": "easy",
    "description": (
        "Review the post-synthesis Quality-of-Results report for an AES crypto accelerator. "
        "Identify timing violations, area bloat, and design rule violations. Submit your findings."
    ),
    "overview": "Synthesis Report: AES_128_Core\nTarget: TSMC 28nm\nWNS: -3.42ns (severe violation)\nLatches inferred: 4\nMax Capacitance: 12 nets violated",
    "sections": {
        "timing_summary": "WNS -3.42ns. Critical path through S-Box substitution logic involves 32 levels of logic.",
        "design_rule_violations": "12 Max capacitance violations on key_schedule nets. Drive strength insufficient.",
        "unmapped_cells": "4 inferred latches in state machine due to incomplete case statements in RTL."
    },
    "issues": [
        {
            "id": "T1A_TIMING", "issue_type": "timing_violation", "location": "S-Box substitution logic", "severity": "critical",
            "description": "WNS -3.42ns. Critical path through S-Box.", "root_cause": "32 levels of logic", "recommended_fix": "Pipeline S-Box",
            "keywords": ["timing", "wns", "setup", "s-box", "pipeline", "depth"]
        },
        {
            "id": "T1A_DRC", "issue_type": "capacitance_violation", "location": "key_schedule nets", "severity": "major",
            "description": "12 max capacitance violations.", "root_cause": "Drive strength insufficient for high fanout key nets", "recommended_fix": "Buffer tree insertion",
            "keywords": ["capacitance", "fanout", "buffer", "drive", "key"]
        },
        {
            "id": "T1A_LATCH", "issue_type": "unmapped_cells", "location": "state machine", "severity": "critical",
            "description": "4 inferred latches.", "root_cause": "Incomplete case statements in RTL", "recommended_fix": "Add default case to RTL",
            "keywords": ["latch", "inferred", "case", "default", "rtl"]
        }
    ],
    "red_herrings": [],
    "max_steps": 15,
}

# ---------------------------------------------------------------------------
# Task 4 — MEDIUM — Physical Design IR Drop & EM Debug
# ---------------------------------------------------------------------------
TASK_4 = {
    "id": "pd_em_ir_debug",
    "name": "Physical Design: EM/IR & Congestion Debug",
    "difficulty": "medium",
    "description": (
        "Analyze physical design sign-off reports for a GPU shader tile. "
        "Review Dynamic IR drop, Static IR drop, Electromigration (EM), and routing congestion. "
        "Find real issues and propose PD-specific ECO fixes (stripes, decaps, NDR)."
    ),
    "overview": "Volt/Temp: 0.8V, 105C\nDynamic IR Max Drop: 120mV (15%)\nStatic IR Max Drop: 15mV (1.8%)\nEM Violations: 4\nRouting Congestion: Channel 3 at 112%",
    "sections": {
        "dynamic_ir_drop": "Dynamic Voltage Drop (DVD): Max drop 120mV (15% of VDD) observed near MAC clusters. Peak switching current exceeds local power grid capacity.",
        "static_ir_drop": "Static IR Drop: Max drop 15mV (1.8% of VDD). Well within the 5% sign-off limit. Grid is robust for static load.",
        "em_analysis": "Electromigration (EM): 4 signal EM violations on main clk_trunk (M6). Current density exceeds limits at 105C.",
        "routing_congestion": "Congestion Map: Channel 3 shows 112% utilization on M3/M4. Associated with 450 actual DRC shorts in the area."
    },
    "issues": [
        {
            "id": "T4_DYNAMIC_IR", "issue_type": "dynamic_ir_drop", "location": "MAC clusters", "severity": "critical",
            "description": "DVD reaches 120mV (15%) near MACs.", "root_cause": "Peak switching exceeds grid capacity", "recommended_fix": "Add decoupling capacitors (decaps) and local power stripes",
            "keywords": ["dynamic", "ir drop", "dvd", "120mv", "voltage", "decap", "stripe", "mac"]
        },
        {
            "id": "T4_EM", "issue_type": "em_violation", "location": "clk_trunk (M6)", "severity": "major",
            "description": "4 signal EM violations on clock trunk.", "root_cause": "High current density at high frequency/temp", "recommended_fix": "Apply Non-Default Routing (NDR) rules to double wire width",
            "keywords": ["em", "electromigration", "current", "density", "clk_trunk", "trunk", "widen", "ndr", "non-default"]
        },
        {
            "id": "T4_CONGESTION", "issue_type": "routing_congestion", "location": "Channel 3", "severity": "critical",
            "description": "112% routing congestion causing 450 shorts.", "root_cause": "High cell density forcing M3/M4 overutilization", "recommended_fix": "Add partial placement blockage to spread cells out",
            "keywords": ["congestion", "112", "short", "utilization", "placement", "blockage", "spread"]
        }
    ],
    "red_herrings": [
        {
            "id": "T4_RH_STATIC", "description": "Static IR drop of 15mV", "why_not_issue": "Static drop of 1.8% is perfectly acceptable (limit is 5%).", "keywords": ["static", "ir drop", "15mv", "voltag"]
        }
    ],
    "max_steps": 20,
}


import os

# Helper to read real data files
def _read_data_file(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "data", filename)
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"[ERROR] Could not load authentic report: {path}"

# ---------------------------------------------------------------------------
# Task 5 — HARD — Full OpenROAD Authentic Audit
# ---------------------------------------------------------------------------
TASK_5 = {
    "id": "openroad_audit",
    "name": "Authentic OpenROAD/Sky130 Audit",
    "difficulty": "hard",
    "description": (
        "Audit a 100% authentic set of EDA log files from OpenLane/OpenROAD "
        "targeting SkyWater 130nm. You must analyze the Yosys synthesis stat report, "
        "the OpenSTA max path report, and the Magic DRC layout report to find 3 real issues."
    ),
    "overview": "Authentic Open-Source Sign-off Data.\nDevice 1: PicoRV32a (Synthesized & Timed)\nDevice 2: AES128 Core (Physical Verification)\nPDK: sky130A\nToolchain: Yosys 0.20, OpenSTA 2.3.0, Magic 8.3",
    "sections": {
        "yosys_stat": _read_data_file("picorv32a_synthesis.stat.rpt"),
        "opensta_setup": _read_data_file("picorv32a_sta.max.rpt"),
        "magic_drc": _read_data_file("aes_drc.rpt")
    },
    "issues": [
        {
            "id": "T5_YOSYS_LATCH", "issue_type": "unmapped_cells", "location": "cpu_state_q", "severity": "critical",
            "description": "Yosys inferred a latch for cpu_state_q due to missing default assignment.", "root_cause": "Incomplete if-else in Verilog", "recommended_fix": "Add default case to fix latch",
            "keywords": ["latch", "cpu_state_q", "inferred", "default", "assignment", "if-else", "missing"]
        },
        {
            "id": "T5_STA_VIOLATION", "issue_type": "setup_violation", "location": "latched_rdata_reg to reg_out_reg", "severity": "major",
            "description": "OpenSTA setup violation of -2.71ns slack on path to reg_out_reg[23].", "root_cause": "High combinational delay through nor2, a21o, and o21ai logic cells (sky130_fd_sc_hd)", "recommended_fix": "Optimize combinational logic or re-pipeline rdata to reg_out",
            "keywords": ["violation", "setup", "slack", "-2.71", "latched_rdata_reg", "reg_out_reg", "sky130_"]
        },
        {
            "id": "T5_MAGIC_DRC", "issue_type": "drc_violation", "location": "li.1 and m1.6 rules", "severity": "critical",
            "description": "3 Magic DRC errors: local interconnect spacing (li.1) and metal1 minimum area (m1.6).", "root_cause": "Routing congestion crossing M1 boundaries", "recommended_fix": "ECO placement/routing to clear spacing/area rules",
            "keywords": ["drc", "magic", "li.1", "m1.6", "spacing", "area", "interconnect", "metal1", "local"]
        }
    ],
    "red_herrings": [],
    "max_steps": 25,
}

# ---------------------------------------------------------------------------
# Task 6 — HARD — Advanced Verification & Power Sign-off
# ---------------------------------------------------------------------------
TASK_6 = {
    "id": "advanced_signoff",
    "name": "Advanced Verification & Power Sign-off",
    "difficulty": "hard",
    "description": (
        "Perform advanced ASIC sign-off verification using authentic Open-Source logs. "
        "Analyze TritonCTS clock skew, TritonPower consumption breakdowns, and "
        "Yosys EQY formal equivalence proofs to uncover deep architectural and synthesis flaws."
    ),
    "overview": "Advanced Sign-off Package.\nDevice A: Ibex Core (CTS)\nDevice B: Ariane SoC (Power)\nDevice C: AES Crypto (Formal EQY)\nToolchain: OpenROAD, TritonCTS, TritonPower, Yosys EQY 3.14",
    "sections": {
        "clock_tree_cts": _read_data_file("ibex_cts.rpt"),
        "power_analysis": _read_data_file("ariane_power.rpt"),
        "formal_equivalence": _read_data_file("aes_eqy.log")
    },
    "issues": [
        {
            "id": "T6_CTS_SKEW", "issue_type": "clock_tree_issue", "location": "id_stage_i to ex_stage_i", "severity": "major",
            "description": "Clock skew of 255ps exceeds the 100ps target, impacting setup margin between ID and EX stages.", "root_cause": "Tree balancing algorithm terminated early due to placement congestion in region X=[120.5:140.0]", "recommended_fix": "Fix placement congestion and re-run CTS",
            "keywords": ["skew", "255", "clock", "cts", "congestion", "placement", "violated"]
        },
        {
            "id": "T6_POWER_BLOAT", "issue_type": "power_budget_violation", "location": "gen_fpu.i_fpu", "severity": "critical",
            "description": "Total SOC power is OVER BUDGET by 0.1767 W. FPU consumes 43% of total power (0.2651 W).", "root_cause": "FPU lacks clock gating. Clock Gating Efficiency is only 5.9%, causing high switching power", "recommended_fix": "Add architectural RTL clock gating to FPU registers",
            "keywords": ["power", "fpu", "budget", "gating", "switching", "efficiency"]
        },
        {
            "id": "T6_FORMAL_FAIL", "issue_type": "formal_verification_fail", "location": "mix_columns_bypass_sec_q", "severity": "critical",
            "description": "Formal equivalence proof FAIL on mix_columns_bypass_sec_q. RTL specifies secure mode logic but Netlist optimized it away.", "root_cause": "Aggressive Yosys synthesis optimization stripped security logic, disconnecting secure_mode_en", "recommended_fix": "Add (* keep *) attribute in Verilog RTL to secure_mode_en logic",
            "keywords": ["formal", "eqy", "mismatch", "mix_columns", "bypass", "secure", "optimized away", "optimize", "(* keep *)"]
        }
    ],
    "red_herrings": [],
    "max_steps": 25,
}

# ---------------------------------------------------------------------------
# Task Registry
# ---------------------------------------------------------------------------
# Notice how 'synthesis_review' is now a list of cases for data randomization.
# The environment's reset() function will use random.choice() to select one.

TASKS = {
    "synthesis_review": [
        {
            "id": "synthesis_review",
            "name": "Synthesis QoR Report Review",
            "difficulty": "easy",
            "description": (
                "Review the post-synthesis Quality-of-Results report for a UART controller design. "
                "Identify all design issues including timing violations, unmapped cells, and design rule "
                "violations. Submit your findings with severity ratings and recommended fixes."
            ),
            "overview": TASK_1_OVERVIEW,
            "sections": TASK_1_SECTIONS,
            "issues": TASK_1_ISSUES,
            "red_herrings": [],
            "max_steps": 15,
        },
        TASK_1_VAR_A
    ],
    "sta_debug": {
        "id": "sta_debug",
        "name": "STA Timing Path Debug",
        "difficulty": "medium",
        "description": (
            "Debug the Static Timing Analysis report for an SPI master design with 3 clock domains. "
            "Analyze each timing path to determine if violations are real or false paths. Identify "
            "hold violations, at-risk paths with thin margins, and bottleneck cells. 5 issues total."
        ),
        "overview": TASK_2_OVERVIEW,
        "sections": TASK_2_SECTIONS,
        "issues": TASK_2_ISSUES,
        "red_herrings": [],
        "max_steps": 25,
    },
    "pd_em_ir_debug": TASK_4,
    "signoff_triage": {
        "id": "signoff_triage",
        "name": "Multi-Corner Multi-Mode Sign-off Triage",
        "difficulty": "hard",
        "description": (
            "Triage a full sign-off report package for a pipelined DSP core across 4 PVT corners. "
            "Review timing (setup + hold), clock tree quality, DRC violations, and power analysis. "
            "Identify all real issues, separate them from non-issues (waivable DRCs, expected test "
            "clock behavior), classify blocking vs non-blocking, and make a tapeout recommendation. "
            "7 real issues with red herrings."
        ),
        "overview": TASK_3_OVERVIEW,
        "sections": TASK_3_SECTIONS,
        "issues": TASK_3_ISSUES,
        "red_herrings": TASK_3_RED_HERRINGS,
        "max_steps": 35,
    },
    "openroad_audit": TASK_5,
    "advanced_signoff": TASK_6,
}
