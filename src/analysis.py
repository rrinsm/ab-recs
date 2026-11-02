# основной разбор теста
# python src/generate_data.py && python src/analysis.py

import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from stats_utils import bootstrap_diff, cuped, holm, sample_size, srm, ztest_prop

users = pd.read_csv("data/users.csv")
act = pd.read_csv("data/activity.csv")

con = sqlite3.connect(":memory:")
users.to_sql("users", con, index=False)
act.to_sql("activity", con, index=False)

queries = open("sql/metrics.sql").read().split(";")
by_group = pd.read_sql(queries[0], con)
df = pd.read_sql(queries[1], con)
print(by_group.to_string(index=False))
print()

# ---------- дизайн
# базовый ctr берем из периода до теста
base = df["clicked_pre"].mean()
print(f"ctr до теста: {base:.4f}")
for mde in [0.05, 0.03]:
    print(f"  mde {mde:.0%}: нужно {sample_size(base, mde):,} на группу")

n_c = (df.grp == "control").sum()
n_t = (df.grp == "test").sum()
print(f"\nsrm: control {n_c}, test {n_t}, p = {srm(n_c, n_t):.3f}")

c = df[df.grp == "control"]
t = df[df.grp == "test"]

# ---------- основная метрика
p_c, p_t, z, p = ztest_prop(c.clicked.sum(), len(c), t.clicked.sum(), len(t))
print(f"\nctr: {p_c:.4f} -> {p_t:.4f}, uplift {p_t / p_c - 1:+.1%}, z = {z:.2f}, p = {p:.2g}")

# ---------- сессии
w = stats.ttest_ind(t.sessions, c.sessions, equal_var=False)
diff, lo, hi, boot = bootstrap_diff(c.sessions.values, t.sessions.values)
print(f"\nсессии: {c.sessions.mean():.3f} -> {t.sessions.mean():.3f} ({t.sessions.mean() / c.sessions.mean() - 1:+.2%})")
print(f"  welch p = {w.pvalue:.3g}")
print(f"  bootstrap: diff {diff:.3f}, 95% ci [{lo:.3f}; {hi:.3f}]")

# cuped на сессиях, ковариата = сессии за 2 недели до теста
df["sessions_cuped"] = cuped(df.sessions.values.astype(float), df.sessions_pre.values.astype(float))
var_before = df.sessions.var()
var_after = df.sessions_cuped.var()
print(f"\ncuped: дисперсия {var_before:.1f} -> {var_after:.1f} (-{1 - var_after / var_before:.0%})")
c2 = df[df.grp == "control"]
t2 = df[df.grp == "test"]
w2 = stats.ttest_ind(t2.sessions_cuped, c2.sessions_cuped, equal_var=False)
print(f"  welch после cuped p = {w2.pvalue:.3g}")
# во сколько раз меньше нужна выборка при той же мощности
print(f"  та же мощность на выборке в {var_before / var_after:.1f} раза меньше")

# ---------- вторичные метрики + поправка
_, _, _, p_buy = ztest_prop(c.bought.sum(), len(c), t.bought.sum(), len(t))
pvals = {"ctr": p, "sessions": w.pvalue, "buy_rate": p_buy}
adj = holm(list(pvals.values()))
print("\nholm:")
for (k, v), a in zip(pvals.items(), adj):
    print(f"  {k:<9} p = {v:.3g}  p_holm = {a:.3g}")

# guardrail: время загрузки не должно вырасти
g = stats.ttest_ind(t.load_ms, c.load_ms, equal_var=False)
print(f"\nguardrail load_ms: {c.load_ms.mean():.1f} -> {t.load_ms.mean():.1f}, p = {g.pvalue:.2f}")

# по платформам интересно глянуть, но это не основной вывод
for plat, part in df.groupby("platform"):
    pc = part[part.grp == "control"].clicked.mean()
    pt = part[part.grp == "test"].clicked.mean()
    print(f"  {plat}: ctr {pc:.4f} -> {pt:.4f} ({pt / pc - 1:+.1%})")

# ---------- графики
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].bar(["control", "test"], [p_c, p_t], color=["#9aa5b1", "#2a6fdb"])
err = [1.96 * np.sqrt(x * (1 - x) / n) for x, n in [(p_c, len(c)), (p_t, len(t))]]
ax[0].errorbar(["control", "test"], [p_c, p_t], yerr=err, fmt="none", color="black", capsize=5)
ax[0].set_ylim(0.2, 0.32)
ax[0].set_title("ctr блока рекомендаций, 95% ci")
ax[1].hist(boot, bins=40, color="#2a6fdb")
ax[1].axvline(0, color="black")
ax[1].set_title("bootstrap: разница сессий на пользователя")
plt.tight_layout()
plt.savefig("figures/ab_result.png", dpi=110)

fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(df.sessions, bins=60, alpha=0.6, label="sessions", color="#9aa5b1")
ax.hist(df.sessions_cuped, bins=60, alpha=0.6, label="sessions cuped", color="#2a6fdb")
ax.legend()
ax.set_title("cuped сужает распределение")
plt.tight_layout()
plt.savefig("figures/cuped.png", dpi=110)
