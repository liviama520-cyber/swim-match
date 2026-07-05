# SwimMatch · Beta

输入游泳比赛成绩(长池米 / 短池米 / 短码),对比 2026 级美国大学新生的真实招募水平,输出 Safety / Match / Reach 分档报告。

- **数据**:SwimSwam 2026 届招募数据库 + SwimCloud 公开成绩的**聚合统计**(33 校 / 355 名新生),站点不含任何选手个人信息。
- **算法**:SwimCloud 同口径积分(1000 分 = 世界纪录)做跨泳池、跨项目统一标尺;积分基准由数据反推(距离项目基准 = 世界纪录,验证吻合)。
- **刷新数据**:更新 `swim-coach/public/recruits-2026.json` 后运行 `python3 build_stats.py` 重新生成 `stats.json`。

免费公测中;付费版(完整报告解锁)待需求验证后接入。
