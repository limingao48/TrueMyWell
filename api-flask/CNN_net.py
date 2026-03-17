
# 卷积网络的网络模型定义
import torch
import torch.nn as nn


class CNN_net(nn.Module):
    def __init__(self):
        super(CNN_net, self).__init__()
        self.model1 = nn.Sequential(
            nn.Conv1d(in_channels=1, out_channels=8, kernel_size=3, stride=1, padding=1),
            nn.Tanh(),
            # nn.MaxPool1d(2),  # torch.Size([128, 16, 5])
            nn.Conv1d(in_channels=8, out_channels=16, kernel_size=3, stride=1, padding=1),
            nn.Tanh(),
            # nn.MaxPool1d(2),  # torch.Size([128, 32, 1])
            nn.Flatten(),  # torch.Size([128, 32])    (假如上一步的结果为[128, 32, 2]， 那么铺平之后就是[128, 64])
        )
        self.model2 = nn.Sequential(
            # 如果要更改卷积核大小等，这里全连接层的输入特征数要改变
            # nn.Linear(in_features=96, out_features=100, bias=True),
            nn.Linear(in_features=352, out_features=100, bias=True),
            # 第二个隐含层
            nn.Linear(100, 100),
            # 第三个隐含层
            nn.Linear(100, 50),
            # 回归预测层
            nn.Linear(50, 1)
        )

    def forward(self, input):
        x = input.reshape(-1, 1, 22)
        x = self.model1(x)
        print(x.shape)
        x = self.model2(x)
        return x[:, 0]