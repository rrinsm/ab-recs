import numpy as np
from scipy import stats


def sample_size(p, mde, alpha=0.05, power=0.8):
    # mde относительный, 0.05 = +5%
    p2 = p * (1 + mde)
    za = stats.norm.ppf(1 - alpha / 2)
    zb = stats.norm.ppf(power)
    n = (za + zb) ** 2 * (p * (1 - p) + p2 * (1 - p2)) / (p2 - p) ** 2
    return int(np.ceil(n))


def srm(n_a, n_b):
    total = n_a + n_b
    return stats.chisquare([n_a, n_b], [total / 2, total / 2]).pvalue


def ztest_prop(x_a, n_a, x_b, n_b):
    p_a, p_b = x_a / n_a, x_b / n_b
    p = (x_a + x_b) / (n_a + n_b)
    se = np.sqrt(p * (1 - p) * (1 / n_a + 1 / n_b))
    z = (p_b - p_a) / se
    pval = 2 * stats.norm.sf(abs(z))
    return p_a, p_b, z, pval


def bootstrap_diff(a, b, n=2000, seed=0):
    # разница средних b - a, перцентильный интервал
    rng = np.random.default_rng(seed)
    a = np.asarray(a)
    b = np.asarray(b)
    res = np.empty(n)
    for i in range(n):
        res[i] = rng.choice(b, len(b)).mean() - rng.choice(a, len(a)).mean()
    lo, hi = np.percentile(res, [2.5, 97.5])
    return b.mean() - a.mean(), lo, hi, res


def cuped(y, x):
    # theta считаем по всем пользователям сразу, без разбивки на группы
    theta = np.cov(y, x)[0, 1] / np.var(x, ddof=1)
    return y - theta * (x - x.mean())


def holm(pvals):
    pvals = np.asarray(pvals)
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.zeros(m)
    prev = 0
    for k, i in enumerate(order):
        prev = max(prev, (m - k) * pvals[i])
        adj[i] = min(prev, 1.0)
    return adj
