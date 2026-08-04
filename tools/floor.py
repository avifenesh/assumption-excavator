# Real floor for 230B MoE, 10B active, on Avi's laptop rig.
# Rig (from memory): laptop RTX 5090 24GB GDDR7, Intel Core Ultra, 60GB RAM.

P_total = 230e9
P_active = 10e9
VRAM = 24.0       # GB
RAM  = 60.0       # GB
budget = VRAM + RAM   # 84 GB, ignoring OS/runtime/KV for now

# --- footprint vs bits/param ---
def gb(params, bits): return params*bits/8/1e9
print("=== FOOTPRINT (params only) ===")
for bits in [16,8,4,3,2.5,2]:
    f = gb(P_total, bits)
    print(f"  {bits:>4} bit -> {f:7.1f} GB   fits 84GB budget? {f<=budget}")

print("\n=== bits/param the FOOTPRINT forces (must be <= budget) ===")
# leave room for KV + activations + OS. assume usable for weights = 84 - 8
usable = budget - 8
max_bits = usable*8/P_total*1e9
print(f"  usable for weights ~{usable} GB -> max {max_bits:.2f} bits/param")
print(f"  => Q2-class MANDATORY (cannot afford Q3={gb(P_total,3):.0f}GB or Q4={gb(P_total,4):.0f}GB)")

# --- per-token DECODE speed at Q2, IF it fit ---
print("\n=== DECODE speed: read active params per token ===")
# bandwidths (laptop-realistic, GB/s)
BW = {"VRAM_GDDR7": 900, "DDR5_dual": 90, "PCIe4_x16_real": 26, "NVMe_gen4": 7}
for bits in [4,2]:
    active_bytes = P_active*bits/8/1e9
    print(f"  active {bits}bit = {active_bytes:.2f} GB/token")
    for name,bw in BW.items():
        t = active_bytes/bw*1000
        print(f"    if served from {name:16} ({bw:4}GB/s): {t:6.1f} ms -> {1000/t:6.1f} tok/s")

# --- WHY 30B runs and 230B doesn't ---
print("\n=== 30B dense Q4 vs 230B MoE: the asymmetry ===")
for (name,P,bits) in [("30B dense Q4",30e9,4),("230B MoE Q4",230e9,4),("230B MoE Q2",230e9,2)]:
    f=gb(P,bits)
    print(f"  {name:16}: {f:6.1f} GB  fits VRAM(24)? {f<=VRAM}  fits budget(84)? {f<=budget}")

print("\n=== THE GAP ===")
print(f"  bits FOOTPRINT allows : {max_bits:.2f}  (Q2-class)")
print(f"  bits QUALITY needs(<5% loss): ~4.0  (Q4 is the usual <2% floor)")
print(f"  GAP = quality needs ~4 bits, footprint allows ~2.6. THIS is the wall.")
