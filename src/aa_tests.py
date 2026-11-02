# проверка что z-тест не врет: 500 раз делим контроль пополам и смотрим,
# как часто находим "эффект", которого нет. должно быть около 5%
# python src/aa_tests.py  (минуту-две)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from stats_utils import ztest_prop

N_TESTS = 500
ALPHA = 0.05

users = pd.read_csv("data/users.csv")
act = pd.read_csv("data/activity.csv")
df = act[act.period == "test"].merge(users, on="user_id")
ctrl = df[df.grp == "control"].rec_clicked.values

rng = np.random.default_rng(11)
pvals = []
for i in range(N_TESTS):
    mask = rng.random(len(ctrl)) < 0.5
    a, b = ctrl[mask], ctrl[~mask]
    pvals.append(ztest_prop(a.sum(), len(a), b.sum(), len(b))[3])
pvals = np.array(pvals)

fpr = (pvals < ALPHA).mean()
print(f"a/a: {N_TESTS} тестов, ложных срабатываний {fpr:.1%} при alpha {ALPHA:.0%}")
# 95% интервал для доли при честных 5%
se = np.sqrt(ALPHA * (1 - ALPHA) / N_TESTS)
print(f"ожидаемо {ALPHA - 1.96 * se:.1%} - {ALPHA + 1.96 * se:.1%}")

plt.hist(pvals, bins=20, color="#2a6fdb", edgecolor="white")
plt.axhline(N_TESTS / 20, color="black", ls="--")
plt.title("p-value в a/a тестах (должно быть равномерно)")
plt.savefig("figures/aa_pvalues.png", dpi=110)
