import torch
import torch.nn as nn


# ---------------------- LSTM模型（适配TE时序数据） ----------------------
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size=128, num_layers=2, output_size=1, dropout=0.2):
        """
        input_size: 特征工程后特征维度（train_final.csv列数-1）
        hidden_size: LSTM隐藏层维度
        num_layers: LSTM层数
        output_size: 输出维度（二分类设为1，多分类设为类别数）
        """
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM层
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,  # 输入形状: (batch_size, seq_len, input_size)
            dropout=dropout if num_layers > 1 else 0
        )

        # 全连接输出层
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, output_size)
        )

    def forward(self, x):
        # 初始化隐藏状态
        batch_size = x.size(0)
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(x.device)

        # LSTM前向传播
        out, _ = self.lstm(x, (h0, c0))
        # 取最后一个时间步的输出
        out = out[:, -1, :]
        # 全连接层输出
        out = self.fc(out)
        return out


# ---------------------- Transformer模型（可选，长序列效果更好） ----------------------
class PositionalEncoding(nn.Module):
    """位置编码，Transformer专用"""

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
        d_model必须是nhead的倍数（如128/4=32）
        """
        super(TransformerModel, self).__init__()
        self.d_model = d_model

        # 输入投影层
        self.embedding = nn.Linear(input_size, d_model)
        # 位置编码
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        # Transformer编码器
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dim_feedforward=256, dropout=dropout)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        # 全连接输出层
        self.fc = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, output_size)
        )

    def forward(self, x):
        # x形状: (batch_size, seq_len, input_size)
        x = self.embedding(x) * torch.sqrt(torch.tensor(self.d_model, dtype=torch.float32))
        x = self.pos_encoder(x)
        # Transformer输入需要(seq_len, batch_size, d_model)，转置
        x = x.transpose(0, 1)
        x = self.transformer_encoder(x)
        # 取最后一个时间步输出
        x = x[-1, :, :]
        x = self.fc(x)
        return x


# ---------------------- 模型测试（运行脚本验证） ----------------------
if __name__ == "__main__":
    # 模拟输入: batch_size=32, seq_len=5, input_size=52（TE原始特征数+窗口特征）
    input_size = 52 * 6  # 原始52个特征 + 5个窗口特征，可根据实际调整
    lstm_model = LSTMModel(input_size=input_size)
    transformer_model = TransformerModel(input_size=input_size)

    # 测试前向传播
    dummy_input = torch.randn(32, 5, input_size)
    lstm_out = lstm_model(dummy_input)
    trans_out = transformer_model(dummy_input)

    print(f"✅ LSTM模型测试通过，输出形状: {lstm_out.shape}")
    print(f"✅ Transformer模型测试通过，输出形状: {trans_out.shape}")
