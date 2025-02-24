import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque

# 超参数
BATCH_SIZE = 64
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.99
MEMORY_SIZE = 10000
TARGET_UPDATE = 10
LEARNING_RATE = 0.01

# DQN 神经网络
class DQN(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(state_dim, 128)  # 输入特征数应为 state_dim（80）
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, action_dim)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

# 经验回放缓冲区
class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        # 将状态和下一个状态转换为 numpy 数组
        states = np.array(states, dtype=np.float32)
        next_states = np.array(next_states, dtype=np.float32)
        actions = np.array(actions, dtype=np.int64)
        rewards = np.array(rewards, dtype=np.float32)
        dones = np.array(dones, dtype=np.float32)
        return states, actions, rewards, next_states, dones

    def __len__(self):
        return len(self.buffer)

# DQN 训练器
class DQNTrainer:
    def __init__(self, state_dim, action_dim):
        self.policy_net = DQN(state_dim, action_dim)
        self.target_net = DQN(state_dim, action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=LEARNING_RATE)
        self.memory = ReplayBuffer(MEMORY_SIZE)
        self.epsilon = EPSILON_START
        self.episode = 0  # 新增：记录训练的次数

    def select_action(self, state):
        if random.random() < self.epsilon:
            return random.randint(0, 1)  # 随机动作
        else:
            with torch.no_grad():
                # 将状态转换为张量，并调整形状为 (1, state_dim)
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                q_values = self.policy_net(state_tensor)
                return q_values.argmax().item()  # 选择 Q 值最大的动作

    def update_model(self):
        if len(self.memory) < BATCH_SIZE:
            return

        # 从经验回放中采样
        states, actions, rewards, next_states, dones = self.memory.sample(BATCH_SIZE)

        # 将 numpy 数组转换为张量
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)

        # 计算当前 Q 值
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1))

        # 计算目标 Q 值
        next_q_values = self.target_net(next_states).max(1)[0].detach()
        target_q_values = rewards + (1 - dones) * GAMMA * next_q_values

        # 计算损失
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)

        # 更新模型
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 更新 epsilon
        self.epsilon = max(EPSILON_END, self.epsilon * EPSILON_DECAY)

    def update_target_net(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def save_model(self, path):
        checkpoint = {
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'episode': self.episode
        }
        torch.save(checkpoint, path)

    def load_model(self, path):
        try:
            checkpoint = torch.load(path)
            self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
            self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.epsilon = checkpoint['epsilon']
            self.episode = checkpoint['episode']
            self.target_net.eval()
            print("模型加载成功。")
        except (FileNotFoundError, RuntimeError) as e:
            print(f"加载模型时出现错误: {e}，将从头开始训练。")