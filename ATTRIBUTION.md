# 灵感来源与致谢（Attribution）

本插件的**方法论灵感**来自以下优秀的公开项目与研究，**所有实现代码、检测规则与文案均为原创**，未复制任何第三方的原文案。

| 项目 / 研究 | 作者 / 组织 | 许可 / 性质 | 链接 | 借鉴了什么思路 |
|---|---|---|---|---|
| PRIMM 教学法 | Sue Sentance、Jane Waite、Maria Kallia（Raspberry Pi Foundation 相关研究） | 公开教学研究（论文） | https://www.raspberrypi.org | "预测→运行→探究→改写→创造"五步课堂流程；"先读代码再写代码"的思想。本插件 `lhg-kc-lesson` 的教案骨架受其启发，**教案模板与话术均为原创** |
| Use-Modify-Create | Lee 等（2011） | 公开教学研究（论文） | — | "用→改→创"三阶渐进：先玩现成程序、再小改、最后创造。本插件的单元节奏受其启发 |
| TIPP&SEE | Salac 等（2020） | 公开教学研究（论文） | — | 给低龄学习者探索代码时的元认知脚手架思想；本插件"给脚手架、不给白纸"的创造环节受其启发 |
| Scratch | MIT Media Lab（Lifelong Kindergarten） | 开源项目 | https://scratch.mit.edu | 图形化积木编程的"低门槛、高天花板"理念；本插件积木描述规范参考其积木分类逻辑，**描述文案均为原创** |
| education-agent-skills | GarethManning | 开源（GitHub） | https://github.com/GarethManning/education-agent-skills | "循证教学法 skill 化、teacher-facing 而非 student-facing"的定位思想；本插件"备课助手、不直接面向儿童"的安全定位受其启发 |
| teaching-site-skills | kevintsai1202 | MIT | https://github.com/kevintsai1202/teaching-site-skills | "1 个超级 skill + N 个子 skill"的流水线拆分模式 |

## 声明

1. **借鉴思路，实现与文案均为原创**：以上项目/研究的原文案、代码实现均未被复制。本插件的 skill 方法论文案、类比库、故事示例、审计规则、命令流程均为独立撰写。
2. **许可合规**：上述开源项目均为 MIT / Apache-2.0 等宽松许可，允许在保留声明的前提下进行思路借鉴与二次创作；公开教学研究成果的引用属于思想借鉴，不涉及文本复制。本文件即为保留声明的一部分。
3. **商标与归属**：各项目名称与作者署名归其各自所有者所有。Scratch 是 MIT 的项目，本插件仅为其备课辅助工具，与 MIT 无关联。

## 本插件自身的许可

本插件原创部分采用 MIT 许可（见 `LICENSE` 文件），版权所有：刘洪光（https://github.com/lhg-skills）。
