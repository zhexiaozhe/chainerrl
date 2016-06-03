import unittest

import chainer
from chainer import cuda
from chainer import optimizers
import numpy as np

import q_function
import random_seed
from envs.simple_abc import ABC


class _TestDQNLike(unittest.TestCase):

    def setUp(self):
        pass

    def make_agent(self, gpu, q_func, opt):
        raise NotImplementedError

    def _test_abc(self, gpu):

        random_seed.set_random_seed(0)

        q_func = q_function.FCSIQFunction(1, 3, 10, 2)

        opt = optimizers.RMSpropGraves(
            lr=1e-3, alpha=0.95, momentum=0.95, eps=1e-4)
        opt.setup(q_func)

        agent = self.make_agent(gpu, q_func, opt)

        env = ABC()

        total_r = 0
        episode_r = 0

        # Train
        for i in range(5000):
            episode_r += env.reward
            total_r += env.reward

            action = agent.act(env.state, env.reward, env.is_terminal)

            if env.is_terminal:
                print(('i:{} epsilon:{} episode_r:{}'.format(
                    i, agent.epsilon, episode_r)))
                episode_r = 0
                env.initialize()
            else:
                env.receive_action(action)

        # Test
        agent.epsilon = 0.0
        env.initialize()
        total_r = env.reward
        while not env.is_terminal:
            s = np.expand_dims(env.state, 0)
            if gpu >= 0:
                s = cuda.to_gpu(s, device=gpu)
            action = q_func(chainer.Variable(s)).greedy_actions.data[0]
            env.receive_action(action)
            total_r += env.reward
        self.assertAlmostEqual(total_r, 1)

    def test_abc_gpu(self):
        self._test_abc(0)

    def test_abc_cpu(self):
        self._test_abc(-1)