# Transformer 训练汇总（100 Epoch）

## 1. 运行背景
- 项目：Chemical_AI_Project
- 训练脚本：train.py
- 运行环境：Python venv（Windows）
- 最近成功任务：`--epochs 100 --early-stop-patience 1000 --max-rows 5000 --curve-path logs/figure2_loss_accuracy_100ep_fast.png`

## 2. 数据规模（本次实际运行）
本次成功训练使用了 `max-rows=5000`，因此是全流程训练但在读取阶段截取前 5000 行。

- 原始读取行数：5000
- 时序窗口长度（look_back）：20
- 训练样本数（train_size）：3502
- 验证样本数（val_size）：731
- 窗口总样本数：4233
- 特征维度（feature_count）：15
- 类别数（class_count）：4

## 3. 训练参数
### 3.1 本次命令参数（实际生效）
- epochs：100
- early-stop-patience：1000
- max-rows：5000
- curve-path：logs/figure2_loss_accuracy_100ep_fast.png

### 3.2 模型与优化默认参数（代码默认）
- batch_size：128
- lr：3e-4
- weight_decay：1e-3
- train_ratio：0.7
- val_ratio：0.15
- d_model：32
- nhead：2
- num_layers：1
- dropout：0.4
- dim_feedforward：64
- grad_clip：1.0
- ema_decay：0.999
- augment_noise_std：0.01
- augment_feature_dropout：0.03

## 4. 学习率衰减策略
本项目已启用学习率衰减（ReduceLROnPlateau）：

- mode：min
- factor：0.5
- patience：2
- min_lr：1e-6

说明：验证损失在若干 epoch 无改善时，学习率按 0.5 递减；本次训练中学习率从 `3.00e-04` 逐步降低至 `1.00e-06`。

## 5. 训练结果摘要
- 最终轮次：Epoch 100
- FINAL_BEST_VAL_LOSS：1.235932
- 最高验证准确率（Val Acc）：0.5103（Epoch 79）
- Epoch 100 指标：
  - Train Loss：0.8022
  - Val Loss：1.2359
  - Train Acc：0.6733
  - Val Acc：0.5034

## 6. 产物与日志
- 训练日志：logs/train_log_20260413_191822.txt
- 曲线图：logs/figure2_loss_accuracy_100ep_fast.png
- 最终模型：models/best_overfit_fixed.pth

## 7. 备注
- 全量数据版本（不加 `max-rows`）在当前机器上耗时较高，曾出现中断/失败（退出码 1）。
- 如需正式发布版结果，建议再执行一次全量 100 epoch，并与本次 fast 版本做对比报告。
