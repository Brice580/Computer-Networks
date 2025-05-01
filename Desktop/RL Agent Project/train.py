

from env.trading_env import create_trading_env
from models.dqn_agent import DQNAgent
import matplotlib.pyplot as plt

def main():
    env = create_trading_env("data/AAPL.csv")

    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    agent = DQNAgent(state_dim, action_dim)

    num_episodes = 100
    net_worths = []

    for episode in range(num_episodes):
        state, info = env.reset()
        total_reward = 0
        done = False
        truncated = False

        while not done and not truncated:
            action = agent.select_action(state)
            next_state, reward, done, truncated, info = env.step(action)

            agent.buffer.push(state, action, reward, next_state, done)
            agent.train()

            state = next_state
            total_reward += reward
            net_worths.append(info['portfolio_valuation'])

        agent.update_target()
        print(f"Episode {episode+1}: Total Reward = {total_reward:.2f} | Net Worth = ${info['portfolio_valuation']:.2f}")

    # Plot net worth
    plt.plot(net_worths)
    plt.xlabel("Timesteps")
    plt.ylabel("Net Worth")
    plt.title("Agent Portfolio Value")
    plt.show()

if __name__ == "__main__":
    main()
