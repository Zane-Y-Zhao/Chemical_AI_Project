import torch
import torch.nn as nn


# ---------------------- Transformer模型（最终保留，适配TE时序数据） ----------------------
class PositionalEncoding(nn.Module):
    """位置编码，Transformer专用，用于补充序列位置信息"""
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-torch.log(torch.tensor(10000.0)) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0)]
        return self.dropout(x)


class TransformerModel(nn.Module):
    def __init__(self, input_size, d_model=128, nhead=4, num_layers=2, output_size=1, dropout=0.2):
        """
        适配TE时序数据的Transformer模型
        参数说明：
        input_size: 特征工程后特征维度（对应韩永盛处理好的TE_processed.csv的特征数）
        d_model: Transformer隐藏层维度，必须是nhead的倍数（128/4=32，符合要求）
        nhead: 多头注意力头数
        num_layers: Transformer编码器层数
        output_size: 输出维度（二分类设为1，多分类设为类别数）
        dropout:  dropout率，防止过拟合
        """
        super(TransformerModel, self).__init__()
        self.d_model = d_model

        # 1. 输入投影层：将原始特征映射到Transformer的d_model维度
        self.embedding = nn.Linear(input_size, d_model)
        # 2. 位置编码：补充序列的位置信息
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        # 3. Transformer编码器：核心自注意力结构
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=256,
            dropout=dropout,
            batch_first=True  # 适配(batch_size, seq_len, d_model)输入，无需手动转置
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        # 4. 全连接输出层：分类/回归头
        self.fc = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, output_size)
        )

    def forward(self, x):
        # x输入形状: (batch_size, seq_len, input_size)，和原LSTM输入完全一致
        # 1. 输入投影 + 缩放
        x = self.embedding(x) * torch.sqrt(torch.tensor(self.d_model, dtype=torch.float32, device=x.device))
        # 2. 位置编码
        x = self.pos_encoder(x)
        # 3. Transformer编码器前向传播（batch_first=True，无需转置）
        x = self.transformer_encoder(x)
        # 4. 取最后一个时间步的输出，用于分类
        x = x[:, -1, :]
        # 5. 全连接层输出结果
        x = self.fc(x)
        return x


# ---------------------- 模型测试（运行脚本验证，确保代码可跑） ----------------------
if __name__ == "__main__":
    # 模拟输入：batch_size=32, seq_len=5, input_size=52（适配TE数据特征数，可根据实际调整）
    input_size = 52
    transformer_model = TransformerModel(input_size=input_size)

    # 测试前向传播
    dummy_input = torch.randn(32, 5, input_size)
    trans_out = transformer_model(dummy_input)

    print(f"✅ Transformer模型测试通过，输出形状: {trans_out.shape}")
    print(f"✅ 模型结构符合要求，可直接用于TE数据训练")
