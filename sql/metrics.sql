-- метрики по группам за период теста
-- ctr тут пользовательский: доля тех, кто хоть раз кликнул по блоку рекомендаций

select
    u.grp,
    count(*)                                   as users,
    sum(a.rec_clicked)                         as clicked_users,
    round(avg(a.rec_clicked), 4)               as ctr,
    round(avg(a.sessions), 3)                  as sessions_per_user,
    round(avg(a.bought_service), 4)            as buy_rate,
    round(avg(a.load_ms), 1)                   as avg_load_ms,
    -- считаем и классический ctr по показам, просто для сравнения
    round(1.0 * sum(a.rec_clicked) / nullif(sum(a.rec_impressions), 0), 4) as clicks_per_impr
from users u
join activity a
  on a.user_id = u.user_id
 and a.period = 'test'
group by u.grp
order by u.grp;


-- по пользователю: метрика в тесте + то же самое до теста (для cuped)
select
    u.user_id,
    u.grp,
    u.platform,
    max(case when a.period = 'test' then a.sessions end)    as sessions,
    max(case when a.period = 'pre'  then a.sessions end)    as sessions_pre,
    max(case when a.period = 'test' then a.rec_clicked end) as clicked,
    max(case when a.period = 'pre'  then a.rec_clicked end) as clicked_pre,
    max(case when a.period = 'test' then a.bought_service end) as bought,
    max(case when a.period = 'test' then a.load_ms end)     as load_ms
from users u
join activity a on a.user_id = u.user_id
group by u.user_id, u.grp, u.platform;
