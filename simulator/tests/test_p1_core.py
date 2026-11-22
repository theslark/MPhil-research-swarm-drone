"""P1 core tests: oracle exit criterion (a), conflict-freedom, determinism, physical invariants."""
import os
import unittest

from uavsim.comms import FullConnectivity
from uavsim.config import load_config, SimConfig
from uavsim.metrics import Recorder
from uavsim.sim import run
from uavsim.world import World, Mode

HERE = os.path.dirname(os.path.abspath(__file__))
S1 = os.path.join(HERE, "..", "scenarios", "s1_normal.toml")
SEEDS = range(2001, 2011)          # 10 seeds keep the unit tests fast; the exit-check script uses 30


class OracleExitCriterion(unittest.TestCase):
    def test_oracle_completes_everything_without_faults(self):
        for seed in SEEDS:
            m = run(load_config(S1, seed=seed), "oracle")
            self.assertEqual(m["mcr"], 1.0, f"seed {seed}")
            self.assertIsNotNone(m["t_mc"])
            self.assertLessEqual(m["t_mc"], 1800.0)

    def test_no_duplicate_or_wasted_work_without_faults(self):
        for method in ("oracle", "greedy"):
            for seed in list(SEEDS)[:3]:
                m = run(load_config(S1, seed=seed), method)
                self.assertAlmostEqual(m["dwr"], 0.0, places=12, msg=f"{method} {seed}")
                self.assertAlmostEqual(m["wdr"], 0.0, places=12, msg=f"{method} {seed}")


class Determinism(unittest.TestCase):
    def test_same_seed_same_outcome(self):
        for method in ("oracle", "greedy"):
            a = run(load_config(S1, seed=2001), method)
            b = run(load_config(S1, seed=2001), method)
            self.assertEqual(a["result_hash"], b["result_hash"], method)

    def test_different_seed_different_world(self):
        a = run(load_config(S1, seed=2001), "greedy")
        b = run(load_config(S1, seed=2002), "greedy")
        self.assertNotEqual(a["result_hash"], b["result_hash"])


class Invariants(unittest.TestCase):
    def _run_world(self, seed, method="oracle"):
        from uavsim.allocators import make_allocator
        cfg = load_config(S1, seed=seed)
        rec = Recorder()
        w = World(cfg, recorder=rec)
        a = make_allocator(method)
        a.plan(w)
        while not w.finished():
            w.step(a.decide)
        return w, rec

    def test_energy_never_negative_and_equals_airborne_time(self):
        for method in ("oracle", "greedy"):
            w, rec = self._run_world(2003, method)
            for d in w.drones:
                self.assertGreaterEqual(d.energy, -1e-9)
                self.assertAlmostEqual(w.cfg.energy - d.energy, rec.energy[d.id], places=6)
                if d.mode == Mode.LANDED:
                    self.assertAlmostEqual(rec.land_time[d.id], rec.energy[d.id], places=6)

    def test_landed_drones_are_at_base(self):
        w, _ = self._run_world(2004)
        for d in w.drones:
            if d.mode == Mode.LANDED:
                self.assertAlmostEqual(d.x, w.cfg.base_x, places=6)
                self.assertAlmostEqual(d.y, w.cfg.base_y, places=6)

    def test_each_completed_task_serviced_only_by_completer(self):
        w, rec = self._run_world(2005)
        for t in w.tasks:
            servers = {i for (i, k), h in rec.service.items() if k == t.id and h > 0}
            self.assertEqual(servers, {t.completer})
            self.assertAlmostEqual(rec.service[(t.completer, t.id)], t.service, places=6)

    def test_task_generation_matches_step6(self):
        cfg = load_config(S1, seed=2001)
        w = World(cfg)
        self.assertEqual(len(w.tasks), 30)
        self.assertTrue(all(150 <= t.service <= 250 for t in w.tasks))
        self.assertEqual(len({(t.x, t.y) for t in w.tasks}), 30)
        self.assertEqual(len(w.drones), 10)


class Comms(unittest.TestCase):
    def test_full_connectivity_single_component(self):
        w = World(SimConfig(seed=1))
        c = FullConnectivity(w.cfg)
        self.assertEqual(c.components(w), [set(range(10))])
        self.assertTrue(c.send(w, 0, 9, nbytes=10))
        self.assertEqual((c.sent, c.delivered, c.bytes_sent), (1, 1, 10))


if __name__ == "__main__":
    unittest.main()
