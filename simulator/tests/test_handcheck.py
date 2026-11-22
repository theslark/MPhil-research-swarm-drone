"""P1 exit criterion (b): metrics verified by hand on a 3-drone, 5-task case.

Scenario: scenarios/p1_handcheck.toml. Base (0,0), speed 10 m/s, all drones start idle at t=0.
Greedy rule: an idle drone takes the nearest open, unclaimed task; simultaneous decisions are
taken in drone-id order; when nothing is left it flies home.

Hand derivation (distances in m, times in s):
  t=0   d0 -> k0 (100,0)    dist 100           arrive 10   done 10+50 = 60
        d1 -> k1 (0,150)    dist 150           arrive 15   done 15+30 = 45
        d2 -> k2 (0,-250)   dist 250           arrive 25   done 25+21 = 46
  t=45  d1 at (0,150): open & unclaimed = {k3, k4}
          |k4| = hypot(100,150) = 180.2776 < |k3| = hypot(300,150) = 335.41  -> k4
          arrive 45 + 18.02776 = 63.02776, done 73.02776
  t=46  d2 at (0,-250): only k3 left, dist hypot(300,250) = 390.5125
          arrive 46 + 39.05125 = 85.05125, done 125.05125
  t=60  d0 at (100,0): nothing left -> home, 100 m -> lands at 70
  t=73.03 d1 at (100,300): home, hypot(100,300) = 316.2278 -> lands at 104.6505
  t=125.05 d2 at (300,0): home, 300 m -> lands at 155.05125
Metrics (T_max = 200, all weights 1):
  MCR = 1, T_mc = 125.05125
  AUC = sum(200 - t_k) / (5*200) = (140 + 155 + 154 + 74.94875 + 126.97224) / 1000
  DWR = 0 (each task serviced once, exactly s_k), WDR = 0 (no abandoned legs)
  distance = (100+100) + (150+180.2776+316.2278) + (250+390.5125+300)
  energy   = airborne time = 70 + 104.6505 + 155.05125
"""
import math
import os
import unittest

from uavsim.config import load_config
from uavsim.sim import run

HERE = os.path.dirname(os.path.abspath(__file__))
SCEN = os.path.join(HERE, "..", "scenarios", "p1_handcheck.toml")

h = math.hypot
DONE = {
    0: (60.0, 0),
    1: (45.0, 1),
    2: (46.0, 2),
    4: (45 + h(100, 150) / 10 + 10, 1),
    3: (46 + h(300, 250) / 10 + 40, 2),
}
LAND = {0: 60 + 10.0, 1: DONE[4][0] + h(100, 300) / 10, 2: DONE[3][0] + 30.0}


class HandCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = run(load_config(SCEN), "greedy", keep_events=True)

    def test_completion_times_and_completers(self):
        self.assertEqual(sorted(self.m["completions"]), [0, 1, 2, 3, 4])
        for k, (t, i) in DONE.items():
            t_sim, i_sim = self.m["completions"][k]
            self.assertAlmostEqual(t_sim, t, places=6, msg=f"task {k}")
            self.assertEqual(i_sim, i, msg=f"completer of task {k}")

    def test_landing_times(self):
        lands = {i: t for (t, kind, i, k) in self.m["events"] if kind == "land"}
        for i, t in LAND.items():
            self.assertAlmostEqual(lands[i], t, places=6, msg=f"drone {i}")

    def test_mission_metrics(self):
        m = self.m
        self.assertEqual(m["mcr"], 1.0)
        self.assertAlmostEqual(m["t_mc"], DONE[3][0], places=6)
        auc = sum(200 - t for t, _ in DONE.values()) / (5 * 200)
        self.assertAlmostEqual(m["coverage_auc"], auc, places=9)
        self.assertAlmostEqual(m["dwr"], 0.0, places=12)
        self.assertAlmostEqual(m["wdr"], 0.0, places=12)

    def test_distance_and_energy(self):
        dist = (100 + 100) + (150 + h(100, 150) + h(100, 300)) + (250 + h(300, 250) + 300)
        self.assertAlmostEqual(self.m["distance_total_m"], dist, places=6)
        self.assertAlmostEqual(self.m["energy_total_s"], sum(LAND.values()), places=6)
        self.assertAlmostEqual(self.m["energy_per_task_s"], sum(LAND.values()) / 5, places=6)

    def test_score(self):
        score = sum(0.999 ** t for t, _ in DONE.values())
        self.assertAlmostEqual(self.m["score"], score, places=9)


class HandCheckDuplicateWork(unittest.TestCase):
    """DWR/WDR formulas on a constructed case: two drones sweep the same task in parallel."""

    def test_parallel_sweep_counts_duplicate(self):
        from uavsim.config import SimConfig, TaskSpec
        from uavsim.metrics import Recorder, compute
        from uavsim.world import World

        cfg = SimConfig(n_drones=2, base_x=0, base_y=0, t_max=100, dt=0.5,
                        tasks=[TaskSpec(100, 0, 30), TaskSpec(0, 100, 10)], energy=1000)
        rec = Recorder()
        w = World(cfg, recorder=rec)
        # both drones go to k0 (a "wrong takeover"); drone 1 also later flies 50 m toward k1 then aborts
        plan = {0: [0, None], 1: [0, None]}

        def decide(d, world, now):
            world.assign(d, plan[d.id].pop(0) if plan[d.id] else None)
        while not w.finished():
            w.step(decide)
        m = compute(w, rec)
        # k0 swept twice in full (30 s each): duplicate = 30 s of the 40 s total work
        self.assertAlmostEqual(m["dwr"], 30 / 40, places=9)
        self.assertEqual(m["n_done"], 1)
        self.assertAlmostEqual(m["mcr"], 0.5)


if __name__ == "__main__":
    unittest.main()
