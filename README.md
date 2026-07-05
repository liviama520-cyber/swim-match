# SwimMatch · Beta

输入游泳比赛成绩(长池米 / 短池米 / 短码),对比 2026 级美国大学新生的真实招募水平,输出 Safety / Match / Reach 分档报告。

- **数据**:SwimSwam 2026 届招募数据库 + SwimCloud 公开成绩的**聚合统计**(33 校 / 355 名新生),站点不含任何选手个人信息。
- **算法**:SwimCloud 同口径积分(1000 分 = 世界纪录)做跨泳池、跨项目统一标尺;积分基准由数据反推(距离项目基准 = 世界纪录,验证吻合)。
- **刷新数据**:更新 `swim-coach/public/recruits-2026.json` 后运行 `python3 build_stats.py` 重新生成 `stats.json`。

## 招募重点预测(2026-07-05 新增)

按泳姿×年级推算 2027–2030 年各校每届的招募空缺:某届高中生入学时,恰好要填补当年毕业主力留下的泳姿空缺。

- **数据源**:2026 NCAA D1 锦标赛(男/女)、2026 藤校联赛(男/女)、2026 NCAA D3 锦标赛 psych sheet — 选手年级(FR/SO/JR/SR)×参赛项目;2030 届由该校 2026 级新生构成推算。
- **模型**:每名主力按参赛项目均摊 1.0 权重到 7 个泳姿组(短/中/长距自由、仰、蛙、蝶、混);JR→2027 届空缺、SO→2028、FR→2029、2026 级新生→2030。`build_needs.py` 生成 `needs.json`。
- **合规**:原始成绩文件在 `meets/`(**不入库**,含选手姓名),站点只发布聚合的 `needs.json`。
- **刷新数据**(新赛季,如 2027 年 4 月用 2027 锦标赛结果):
  ```bash
  python3 scrape_hytek.py "https://swimmeetresults.tech/NCAA-Division-I-Men-2027/" M meets/ncaa-d1-men-2027.json
  python3 scrape_hytek.py "https://swimmeetresults.tech/NCAA-Division-I-Women-2027/" W meets/ncaa-d1-women-2027.json
  # 藤校: besmarttinc/sidearmstats 的 Hy-Tek RTR 页同样用 scrape_hytek.py
  # D3: 下载 NCAA psych sheet PDF 后 python3 parse_d3_psych.py <pdf> meets/ncaa-d3-2027.json
  python3 build_needs.py meets/*.json needs.json   # 注意先更新脚本内 GRAD 年级→毕业年映射
  ```

免费公测中;付费版(完整报告解锁)待需求验证后接入。
