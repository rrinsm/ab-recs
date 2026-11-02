# генерим пользователей приложения оператора и их активность до и во время теста
# эффекты заложены специально, чтобы потом проверить, находят ли их методы:
#   ctr блока рекомендаций +12% в тесте
#   сессии +1.5%
#   покупки услуг и время загрузки экрана без изменений
# запуск: python src/generate_data.py  (создаст data/users.csv и data/activity.csv)

import os
import numpy as np
import pandas as pd

N = 200_000
SEED = 88
DAYS = 14

rng = np.random.default_rng(SEED)
os.makedirs("data", exist_ok=True)

users = pd.DataFrame({
    "user_id": np.arange(1, N + 1),
    "grp": rng.choice(["control", "test"], N),
    "platform": rng.choice(["android", "ios"], N, p=[0.68, 0.32]),
    "region": rng.choice(["msk", "spb", "regions"], N, p=[0.3, 0.12, 0.58]),
    "tariff": rng.choice(["basic", "smart", "premium"], N, p=[0.5, 0.38, 0.12]),
})
is_test = (users["grp"] == "test").values

# активность у всех разная, и она устойчивая во времени, поэтому cuped будет работать
activity = rng.lognormal(np.log(0.9), 0.59, N)  # сессий в день
sess_pre = rng.poisson(activity * DAYS)
sess_test = rng.poisson(activity * DAYS * np.where(is_test, 1.015, 1.0))

# склонность кликать по рекомендациям, ~25.75% в среднем
click_p = np.clip(rng.beta(2.6, 7.5, N), 0, 1)
clicked_pre = rng.random(N) < click_p
clicked_test = rng.random(N) < np.clip(click_p * np.where(is_test, 1.12, 1.0), 0, 1)

impr_pre = rng.poisson(sess_pre * 0.6)
impr_test = rng.poisson(sess_test * 0.6)

bought_pre = rng.random(N) < 0.031
bought_test = rng.random(N) < 0.031

load_ms = rng.lognormal(np.log(820), 0.25, N).round()

act = pd.concat([
    pd.DataFrame({"user_id": users.user_id, "period": "pre", "sessions": sess_pre,
                  "rec_impressions": impr_pre, "rec_clicked": clicked_pre.astype(int),
                  "bought_service": bought_pre.astype(int),
                  "load_ms": rng.lognormal(np.log(820), 0.25, N).round()}),
    pd.DataFrame({"user_id": users.user_id, "period": "test", "sessions": sess_test,
                  "rec_impressions": impr_test, "rec_clicked": clicked_test.astype(int),
                  "bought_service": bought_test.astype(int), "load_ms": load_ms}),
])

users.to_csv("data/users.csv", index=False)
act.to_csv("data/activity.csv", index=False)
print("users:", len(users), " activity rows:", len(act))
