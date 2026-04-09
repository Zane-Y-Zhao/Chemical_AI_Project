def test_model_inference():
    """测试模型推理稳定性"""
    data_path = r"D:\TE_Project1\data"
    model_dir = r"D:\TE_Project1\models"
    train_df = pd.read_csv(os.path.join(data_path, "train_final.csv"))
    input_size = len(train_df.columns[:-1])

    # 自动获取最新的模型文件
    model_files = [f for f in os.listdir(model_dir) if f.startswith("best_model") and f.endswith(".pth")]
    if not model_files:
        raise FileNotFoundError("未找到模型文件，请先运行train.py训练模型")
    latest_model = max(model_files, key=lambda x: os.path.getmtime(os.path.join(model_dir, x)))
    model_path = os.path.join(model_dir, latest_model)

    model = LSTMModel(input_size=input_size, hidden_size=128, num_layers=2, output_size=2)
    model.load_state_dict(torch.load(model_path))
    model.eval()

    for _ in range(10):
        test_input = torch.randn(1, 5, input_size)
        with torch.no_grad():
            output = model(test_input)
        assert output.shape == (1, 2), "推理输出形状错误"
    print("✅ 模型推理稳定性测试通过")
