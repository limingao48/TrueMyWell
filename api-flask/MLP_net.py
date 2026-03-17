# 定义多层感知机
import torch
import torch.nn as nn

class MLP_net(torch.nn.Module):
    def __init__(self):
        super(MLP_net, self).__init__()
        # 第一个隐含层
        self.hidden1 = nn.Linear(in_features=22, out_features=100, bias=True)
        # 第二个隐含层
        self.hidden2 = nn.Linear(100, 100)
        # 第三个隐含层
        self.hidden3 = nn.Linear(100, 50)
        # 回归预测层
        self.predict = nn.Linear(50, 1)

        # 定义网络前向传播路径
    def forward(self, x):
        #使用tanh函数作为隐含层之间的非线性激活函数
        x = torch.tanh(self.hidden1(x))
        x = torch.tanh(self.hidden2(x))
        x = torch.tanh(self.hidden3(x))
        output = self.predict(x)
        # 输出一个一维向量
        # return output[:, 0:1]
        return output